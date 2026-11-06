"""Student checks must share process handling and refresh only their own data."""

from __future__ import annotations

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE, PROJECT, TEAM

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("student checks need a running server", allow_module_level=True)

JOB_KEY = "run_checks:team:" + TEAM


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def student_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 1000},
        is_mobile=mode != "desktop",
        has_touch=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        ctx.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        writes = []

        def intercept(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.fulfill(status=204)

        ctx.route("**/*", intercept)
        if mode == "no-gsap":
            ctx.route(
                "**/gsap*.js*",
                lambda route: route.fulfill(body="", content_type="application/javascript"),
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/teams/" + TEAM)
        link = page.locator('a[href*="/dashboard/students/"]').first
        link.wait_for(state="attached")
        path = link.get_attribute("href")
        page.goto(live_server + path)
        page.locator("#runChecksGrid .rcm-cb").first.wait_for(state="attached")
        page.evaluate("""() => {
          window.__studentProbe = {history: [], polls: [], requests: []};
          const fetch = window.fetch;
          window.fetch = (url, opts) => {
            if (String(url).includes('/api/v1/compliance/')) {
              __studentProbe.history.push(String(url));
              return new Promise(() => {});
            }
            return fetch(url, opts);
          };
        }""")
        yield page
        assert not errors, errors
        assert not [url for url in writes if url.endswith("/run-checks")], writes


@pytest.mark.parametrize(
    "scenario",
    [
        "enqueue-failed",
        "enqueue-cancelled",
        "http-error",
        "stream-failed",
        "stream-cancelled",
        "stream-error",
        "no-stream",
        "completed",
        "immediate",
    ],
)
def test_student_checks_handle_terminal_responses_and_stream_failure(student_page, scenario):
    page = student_page
    page.evaluate("() => GP.openModal('runChecksModal')")
    page.wait_for_timeout(750)
    group_name = page.locator("#runChecksModal .rcm-scope-name").inner_text()
    assert page.locator("#runChecksModal .rcm-scope-kind").inner_text() == "Group"
    assert group_name == "tim-01-kniznica"
    page.evaluate(
        """scenario => {
      const fetch = window.fetch;
      window.fetch = (url, opts) => {
        if (opts?.method === 'POST' && String(url).endsWith('/run-checks')) {
          __studentProbe.requests.push({url: String(url), body: JSON.parse(opts.body)});
          if (scenario === 'http-error') return Promise.reject(new Error('Queue unavailable'));
          const result = scenario === 'immediate' ? {status: 'completed', message: 'Complete'}
            : {job_id: 'probe-job', status: scenario.startsWith('enqueue-')
              ? scenario.slice(8) : 'queued', message: 'Probe result'};
          return Promise.resolve(new Response(JSON.stringify(result), {
            status: 202, headers: {'Content-Type': 'application/json'},
          }));
        }
        return fetch(url, opts);
      };
      window.streamJobProgress = scenario === 'no-stream' ? undefined
        : (id, callbacks) => {window.__studentStream = callbacks; return {close() {}};};
      window.startGenericStatusPolling = (...args) => __studentProbe.polls.push(args.slice(0, 2));
    }""",
        scenario,
    )
    expected = page.locator("#runChecksGrid .rcm-cb:checked").evaluate_all(
        "boxes => boxes.map(box => box.value)"
    )
    page.locator("#btnRunChecks").click()
    page.wait_for_function("() => __studentProbe.requests.length === 1")
    if scenario.startswith("stream-") or scenario == "completed":
        page.wait_for_function("() => !!window.__studentStream")
        page.evaluate(
            """scenario => {
          if (scenario === 'stream-error') __studentStream.onError();
          else __studentStream.onComplete({
            status: scenario === 'completed' ? 'completed' : scenario.slice(7),
            error_message: 'Probe terminal error', result_summary: 'Probe completed',
          });
        }""",
            scenario,
        )
    if scenario in {"stream-error", "no-stream"}:
        page.wait_for_function("() => __studentProbe.polls.length > 0")
        assert page.evaluate("() => __studentProbe.polls[0]") == [JOB_KEY, "/api/v1/jobs/probe-job"]
        assert page.evaluate("key => _globalJobs[key].status", JOB_KEY) == "running"
        assert not page.evaluate("() => __studentProbe.history")
    else:
        success = scenario in {"completed", "immediate"}
        page.wait_for_function(
            "({key, status}) => _globalJobs[key]?.status === status",
            arg={"key": JOB_KEY, "status": "done" if success else "error"},
        )
        page.wait_for_function("""() => {
          const btn = document.getElementById('btnRunChecks');
          return !btn.classList.contains('loading') && !btn._loadingArmed;
        }""")
        assert len(page.evaluate("() => __studentProbe.history")) == (1 if success else 0)
    probe = page.evaluate("() => __studentProbe")
    assert probe["requests"] == [
        {"url": f"/api/v1/teams/{TEAM}/run-checks", "body": {"check_codes": expected}}
    ]
    assert page.evaluate("key => _globalJobs[key].meta.localIndicatorSelector", JOB_KEY) is None
    assert group_name in page.evaluate(
        "key => _globalJobs[key].message", JOB_KEY
    ) or scenario not in {"stream-error", "no-stream"}
    assert not page.locator("#gpConfirmDialog.active").count()
    page.wait_for_function("() => !document.querySelector('#runChecksModal.active')")


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("unrelated", 0),
        ("other-team", 0),
        ("other-course", 0),
        ("failed", 0),
        ("team", 1),
        ("course", 1),
        ("key-only", 1),
        ("stored-meta", 1),
        ("burst", 1),
        ("disposed", 0),
        ("hidden", 1),
    ],
)
def test_student_refresh_matches_scope_and_coalesces_completions(student_page, kind, expected):
    page = student_page
    page.evaluate(
        """({kind, team, course}) => {
      const detail = {jobType: 'run_checks:team:' + team, status: 'done',
        meta: {teamId: team, courseId: course}};
      if (kind === 'unrelated') Object.assign(detail, {jobType: 'enrichment', meta: {}});
      if (kind === 'other-team') detail.meta.teamId = 'another-team';
      if (kind === 'other-course') {
        detail.jobType = 'run_checks:course:another-course';
        detail.meta = {courseId: 'another-course'};
      }
      if (kind === 'failed') detail.status = 'error';
      if (kind === 'course') {
        detail.jobType = 'run_checks:course:' + course; detail.meta = {courseId: course};
      }
      if (kind === 'key-only') delete detail.meta;
      if (kind === 'stored-meta') {
        detail.jobType = 'sync:project:probe-project';
        _globalJobs[detail.jobType] = {status: 'done', meta: detail.meta};
        delete detail.meta;
      }
      if (kind === 'disposed') GP.studentDetailCleanup();
      if (kind === 'hidden') Object.defineProperty(document, 'visibilityState', {
        configurable: true, value: 'hidden',
      });
      const send = () => window.dispatchEvent(new CustomEvent('gp:job-complete', {detail}));
      send();
      if (kind === 'burst') {send(); send();}
    }""",
        {"kind": kind, "team": TEAM, "course": COURSE},
    )
    if kind == "hidden":
        assert not page.evaluate("() => __studentProbe.history")
        page.evaluate("""() => {
          Object.defineProperty(document, 'visibilityState', {
            configurable: true, value: 'visible',
          });
          document.dispatchEvent(new Event('visibilitychange'));
        }""")
    page.wait_for_timeout(200)
    assert len(page.evaluate("() => __studentProbe.history")) == expected


def test_project_picker_reports_the_group_actually_recomputed(student_page, live_server: str):
    page = student_page
    page.goto(live_server + "/dashboard/projects/" + PROJECT)
    page.evaluate("() => GP.openModal('runChecksModal')")
    page.wait_for_timeout(750)
    assert page.locator("#runChecksModal .rcm-scope-kind").inner_text() == "Group"
    assert page.locator("#runChecksModal .rcm-scope-name").inner_text() == "tim-01-kniznica"

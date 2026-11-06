"""Group analysis uses the shipped global job component; only transport is controlled."""

from __future__ import annotations

import json
import os
import re

import pytest

pytestmark = pytest.mark.e2e
TEAM = os.getenv("GITPULSE_E2E_LLM_TEAM_ID")
if not os.getenv("GITPULSE_E2E_BASE_URL") or not TEAM:
    pytest.skip("needs a local LLM-enabled group fixture", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def team_page(browser, context_for, live_server: str, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        is_mobile=width == 390,
        has_touch=width == 390,
    ) as ctx:
        hold_discovery = request.node.callspec.params.get("hold_discovery", False)
        ctx.add_init_script("window.__holdJobDiscovery = " + json.dumps(hold_discovery))
        ctx.add_init_script("""
          localStorage.setItem('gp_tour_v2:team_detail_teacher@admin:completed', '1');
          window.__analysisSources = [];
          const NativeSource = EventSource;
          window.EventSource = class extends EventTarget {
            constructor(url, options) {
              super();
              if (!String(url).endsWith('/llm-analysis-stream')) {
                return new NativeSource(url, options);
              }
              this.url = String(url);
              __analysisSources.push(this);
            }
            close() { this.closed = true; }
            emit(data, type = 'message') {
              this.dispatchEvent(new MessageEvent(type, {
                data: typeof data === 'string' ? data : JSON.stringify(data)}));
            }
          };
          const fetch = window.fetch;
          window.__status = {status: 'none'};
          window.__statusMode = 'ready';
          window.__statusReads = 0;
          window.__statusPending = [];
          window.__completed = [];
          window.__liveReads = 0;
          window.__discoveryPending = [];
          addEventListener('gp:job-complete', event => __completed.push(event.detail));
          window.fetch = (url, options) => {
            const path = new URL(url, location.href).pathname;
            if (path === '/api/v1/sync/active' && __holdJobDiscovery) {
              return new Promise(resolve => __discoveryPending.push(() => resolve(
                new Response('{"courses":[]}', {headers:{'Content-Type':'application/json'}})
              )));
            }
            if (path.endsWith('/llm-analysis-status')) {
              __statusReads++;
              const respond = data => new Response(JSON.stringify(data), {
                headers: {'Content-Type': 'application/json'}});
              if (__statusMode === 'fail') return Promise.reject(new Error('Status unavailable'));
              if (__statusMode === 'hold') return new Promise(resolve => {
                __statusPending.push(data => resolve(respond(data)));
              });
              return Promise.resolve(respond(__status));
            }
            if (path.endsWith('/live-data')) __liveReads++;
            return fetch(url, options);
          };
        """)
        page = ctx.new_page()
        page.bring_to_front()
        errors = []
        writes = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text) if message.type == "error" else None,
        )

        def readonly(route):
            if route.request.method in {"GET", "HEAD", "OPTIONS"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.fulfill(status=204)

        ctx.route("**/*", readonly)
        page.goto(
            f"{live_server}/dashboard/teams/{TEAM}?lang=en&probe=keep&analysis_started=1#members",
            wait_until="load",
        )
        page.wait_for_function(
            "() => !!GP.teamDetailCleanup && document.documentElement.hasAttribute('data-gp-ready')"
        )
        assert page.locator("#gp-team-detail-config").evaluate(
            "el => JSON.parse(el.textContent).llmEnabled"
        ), "local LLM feature must be enabled"
        page.wait_for_function("() => __statusReads === 1")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page
        assert not errors, errors
        assert not writes, writes


def _start(page):
    page.evaluate("""() => {
      __statusMode = 'ready';
      __status = {status: 'running', progress: 0};
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __analysisSources.length === 1 && !!_globalJobs.analysis")


def _emit(page, data, event="message"):
    page.evaluate(
        "({data, event}) => __analysisSources.at(-1).emit(data, event)",
        {"data": data, "event": event},
    )


def test_one_shared_tracker_preserves_navigation_context(team_page):
    page = team_page
    assert "analysis_started" not in page.url
    assert "lang=en" in page.url
    assert "probe=keep" in page.url
    assert page.url.endswith("#members")
    assert not page.evaluate("() => !!_globalJobs.analysis"), "query marker is not proof of a job"
    _start(page)
    page.locator('[data-job-id="analysis"]').wait_for(state="visible")
    page.evaluate("""() => {
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    assert page.evaluate("() => __analysisSources.length") == 1
    assert page.evaluate("() => __statusReads") == 2
    assert page.locator("#analysisProgress").count() == 0


def test_only_aggregate_progress_and_completion_count(team_page):
    page = team_page
    _start(page)
    for raw, expected in [(0, 0), (25, 25), (300, 100), (-2, 0), (None, None)]:
        _emit(page, {"status": "running", "progress": raw})
        assert page.evaluate("() => _globalJobs.analysis.progress") == expected
    _emit(page, {"status": "running", "progress": 25})
    for status in ["running", "completed", "failed", "cancelled"]:
        _emit(page, {"status": status, "job_id": "child-project", "progress": 100})
        assert page.evaluate("() => _globalJobs.analysis.status") == "running"
        assert page.evaluate("() => _globalJobs.analysis.progress") == 25
    assert page.evaluate("() => __completed.length") == 0


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_terminal_status_refreshes_once_and_closes_shared_stream(team_page, status):
    page = team_page
    _start(page)
    _emit(page, {"status": "running", "progress": 25})
    _emit(page, {"status": status, "message": "Confirmed outcome"})
    _emit(page, {"status": status}, "complete")
    assert page.evaluate("() => _globalJobs.analysis.status") == (
        "done" if status == "completed" else "error"
    )
    assert page.evaluate("() => _globalJobs.analysis.progress") == (
        100 if status == "completed" else 25
    )
    assert page.evaluate("() => __analysisSources[0].closed")
    assert page.evaluate("() => __completed.length") == 1
    page.wait_for_function("() => __liveReads > 0")


def test_unknown_completion_reconciles_without_overlapping_reads(team_page):
    page = team_page
    _start(page)
    page.clock.install()
    page.evaluate("() => __statusMode = 'hold'")
    _emit(page, "bad-json", "complete")
    page.clock.fast_forward(3100)
    page.wait_for_function("() => __statusPending.length === 1")
    page.clock.fast_forward(15000)
    assert page.evaluate("() => __statusPending.length") == 1
    assert page.evaluate("() => isGlobalJobRunning('analysis')")
    page.evaluate("() => __statusPending.shift()({status: 'completed'})")
    page.wait_for_function("() => _globalJobs.analysis.status === 'done'")
    assert page.evaluate("() => __completed.length") == 1


def test_transport_failure_does_not_discard_work(team_page):
    page = team_page
    _start(page)
    page.clock.install()
    page.evaluate("() => __statusMode = 'fail'")
    _emit(page, {}, "complete")
    page.clock.fast_forward(3100)
    page.wait_for_function("() => __statusReads > 2")
    assert page.evaluate("() => isGlobalJobRunning('analysis')")
    assert page.evaluate("() => __completed.length") == 0
    page.evaluate("() => { __statusMode = 'ready'; __status = {status: 'failed'}; }")
    page.clock.fast_forward(3100)
    page.wait_for_function("() => _globalJobs.analysis.status === 'error'")


def test_disposed_page_cannot_register_a_delayed_probe(team_page):
    page = team_page
    page.evaluate("""() => {
      __statusMode = 'hold';
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __statusPending.length === 1")
    page.evaluate("""() => {
      GP.teamDetailCleanup();
      __statusPending.shift()({status: 'running'});
    }""")
    page.evaluate("async () => { await new Promise(requestAnimationFrame); }")
    assert page.evaluate("() => __analysisSources.length") == 0
    assert not page.evaluate("() => !!_globalJobs.analysis")


def test_probe_failure_can_retry_without_claiming_a_job(team_page):
    page = team_page
    page.evaluate("""() => {
      __statusMode = 'fail';
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __statusReads === 2")
    page.evaluate("async () => { await new Promise(requestAnimationFrame); }")
    assert not page.evaluate("() => !!_globalJobs.analysis")
    _start(page)


@pytest.mark.parametrize("hold_discovery", [False, True])
def test_probe_cannot_replace_another_confirmed_run(team_page, hold_discovery):
    page = team_page
    page.evaluate("""() => {
      __statusMode = 'hold';
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __statusPending.length === 1")
    if hold_discovery:
        page.wait_for_function("() => __discoveryPending.length === 1")
    page.evaluate("""() => {
      showGlobalJob('Other confirmed analysis', 'analysis', {
        projectId: 'other', pollUrl: '/dashboard/projects/other/llm-analysis-status'});
      __statusPending.shift()({status: 'running'});
      if (__holdJobDiscovery) __discoveryPending.shift()();
    }""")
    page.evaluate("async () => { await new Promise(requestAnimationFrame); }")
    assert page.evaluate("() => _globalJobs.analysis.meta.projectId") == "other"
    sources = page.evaluate(
        "() => __analysisSources.map(source => ({url:source.url,closed:!!source.closed}))"
    )
    assert sum(not source["closed"] for source in sources) == 1, sources
    assert all(
        source["url"].endswith("/dashboard/projects/other/llm-analysis-stream")
        for source in sources
    )


def test_shared_tracking_survives_full_navigation(team_page, live_server):
    page = team_page
    _start(page)
    page.goto(live_server + "/dashboard/preferences?lang=en", wait_until="load")
    page.wait_for_function("() => __analysisSources.length === 1 && !!_globalJobs.analysis")
    assert page.evaluate("() => isGlobalJobRunning('analysis')")
    _emit(page, {"status": "completed"}, "complete")
    assert page.evaluate("() => _globalJobs.analysis.status") == "done"


@pytest.mark.parametrize("gate", ["feature-disabled", "student", "archived-teacher"])
def test_discovery_obeys_rendered_feature_and_role_configuration(team_page, gate):
    page = team_page

    def configuration(route):
        response = route.fetch()
        html = response.text()
        pattern = r'(<script[^>]+id="gp-team-detail-config"[^>]*>)(.*?)(</script>)'
        match = re.search(pattern, html, re.DOTALL)
        assert match
        config = json.loads(match[2])
        config.update(isAdmin=False, isTeacher=gate == "archived-teacher", canEdit=False)
        config["llmEnabled"] = gate != "feature-disabled"
        if gate == "feature-disabled":
            config["isAdmin"] = True
        html = html[: match.start(2)] + json.dumps(config) + html[match.end(2) :]
        route.fulfill(response=response, body=html)

    # This checks the client's rendered configuration contract; endpoint
    # authorization remains real and is covered by the authenticated route tests.
    page.route("**/dashboard/teams/" + TEAM + "?*", configuration)
    page.reload(wait_until="load")
    page.wait_for_function("() => !!GP.teamDetailCleanup")
    assert page.evaluate("() => __statusReads") == (1 if gate == "archived-teacher" else 0)
    assert page.evaluate("() => __analysisSources.length") == 0

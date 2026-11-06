"""Course check indicators follow accepted work, including failed/declined launches."""

from __future__ import annotations

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("course checks need a running server", allow_module_level=True)

JOB_KEY = "run_checks:course:" + COURSE


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def course_page(browser, context_for, live_server: str, request):
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
        page.goto(live_server + "/dashboard/courses/" + COURSE)
        page.locator("#runChecksGrid .rcm-cb").first.wait_for(state="attached")
        page.evaluate("() => GP.openModal('runChecksModal')")
        page.wait_for_timeout(750)
        yield page
        assert not errors, errors
        assert not [url for url in writes if url.endswith("/run-checks")], writes


@pytest.mark.parametrize(
    "outcome", ["http-error", "all-failed", "competing-run", "accepted", "partial", "empty"]
)
def test_course_indicators_follow_the_launch_outcome(course_page, outcome):
    page = course_page
    page.evaluate(
        """outcome => {
      const fetch = window.fetch;
      window.__courseLaunch = {posts: [], polls: []};
      // Keep live data pending: indicator cleanup must not depend on a later read.
      window.fetch = (url, opts) => {
        if (String(url).includes('/live-data')) return new Promise(() => {});
        if (opts?.method === 'POST' && String(url).endsWith('/run-checks')) {
          __courseLaunch.posts.push(JSON.parse(opts.body));
          if (outcome === 'http-error') return Promise.reject(new Error('Queue unavailable'));
          const enqueued = ['accepted', 'partial'].includes(outcome) ? 1 : 0;
          const failed = ['all-failed', 'partial'].includes(outcome) ? 1 : 0;
          return Promise.resolve(new Response(JSON.stringify({enqueued, failed, skipped: 0,
            message: failed ? 'Queue unavailable' : 'Checks queued'}), {
            status: 202, headers: {'Content-Type': 'application/json'},
          }));
        }
        return fetch(url, opts);
      };
      window.startGenericStatusPolling = (...args) => __courseLaunch.polls.push(args.slice(0, 2));
    }""",
        outcome,
    )
    selected = page.locator("#runChecksGrid .rcm-cb:checked").evaluate_all(
        "boxes => boxes.map(box => box.value)"
    )
    page.locator("#btnRunChecks").click()
    page.locator("#gpConfirmDialog.active").wait_for()
    page.wait_for_timeout(500)
    if outcome == "competing-run":
        page.evaluate(
            """({key, course}) => showGlobalJob('Other checks', key, {
          courseId: course, jobKind: 'run_checks',
        })""",
            {"key": JOB_KEY, "course": COURSE},
        )
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")
    if outcome == "competing-run":
        page.wait_for_timeout(200)
        assert page.evaluate("() => __courseLaunch.posts") == []
        assert not page.locator(".group-recompute-badge").count()
        assert page.locator("#runChecksModal.active").count() == 1
        assert page.evaluate("key => _globalJobs[key].status", JOB_KEY) == "running"
        return
    page.wait_for_function("() => __courseLaunch.posts.length === 1")
    assert page.evaluate("() => __courseLaunch.posts[0].check_codes") == selected
    if outcome in {"accepted", "partial"}:
        page.wait_for_function("() => __courseLaunch.polls.length > 0")
        assert page.locator(".group-recompute-badge").count() > 0
        assert page.evaluate("() => __courseLaunch.polls[0]") == [
            JOB_KEY,
            f"/api/v1/courses/{COURSE}/run-checks-status",
        ]
        # A later failed/completed run must also clear its per-group indicators.
        page.evaluate(
            """({key, outcome}) => completeGlobalJob(key, 'Finished',
          outcome === 'partial' ? 'error' : 'done')
        """,
            {"key": JOB_KEY, "outcome": outcome},
        )
    else:
        page.wait_for_function(
            "({key, status}) => _globalJobs[key]?.status === status",
            arg={"key": JOB_KEY, "status": "done" if outcome == "empty" else "error"},
        )
    page.wait_for_function("() => !document.querySelector('.group-recompute-badge')")
    page.wait_for_function("() => !document.querySelector('#runChecksModal.active')")
    assert not page.locator("#gpConfirmDialog.active").count()
    page.wait_for_function("""() => {
      const btn = document.getElementById('btnRunChecks');
      return !btn.classList.contains('loading') && !btn._loadingArmed;
    }""")

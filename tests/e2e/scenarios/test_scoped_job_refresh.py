"""Job completions refresh their own views and preserve unrelated pages."""

from __future__ import annotations

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE, PROJECT, TEAM

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("job refresh needs a running server", allow_module_level=True)


@pytest.fixture(params=["course", "team", "project"])
def scope_name(request):
    return request.param


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def scoped_page(browser, context_for, live_server: str, request, scope_name):
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
        path = {
            "course": "courses/" + COURSE,
            "team": "teams/" + TEAM,
            "project": "projects/" + PROJECT,
        }[scope_name]
        page.goto(live_server + "/dashboard/" + path)
        page.wait_for_timeout(1000)
        page.evaluate("""() => {
          const fetch = window.fetch;
          window.__scopeReads = [];
          window.fetch = (url, opts) => {
            const path = String(url);
            if ((!opts?.method || opts.method === 'GET') && (
              path.includes('/live-data') || path === location.pathname
            )) {
              __scopeReads.push(path);
              return new Promise(() => {});
            }
            return fetch(url, opts);
          };
        }""")
        yield page
        assert not errors, errors
        assert all("/tour/seen" in url for url in writes), writes


@pytest.mark.parametrize(
    "scenario", ["unrelated", "sibling", "own", "legacy-analysis", "hidden", "disposed"]
)
def test_only_relevant_jobs_refresh_the_current_view(scoped_page, scope_name, scenario):
    page = scoped_page
    page.evaluate(
        """({scenario, scope, course, team, project}) => {
      const detail = {jobType: 'sync:project:' + project, status: 'done',
        meta: {courseId: course, teamId: team, projectId: project}};
      if (scenario === 'unrelated') Object.assign(detail, {jobType: 'enrichment', meta: {}});
      if (scenario === 'sibling') {
        const kind = scope === 'course' ? 'course' : scope === 'team' ? 'team' : 'project';
        detail.jobType = 'sync:' + kind + ':other';
        detail.meta[kind + 'Id'] = 'other';
      }
      // A group-wide check can originate on a different project page.
      if (scenario === 'own' && scope === 'project') {
        detail.jobType = 'run_checks:team:' + team;
        detail.meta.projectId = 'another-project';
      }
      if (scenario === 'legacy-analysis') {
        detail.jobType = 'analysis';
        detail.meta = {courseId: course, teamId: team,
          pollUrl: '/dashboard/projects/' + project + '/llm-analysis-status'};
      }
      if (scenario === 'hidden') Object.defineProperty(document, 'visibilityState', {
        configurable: true, value: 'hidden',
      });
      if (scenario === 'disposed') GP.activePageCleanup();
      window.dispatchEvent(new CustomEvent('gp:job-complete', {detail}));
    }""",
        {
            "scenario": scenario,
            "scope": scope_name,
            "course": COURSE,
            "team": TEAM,
            "project": PROJECT,
        },
    )
    if scenario in {"unrelated", "sibling", "hidden", "disposed"}:
        page.wait_for_timeout(250)
        assert page.evaluate("() => __scopeReads") == []
    if scenario == "hidden":
        page.evaluate("""() => {
          Object.defineProperty(document, 'visibilityState', {
            configurable: true, value: 'visible',
          });
          document.dispatchEvent(new Event('visibilitychange'));
        }""")
    if scenario in {"own", "legacy-analysis", "hidden"}:
        page.wait_for_function("() => __scopeReads.some(url => url.endsWith('/live-data'))")
        if scope_name == "project":
            # One server projection refreshes intelligence and optional AI cards.
            page.wait_for_function("() => __scopeReads.includes(location.pathname)")

"""Background reads obey the current page, feature flags and shared button locks."""

from __future__ import annotations

import json
import os
import re

import pytest

pytestmark = pytest.mark.e2e
PROJECT = os.getenv("GITPULSE_E2E_LLM_PROJECT_ID")
if not os.getenv("GITPULSE_E2E_BASE_URL") or not PROJECT:
    pytest.skip("needs a local project fixture", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def project_page(browser, context_for, live_server, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 950},
    ) as context:
        context.add_init_script("""(() => {
          const fetch = window.fetch;
          window.__liveReads = 0;
          window.__statusReads = 0;
          window.__livePayload = {students: [], bottlenecks: []};
          window.__holdLive = false;
          window.__livePending = [];
          window.fetch = (url, options) => {
            const path = new URL(url, location.href).pathname;
            const json = value => new Response(JSON.stringify(value), {
              headers: {'Content-Type': 'application/json'}});
            if (path.endsWith('/live-data')) {
              __liveReads++;
              // Complete even after abort to exercise an already queued response.
              if (__holdLive) return new Promise(resolve => {
                __livePending.push(data => resolve(json(data)));
              });
              return Promise.resolve(json(__livePayload));
            }
            if (path.endsWith('/llm-analysis-status')) {
              __statusReads++;
              return Promise.resolve(json({status: 'none'}));
            }
            return fetch(url, options);
          };
        })();""")
        page = context.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text) if message.type == "error" else None,
        )
        page.goto(f"{live_server}/dashboard/projects/{PROJECT}?lang=en")
        page.wait_for_function(
            "() => GP.projectDetailCleanup"
            " && document.documentElement.hasAttribute('data-gp-ready')"
        )
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page
        assert not errors, errors


@pytest.mark.parametrize("locked", [False, True])
@pytest.mark.parametrize("empty", [False, True])
def test_live_data_cannot_override_a_shared_button_lock(project_page, locked, empty):
    page = project_page
    button = page.locator("#btnOpenRunChecks")
    assert button.count() == 1
    page.evaluate(
        """({locked, empty}) => {
          GP.setButtonLoading(document.getElementById('btnOpenRunChecks'), locked);
          __livePayload.repo_empty = empty;
          document.dispatchEvent(new CustomEvent('gp-tab-visible'));
        }""",
        {"locked": locked, "empty": empty},
    )
    page.wait_for_function("() => __liveReads === 1")
    page.wait_for_timeout(100)
    assert button.is_disabled() is locked


def test_a_retired_project_cannot_paint_or_schedule_a_trailing_read(project_page):
    page = project_page
    page.evaluate("""() => {
      const stale = document.getElementById('issuesToAddressContainer').cloneNode(true);
      stale.setAttribute('data-scored-count', '999');
      stale.appendChild(document.createTextNode('STALE RESPONSE'));
      window.__staleIssues = stale.outerHTML;
      __holdLive = true;
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
      document.dispatchEvent(new CustomEvent('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __livePending.length === 1")
    page.evaluate(
        "project => GP.navigateTo('/dashboard/projects/' + project + '?lang=en&view=next')", PROJECT
    )
    page.wait_for_function(
        "() => location.search.includes('view=next')"
        " && !document.querySelector('#main-content.is-arriving')"
    )
    before = page.locator("#issuesToAddressContainer").inner_text()
    page.evaluate("""() => __livePending.pop()({
      students: [], bottlenecks: [], issues_html: __staleIssues})""")
    page.wait_for_timeout(150)
    assert page.locator("#issuesToAddressContainer").inner_text() == before
    assert page.evaluate("() => __liveReads") == 1


@pytest.mark.parametrize("enabled", [False, True])
def test_analysis_discovery_respects_the_feature_and_staff_flags(project_page, enabled):
    page = project_page
    html = page.request.get(page.url).text()

    def change_config(match):
        config = json.loads(match[2])
        config.update(
            llmEnabled=enabled, analysisStarted=True, isAdmin=not enabled, isTeacher=False
        )
        return match[1] + json.dumps(config) + match[3]

    html, count = re.subn(
        r'(<script[^>]+id="gp-project-detail-config"[^>]*>)(.*?)(</script>)',
        change_config,
        html,
        flags=re.DOTALL,
    )
    assert count == 1
    page.route(page.url, lambda route: route.fulfill(body=html, content_type="text/html"))
    page.reload()
    page.wait_for_function(
        "() => GP.projectDetailCleanup && document.documentElement.hasAttribute('data-gp-ready')"
    )
    page.evaluate("""() => {
      document.dispatchEvent(new Event('visibilitychange'));
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    page.wait_for_timeout(200)
    assert page.evaluate("() => __statusReads") == 0

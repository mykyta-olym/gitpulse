"""Analysis reflects confirmed work and reuses the server's component projection."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e
PROJECT = os.getenv("GITPULSE_E2E_LLM_PROJECT_ID")
if not os.getenv("GITPULSE_E2E_BASE_URL") or not PROJECT:
    pytest.skip("needs a local LLM-enabled project fixture", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def analysis_page(browser, context_for, live_server: str, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        is_mobile=width == 390,
        has_touch=width == 390,
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text) if message.type == "error" else None,
        )
        page.add_init_script("""
          localStorage.setItem('gp_tour_v2:project_detail_teacher@admin:completed', '1');
          const NativeSource = EventSource;
          window.__analysisSources = [];
          window.EventSource = class extends EventTarget {
            constructor(url, options) {
              super();
              if (!String(url).endsWith('/llm-analysis-stream')) {
                return new NativeSource(url, options);
              }
              __analysisSources.push(this);
            }
            close() { this.closed = true; }
            emit(data, type = 'message') {
              const text = typeof data === 'string' ? data : JSON.stringify(data);
              this.dispatchEvent(new MessageEvent(type, {data: text}));
            }
          };
        """)
        page.goto(f"{live_server}/dashboard/projects/{PROJECT}?lang=en", wait_until="load")
        page.wait_for_function(
            """() => !!window.refreshProjectAnalysis
              && document.documentElement.hasAttribute('data-gp-ready')"""
        )
        assert page.locator("#analysisProgress").count() == 1, "local LLM feature must be enabled"
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        html = page.request.get(f"{live_server}/dashboard/projects/{PROJECT}?lang=en").text()
        page.evaluate(
            """({project, html}) => {
              const original = window.fetch;
              window.__analysisReads = [];
              window.__analysisCards = [];
              window.__analysisStarts = 0;
              window.__analysisStatus = {
                status: 'running', message: 'Working', total: 4, progress: 25};
              window.__holdAnalysisStatus = false;
              window.__analysisHtml = html;
              window.__analysisCardMode = 'hold';
              window.fetch = (url, opts = {}) => {
                const path = new URL(url, location.href).pathname;
                const json = value => new Response(JSON.stringify(value), {
                  headers: {'Content-Type': 'application/json'}});
                if (path.endsWith('/llm-analyze')) {
                  __analysisStarts++;
                  return Promise.resolve(json({status: 'started'}));
                }
                if (path.endsWith('/llm-analysis-status')) {
                  if (!__holdAnalysisStatus) return Promise.resolve(json(__analysisStatus));
                  return new Promise(resolve => __analysisReads.push(data => resolve(json(data))));
                }
                if (path === '/dashboard/projects/' + project) {
                  const respond = () => new Response(__analysisHtml, {
                    headers: {'Content-Type': 'text/html'}});
                  if (__analysisCardMode === 'fail') {
                    return Promise.reject(new Error('Result read failed'));
                  }
                  if (__analysisCardMode === 'ready') return Promise.resolve(respond());
                  return new Promise(resolve => __analysisCards.push(() => resolve(respond())));
                }
                return original(url, opts);
              };
            }""",
            {"project": PROJECT, "html": html},
        )
        yield page
        assert not errors, errors


def _start(page) -> None:
    count = page.evaluate("() => __analysisSources.length")
    page.locator("#runAnalysisBtn").click()
    page.wait_for_function("n => __analysisSources.length > n", arg=count)
    page.wait_for_function(
        "() => document.querySelector('#analysisStatusText').textContent === 'Working'"
    )


def _emit(page, data) -> None:
    page.evaluate("data => __analysisSources.at(-1).emit(data)", data)


def test_unknown_and_zero_progress_do_not_claim_completion(analysis_page) -> None:
    page = analysis_page
    _start(page)
    _emit(page, {"status": "running", "total": 4, "progress": 0})
    assert page.locator("#analysisProgressBar").get_attribute("aria-valuenow") == "0"
    assert "is-indeterminate" not in page.locator(
        "#analysisProgressBar .progress-bar"
    ).get_attribute("class")
    _emit(page, {"status": "running", "total": 4, "progress": 140})
    assert page.locator("#analysisProgressBar").get_attribute("aria-valuenow") == "100"
    _emit(page, {"status": "running", "total": 4, "progress": -20})
    assert page.locator("#analysisProgressBar").get_attribute("aria-valuenow") == "0"
    _emit(page, {"status": "running", "total": 4, "progress": None})
    assert page.locator("#analysisProgressBar").get_attribute("aria-valuenow") is None
    _emit(page, {"status": "unexpected"})
    assert page.locator("#analysisProgress").is_visible()
    assert page.locator("#runAnalysisBtn").is_disabled()
    _emit(page, {"status": "running", "total": 4, "progress": 140})
    # An invalid stream packet switches to the real REST fallback.
    page.wait_for_function(
        """() => document.querySelector('#analysisProgressBar')
          .getAttribute('aria-valuenow') === '25'"""
    )


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_terminal_result_waits_for_the_projection_and_never_for_a_timer(
    analysis_page, status: str
) -> None:
    page = analysis_page
    _start(page)
    text_x = page.locator("#analysisStatusText").bounding_box()["x"]
    _emit(page, {"status": status, "message": "Confirmed result"})
    page.wait_for_function("() => __analysisCards.length === 1")
    assert page.locator("#analysisProgress").is_visible()
    assert page.locator("#analysisProgress").get_attribute("aria-busy") == "true"
    assert page.locator("#analysisProgressBar").is_visible() == (status == "completed")
    assert page.locator("#analysisStatusText").bounding_box()["x"] == text_x
    assert page.evaluate("() => __analysisSources.at(-1).closed")
    # A queued duplicate terminal event cannot invalidate the pending projection.
    _emit(page, {"status": status, "message": "Duplicate result"})
    page.evaluate("() => __analysisCards[0]()")
    page.wait_for_function("() => document.querySelector('.llm-error-card') !== null")
    assert "gitlab-alert" in page.locator(".llm-error-card").get_attribute("class")
    assert not page.locator("#analysisProgress").is_visible()
    assert page.locator("#runAnalysisBtn").is_enabled()


def test_failed_projection_has_a_shared_retry_that_does_not_restart_analysis(analysis_page) -> None:
    page = analysis_page
    _start(page)
    page.evaluate("() => { __analysisCardMode = 'fail'; }")
    _emit(page, {"status": "completed"})
    page.wait_for_selector("#refreshAnalysisBtn", state="visible")
    assert page.locator("#analysisSubtitle").inner_text() == "Failed to refresh project data"
    assert page.locator("#analysisSubtitle").evaluate(
        "el => getComputedStyle(el).color === getComputedStyle(el.parentElement).color"
    )
    page.evaluate("() => { __analysisCardMode = 'hold'; }")
    page.locator("#refreshAnalysisBtn").click()
    page.wait_for_function("() => __analysisCards.length === 1")
    assert page.locator("#refreshAnalysisBtn").get_attribute("aria-busy") == "true"
    page.evaluate("() => __analysisCards[0]()")
    page.wait_for_selector("#analysisProgress", state="hidden")
    assert page.evaluate("() => __analysisStarts") == 1


def test_old_result_cannot_replace_a_new_run(analysis_page) -> None:
    page = analysis_page
    _start(page)
    _emit(page, {"status": "failed"})
    page.wait_for_function("() => __analysisCards.length === 1")
    _start(page)
    page.evaluate("() => { __analysisCards[0](); __analysisSources[0].emit({status: 'failed'}); }")
    page.wait_for_timeout(200)
    assert page.locator("#analysisStatusText").inner_text() == "Working"
    assert page.locator(".llm-error-card").count() == 0
    assert page.locator("#analysisProgress").is_visible()
    assert page.locator("#runAnalysisBtn").is_disabled()


def test_late_rest_response_cannot_overwrite_sse(analysis_page) -> None:
    page = analysis_page
    page.evaluate("() => { __holdAnalysisStatus = true; }")
    page.locator("#runAnalysisBtn").click()
    page.wait_for_function("() => __analysisSources.length >= 1 && __analysisReads.length >= 1")
    _emit(page, {"status": "running", "message": "Newer update", "total": 4, "progress": 75})
    page.evaluate("() => __analysisReads.forEach(resolve => resolve({status: 'none'}))")
    page.wait_for_timeout(150)
    assert page.locator("#analysisStatusText").inner_text() == "Newer update"
    assert page.locator("#analysisProgressBar").get_attribute("aria-valuenow") == "75"
    assert page.locator("#analysisProgress").is_visible()


def test_cleanup_closes_the_analysis_stream(analysis_page) -> None:
    page = analysis_page
    _start(page)
    page.evaluate("() => GP.projectDetailCleanup()")
    assert page.evaluate("() => __analysisSources.at(-1).closed")
    _emit(page, {"status": "completed"})
    assert page.evaluate("() => __analysisCards.length") == 0
    assert page.locator("#analysisStatusText").inner_text() == "Working"


def test_success_with_no_results_restores_the_server_empty_state(analysis_page) -> None:
    page = analysis_page
    _start(page)
    page.evaluate("""() => {
      const doc = new DOMParser().parseFromString(__analysisHtml, 'text/html');
      const empty = doc.querySelector('#projectAnalysisResults .empty-state');
      doc.getElementById('projectAnalysisResults').replaceChildren(empty.cloneNode(true));
      __analysisHtml = doc.documentElement.outerHTML;
      __analysisCardMode = 'ready';
    }""")
    _emit(page, {"status": "completed"})
    page.wait_for_selector("#analysisProgress", state="hidden")
    assert page.locator("#projectAnalysisResults .empty-state").is_visible()
    assert page.locator("#projectAnalysisResults .llm-error-card").count() == 0


def test_a_login_response_cannot_be_mistaken_for_loaded_results(analysis_page) -> None:
    page = analysis_page
    _start(page)
    page.evaluate("""() => {
      __analysisHtml = '<html><body><form>Login</form></body></html>';
      __analysisCardMode = 'ready';
    }""")
    _emit(page, {"status": "completed"})
    page.wait_for_selector("#refreshAnalysisBtn", state="visible")
    assert page.locator("#analysisProgress").is_visible()
    assert page.locator("#analysisSubtitle").inner_text() == "Failed to refresh project data"

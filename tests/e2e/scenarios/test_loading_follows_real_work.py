"""Pending semantics, delayed spinners and results share the real core lifecycle."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("loading scenarios need a running server", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def system_page(browser, context_for, live_server, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        has_touch=width == 390,
        is_mobile=width == 390,
    ) as context:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/system")
        page.wait_for_function("() => !!GP.refreshRegion && !!GP.tableLoading")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page
        assert errors == []


def test_fast_data_never_waits_for_a_spinner(system_page):
    result = system_page.evaluate("""async () => {
      const region = document.querySelector('#systemHealth > .card-body');
      const button = document.getElementById('btnHealthCheck');
      let calls = 0;
      const start = performance.now();
      const pending = GP.refreshRegion({region, button, load: async () => { calls++; }});
      const during = {busy: region.getAttribute('aria-busy'), inert: region.inert,
        disabled: button.disabled, buttonBusy: button.getAttribute('aria-busy')};
      const duplicate = await GP.refreshRegion({region, button, load: async () => { calls++; }});
      const success = await pending;
      return {during, duplicate, success, calls, elapsed: performance.now() - start,
        busy: region.hasAttribute('aria-busy'), disabled: button.disabled,
        spinner: !!button.querySelector('.gp-spinner'),
        refreshing: region.classList.contains('is-refreshing')};
    }""")
    assert result["during"] == {
        "busy": "true",
        "inert": True,
        "disabled": True,
        "buttonBusy": "true",
    }
    assert result["success"]
    assert not result["duplicate"]
    assert result["calls"] == 1
    assert result["elapsed"] < 180
    assert not any(result[key] for key in ("busy", "disabled", "spinner", "refreshing"))


def test_health_refresh_preserves_content_and_reports_failure_then_retry(system_page):
    page = system_page
    page.evaluate("""() => {
      const fetch = window.fetch;
      window.__healthReads = [];
      window.__healthHtml = document.getElementById('systemHealthContent').outerHTML;
      window.fetch = (url, options) => String(url).includes('/admin/system/health')
        ? new Promise((resolve, reject) => __healthReads.push({url: String(url), reject,
          respond: () => resolve(new Response(__healthHtml, {
            headers: {'Content-Type': 'text/html', 'X-Health-Status': 'ok'}
          }))})) : fetch(url, options);
      const button = document.getElementById('btnHealthCheck');
      button.click(); button.click();
    }""")
    page.wait_for_function("() => __healthReads.length === 1")
    assert page.evaluate("() => __healthReads[0].url.endsWith('?fresh=1')")
    page.wait_for_selector("#systemHealth > .card-body.is-refreshing")
    assert page.locator("#btnHealthCheck .gp-spinner").count() == 1
    before = page.locator("#systemHealthContent").inner_html()
    page.evaluate("() => __healthReads[0].reject(new Error('Health read failed'))")
    page.wait_for_function("() => !document.querySelector('#systemHealth > .card-body').inert")
    assert page.locator("#systemHealthContent").inner_html() == before
    assert page.locator("#btnHealthCheck.btn-error").count() == 1
    assert page.locator("#btnHealthCheck .gp-spinner").count() == 0
    page.evaluate("() => document.getElementById('btnHealthCheck').click()")
    page.wait_for_function("() => __healthReads.length === 2")
    page.evaluate("() => __healthReads[1].respond()")
    page.wait_for_selector("#btnHealthCheck.btn-done")
    assert page.locator("#systemHealth > .card-body").get_attribute("aria-busy") is None
    assert page.locator("#btnHealthCheck").is_enabled()


def test_tables_release_busy_state_for_empty_results_without_geometry_drift(system_page):
    result = system_page.evaluate("""async () => {
      const body = document.getElementById('jobsTableBody');
      const box = body.closest('.table-responsive');
      const header = body.closest('table').querySelector('thead');
      const rects = () => [...header.querySelectorAll('th')].map(el => {
        const r = el.getBoundingClientRect(); return [r.x, r.width];
      });
      const before = rects(), minHeight = box.style.minHeight;
      GP.tableLoading(body, 7);
      const immediateBusy = body.inert && body.getAttribute('aria-busy') === 'true';
      await new Promise(resolve => setTimeout(resolve, 220));
      const during = rects(), shown = body.classList.contains('is-refreshing');
      body.innerHTML = GP.emptyStateRow(7, 'No matching jobs');
      await Promise.resolve(); // The real MutationObserver releases the state.
      return {before, during, shown, immediateBusy, inert: body.inert,
        busy: body.hasAttribute('aria-busy'), refreshing: body.classList.contains('is-refreshing'),
        heightRestored: box.style.minHeight === minHeight};
    }""")
    assert result["shown"]
    assert result["immediateBusy"]
    assert result["heightRestored"]
    assert not result["inert"]
    assert not result["busy"]
    assert not result["refreshing"]
    for before, during in zip(result["before"], result["during"], strict=True):
        assert during == pytest.approx(before, abs=0.5)


def test_new_content_retargets_a_running_height_transition(system_page):
    result = system_page.evaluate("""async () => {
      const box = document.querySelector('#systemHealth > .card-body');
      const write = height => { box.innerHTML = '<div style="height:' + height + 'px"></div>'; };
      write(80);
      GP.motion.panelIn(box);
      GP.motion.resize(box, () => write(160));
      await new Promise(resolve => setTimeout(resolve, 40));
      GP.motion.resize(box, () => write(320));
      const samples = [box.getBoundingClientRect().height];
      const start = performance.now();
      await new Promise(resolve => {
        const sample = () => {
          samples.push(box.getBoundingClientRect().height);
          if (performance.now() - start < 600) requestAnimationFrame(sample);
          else resolve();
        };
        requestAnimationFrame(sample);
      });
      const settled = box.getBoundingClientRect().height;
      const inline = box.style.height;
      box.style.height = 'auto';
      return {settled, natural: box.getBoundingClientRect().height, inline,
        opacity: getComputedStyle(box).opacity,
        largestStep: Math.max(...samples.slice(1).map((value, i) => Math.abs(value - samples[i])))};
    }""")
    assert result["settled"] == pytest.approx(result["natural"], abs=0.5)
    assert result["inline"] == ""
    assert result["largestStep"] < 100
    assert float(result["opacity"]) == 1

"""Navigation feedback follows pending requests and page script readiness."""

from __future__ import annotations

import os
from itertools import pairwise

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("navigation states need a running server", allow_module_level=True)


@pytest.fixture(params=[390, 1440])
def navigation_page(browser, context_for, live_server, request):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": request.param, "height": 1000},
        is_mobile=request.param == 390,
        has_touch=request.param == 390,
        service_workers="block",
    ) as context:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/?period=all&lang=en")
        page.wait_for_function("""() => window.GP?.beginTopProgress
          && document.documentElement.hasAttribute('data-gp-ready')
          && !document.getElementById('gp-top-progress').matches('.is-active,.is-finishing')""")
        yield page
        assert errors == []


def _busy(page, busy: bool):
    page.wait_for_function(
        "busy => document.getElementById('gp-top-progress')"
        ".classList.contains('is-active') === busy",
        arg=busy,
    )
    assert page.locator("#gp-top-progress").get_attribute("aria-hidden") == str(not busy).lower()
    assert page.locator("#gp-top-progress").get_attribute("aria-valuenow") is None


def _request(page, name: str, **attributes):
    page.evaluate(
        """([name, attributes]) => {
      const element = document.createElement('div');
      element.id = name;
      for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
      document.getElementById('main-content').appendChild(element);
      htmx.ajax('GET', '/qa/navigation-' + name,
        {source: element, target: element, swap: 'innerHTML'}).catch(() => {});
    }""",
        [name, attributes],
    )


def _finish_at_visible_edge(page):
    result = page.evaluate("""async () => {
      const bar = document.getElementById('gp-top-progress'), inner = bar.firstElementChild;
      const track = bar.getBoundingClientRect(), frames = [];
      window.__finishBar();
      await new Promise((resolve, reject) => {
        const deadline = performance.now() + 3000;
        function tick() {
          const rect = inner.getBoundingClientRect();
          const opacity = Number(getComputedStyle(bar).opacity);
          frames.push({left: rect.left, right: rect.right, opacity});
          if (opacity < .01) resolve();
          else if (performance.now() > deadline) reject(new Error('Progress did not finish'));
          else requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });
      return {left: track.left, edge: track.right, frames};
    }""")
    assert any(
        frame["opacity"] > 0.99
        and abs(frame["left"] - result["left"]) < 1
        and frame["right"] >= result["edge"] - 1
        for frame in result["frames"]
    ), result


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("accent", ["default", "blue", "indigo", "green", "red", "gray"])
@pytest.mark.parametrize("phase", [0, 0.1, 0.5, 0.8, 0.9, 0.99])
def test_continuous_fill_reaches_full_width_before_fading(navigation_page, theme, accent, phase):
    page = navigation_page
    _busy(page, False)
    page.evaluate(
        """([theme, accent]) => {
      document.documentElement.dataset.theme = theme;
      document.documentElement.dataset.accent = accent;
      window.__finishBar = GP.beginTopProgress();
    }""",
        [theme, accent],
    )
    result = page.evaluate(
        """async phase => {
      const bar = document.querySelector('#gp-top-progress'), inner = bar.firstElementChild;
      gsap.getTweensOf(inner)[0].pause().progress(phase);
      const track = bar.getBoundingClientRect();
      const color = getComputedStyle(inner).backgroundColor;
      const probe = document.createElement('span');
      probe.style.color = 'var(--primary)';
      document.body.appendChild(probe);
      const expectedColor = getComputedStyle(probe).color;
      probe.remove();
      const frames = [];
      const sample = () => {
        const rect = inner.getBoundingClientRect();
        frames.push({left: rect.left, right: rect.right,
          opacity: parseFloat(getComputedStyle(bar).opacity)});
      };
      sample();
      window.__finishBar();
      await new Promise((resolve, reject) => {
        const deadline = performance.now() + 3000;
        function tick() {
          sample();
          if (frames.at(-1).opacity < 0.01) resolve();
          else if (performance.now() > deadline) reject(new Error('Progress did not finish'));
          else requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });
      return {height: track.height, left: track.left, edge: track.right,
        color, expectedColor, frames};
    }""",
        phase,
    )
    assert result["height"] == 3
    assert result["color"] == result["expectedColor"]
    visible = [frame for frame in result["frames"] if frame["opacity"] > 0.99]
    assert visible
    assert all(abs(frame["left"] - result["left"]) < 1 for frame in visible)
    assert visible[-1]["right"] >= result["edge"] - 1
    assert all(after["right"] >= before["right"] - 1 for before, after in pairwise(visible))
    _busy(page, False)


def test_new_work_preserves_the_continuous_fill(navigation_page):
    page = navigation_page
    result = page.evaluate("""async () => {
      const release = GP.beginTopProgress(), bar = document.querySelector('#gp-top-progress');
      const inner = bar.firstElementChild;
      gsap.getTweensOf(inner)[0].pause().progress(.5);
      release();
      await new Promise(resolve => requestAnimationFrame(resolve));
      const before = inner.getBoundingClientRect().width;
      const next = GP.beginTopProgress();
      const after = inner.getBoundingClientRect().width;
      await new Promise(resolve => requestAnimationFrame(resolve));
      const during = inner.getBoundingClientRect().width;
      next();
      return {before, after, during};
    }""")
    assert result["after"] >= result["before"] - 1
    assert result["during"] >= result["before"] - 1


@pytest.mark.parametrize("stage", ["sweep", "fade"])
def test_new_request_cancels_the_previous_finish(navigation_page, stage):
    page = navigation_page
    page.evaluate("() => window.__firstBar = GP.beginTopProgress()")
    page.wait_for_timeout(150)
    page.evaluate("() => window.__firstBar()")
    if stage == "sweep":
        page.wait_for_timeout(50)
    else:
        page.wait_for_function("""() => {
          const bar = document.querySelector('#gp-top-progress');
          const opacity = Number(getComputedStyle(bar).opacity);
          return opacity > 0 && opacity < 1;
        }""")
    page.evaluate("() => window.__nextBar = GP.beginTopProgress()")
    page.wait_for_timeout(600)
    page.evaluate("() => window.__firstBar()")
    _busy(page, True)
    assert (
        page.locator("#gp-top-progress").evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        > 0.99
    )
    page.evaluate("() => window.__nextBar()")
    _busy(page, False)


def test_bfcache_restore_reloads_without_a_stale_bar(navigation_page):
    page = navigation_page
    page.evaluate("() => GP.beginTopProgress()")
    # Restored documents intentionally reload through the shared session handler.
    with page.expect_navigation(wait_until="load"):
        page.evaluate("""() => window.dispatchEvent(
          new PageTransitionEvent('pageshow', {persisted: true}))""")
    page.wait_for_function("() => !!GP.beginTopProgress")
    _busy(page, False)


def test_reduced_motion_keeps_a_static_fill(navigation_page):
    page = navigation_page
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function("() => GP.motion.reduced()")
    page.evaluate("() => window.__finishBar = GP.beginTopProgress()")
    page.wait_for_timeout(100)
    width = page.locator(".gp-top-progress-bar").evaluate("el => el.getBoundingClientRect().width")
    page.wait_for_timeout(700)
    assert (
        page.locator(".gp-top-progress-bar").evaluate("el => el.getBoundingClientRect().width")
        == width
    )
    assert (
        page.locator(".gp-top-progress-bar").evaluate("el => getComputedStyle(el).animationName")
        == "none"
    )
    _busy(page, True)
    _finish_at_visible_edge(page)
    _busy(page, False)


def test_continuous_feedback_finishes_without_gsap(navigation_page):
    page = navigation_page
    page.route("**/gsap*.js*", lambda route: route.fulfill(body="", content_type="text/javascript"))
    page.reload()
    page.wait_for_function("() => !!GP.beginTopProgress")
    assert not page.evaluate("() => GP.motion.available")
    page.evaluate("() => window.__finishBar = GP.beginTopProgress()")
    state = page.locator("#gp-top-progress").evaluate("""el => {
      const rect = el.getBoundingClientRect();
      return {opacity: parseFloat(getComputedStyle(el).opacity),
        fraction: el.firstElementChild.getBoundingClientRect().width / rect.width,
        animation: getComputedStyle(el.firstElementChild).animationName};
    }""")
    assert state["opacity"] == 1
    assert state["fraction"] == pytest.approx(0.9, abs=0.001)
    assert state["animation"] == "none"
    _finish_at_visible_edge(page)
    assert (
        page.locator("#gp-top-progress").evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        == 0
    )


@pytest.mark.parametrize("outcome", ["success", "failed", "malformed", "html", "cancelled"])
def test_mutation_feedback_follows_the_actual_response(navigation_page, outcome):
    page = navigation_page
    reads = []
    page.route("**/qa/progress-write", lambda route: reads.append(route))
    page.evaluate("""() => {
      window.__writeController = new AbortController();
      window.__write = null;
      GP.apiCall('/qa/progress-write', 'POST', {}, {
        maxRetries: 0, signal: window.__writeController.signal
      }).then(value => window.__write = {value}, error => window.__write = {error: error.name});
    }""")
    _busy(page, True)
    page.wait_for_timeout(100)
    assert len(reads) == 1
    if outcome == "cancelled":
        page.evaluate("() => window.__writeController.abort()")
    else:
        reads.pop().fulfill(
            status=400 if outcome == "failed" else 200,
            content_type="text/html" if outcome == "html" else "application/json",
            body=(
                "<html>Proxy error</html>"
                if outcome == "html"
                else "{broken"
                if outcome == "malformed"
                else '{"detail":"Result"}'
            ),
        )
    page.wait_for_function("() => window.__write !== null")
    _busy(page, False)
    result = page.evaluate("() => window.__write")
    assert ("value" in result) == (outcome == "success")
    if outcome in {"malformed", "html"}:
        assert result["error"] == "SyntaxError"
    for route in reads:
        route.abort()


@pytest.mark.parametrize("detached", [False, True])
def test_region_and_mutation_release_their_own_feedback(navigation_page, detached):
    page = navigation_page
    reads = []
    page.route("**/qa/progress-*", lambda route: reads.append(route))
    page.evaluate("""() => {
      const region = document.createElement('div');
      region.id = 'qa-region';
      region.innerHTML = GP.buttonHtml('Refresh', {id: 'qa-refresh'});
      document.querySelector('#main-content').appendChild(region);
      GP.refreshRegion({region, button: region.firstElementChild,
        load: () => GP.apiCall('/qa/progress-read', 'GET', null, {maxRetries: 0})});
      GP.apiCall('/qa/progress-write', 'POST', {}, {maxRetries: 0}).catch(() => {});
    }""")
    _busy(page, True)
    page.wait_for_timeout(100)
    assert len(reads) == 2
    region = page.locator("#qa-region")
    assert region.get_attribute("aria-busy") == "true"
    assert page.locator("#qa-refresh").is_disabled()
    if detached:
        region.evaluate("el => el.remove()")
    read = next(route for route in reads if route.request.method == "GET")
    read.fulfill(content_type="application/json", body='{"updated":true}')
    reads.remove(read)
    page.wait_for_timeout(100)
    _busy(page, True)
    reads.pop().fulfill(status=400, content_type="application/json", body='{"detail":"Failed"}')
    _busy(page, False)
    if not detached:
        assert region.get_attribute("aria-busy") is None
        assert not page.locator("#qa-refresh").is_disabled()


def test_background_api_reads_do_not_start_foreground_feedback(navigation_page):
    page = navigation_page
    reads = []
    page.route("**/qa/progress-poll", lambda route: reads.append(route))
    page.evaluate("""() => {
      GP.apiCall('/qa/progress-poll', 'GET', null, {maxRetries: 0}).catch(() => {});
    }""")
    page.wait_for_timeout(100)
    _busy(page, False)
    assert len(reads) == 1
    reads.pop().fulfill(content_type="application/json", body='{"status":"running"}')


def test_duplicate_failure_events_do_not_finish_another_request(navigation_page):
    page = navigation_page
    reads = []
    page.route("**/qa/navigation-*", lambda route: reads.append(route))
    try:
        _request(page, "one")
        _request(page, "two")
        page.wait_for_function("() => document.querySelectorAll('.htmx-request').length >= 2")
        for _ in range(100):
            if len(reads) == 2:
                break
            page.wait_for_timeout(20)
        assert len(reads) == 2
        _busy(page, True)
        reads.pop(0).fulfill(status=503, body="Expected test failure")
        page.wait_for_timeout(300)
        _busy(page, True)
        reads.pop().fulfill(status=200, body="Complete")
        _busy(page, False)
    finally:
        for route in reads:
            route.fulfill(status=200, body="Complete")


def test_removing_the_request_source_still_releases_feedback(navigation_page):
    page = navigation_page
    reads = []
    page.route("**/qa/navigation-*", lambda route: reads.append(route))
    try:
        _request(page, "removed")
        _busy(page, True)
        page.wait_for_timeout(100)
        page.locator("#removed").evaluate("element => element.remove()")
        reads.pop().fulfill(status=200, body="Complete")
        _busy(page, False)
    finally:
        for route in reads:
            route.fulfill(status=200, body="Complete")


@pytest.mark.parametrize("attributes", [{"data-no-progress": ""}, {"hx-trigger": "every 1m"}])
def test_silent_requests_do_not_start_navigation_feedback(navigation_page, attributes):
    page = navigation_page
    reads = []
    page.route("**/qa/navigation-*", lambda route: reads.append(route))
    try:
        _request(page, "silent", **attributes)
        page.wait_for_timeout(100)
        assert len(reads) == 1
        _busy(page, False)
    finally:
        for route in reads:
            route.fulfill(status=200, body="Complete")


def test_cancelled_before_request_does_not_leave_feedback(navigation_page):
    page = navigation_page
    page.evaluate("""() => document.body.addEventListener('htmx:beforeRequest', event => {
      if (event.detail.elt.id === 'cancelled') event.preventDefault();
    })""")
    _request(page, "cancelled")
    page.wait_for_timeout(100)
    _busy(page, False)


def test_slow_page_scripts_keep_the_page_pending_until_ready(navigation_page, live_server):
    page = navigation_page
    scripts = []
    page.route("**/js/pages/admin-users*.js*", lambda route: scripts.append(route))
    try:
        page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
        page.wait_for_url(live_server + "/dashboard/admin/users")
        page.wait_for_timeout(3500)
        assert scripts
        _busy(page, True)
        main = page.locator('xpath=//main[@id="main-content"]')
        assert main.get_attribute("aria-busy") == "true"
        assert "is-arriving" in main.get_attribute("class")
        assert page.evaluate("() => document.querySelectorAll('#main-content').length") == 1
        scripts.pop().continue_()
        _busy(page, False)
        assert page.locator("#usersTable").count() == 1
        assert main.get_attribute("aria-busy") is None
    finally:
        for route in scripts:
            route.continue_()


@pytest.mark.parametrize("failure", ["network", "timeout", "html"])
def test_failed_page_scripts_present_a_shared_retry(navigation_page, live_server, failure):
    page = navigation_page
    held = []

    def serve_script(route):
        if failure == "network":
            route.abort()
        elif failure == "html":
            route.fulfill(status=200, content_type="text/html", body="<html>Proxy error</html>")
        else:
            held.append(route)

    page.route("**/js/pages/admin-users*.js*", serve_script)
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_url(live_server + "/dashboard/admin/users")
    page.wait_for_selector("#main-content .gp-retry-btn")
    _busy(page, False)
    assert page.locator("#main-content .table-empty-state--error").count() == 1
    main = page.locator('xpath=//main[@id="main-content"]')
    assert "is-arriving" not in main.get_attribute("class")
    assert main.get_attribute("aria-busy") is None
    if held:
        held.pop().fulfill(status=200, body="window.__lateNavigationScript = true;")
        page.wait_for_timeout(100)
        assert not page.evaluate("() => !!window.__lateNavigationScript")
    page.unroute("**/js/pages/admin-users*.js*")
    page.locator("#main-content .gp-retry-btn").click()
    page.wait_for_selector("#usersTable")

"""The real CSP runtime avoids retired globals and keeps bindings functional."""

from pathlib import Path

import pytest
from scripts.vendor_alpine_csp import ALPINE_VERSION

pytestmark = pytest.mark.e2e
VENDOR = Path(__file__).resolve().parents[2] / "src/app/templates/static/vendor"


@pytest.mark.parametrize("instrument", [False, True])
def test_alpine_does_not_read_fenced_frame_api(browser, instrument):
    with browser.new_context(service_workers="block") as context:
        page = context.new_page()
        errors = []
        deprecations = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        cdp = context.new_cdp_session(page)
        cdp.on(
            "Audits.issueAdded",
            lambda event: (
                deprecations.append(event) if event["issue"]["code"] == "DeprecationIssue" else None
            ),
        )
        cdp.send("Audits.enable")
        page.route(
            "http://127.0.0.1:18999/**",
            lambda route: route.fulfill(
                content_type="text/html",
                body="""<section x-data="{ count: 0, open: true }">
                  <button id="increment" @click="count++" x-text="count"></button>
                  <button id="toggle" @click="open = !open">Toggle</button>
                  <div id="content" x-show="open" x-collapse>Content</div>
                </section>""",
            ),
        )
        page.goto("http://127.0.0.1:18999/alpine-runtime")
        if instrument:
            page.evaluate("""() => {
              window.__fenceReads = 0;
              Object.defineProperty(window, 'fence', { configurable: true,
                get() { window.__fenceReads++; return null; } });
            }""")
        for package in ["collapse", "csp"]:
            page.add_script_tag(path=str(VENDOR / f"alpine-{package}-{ALPINE_VERSION}.min.js"))
        page.wait_for_function(
            "window.Alpine && document.querySelector('#increment').textContent === '0'"
        )
        page.locator("#increment").click()
        assert page.locator("#increment").inner_text() == "1"
        page.locator("#toggle").click()
        page.wait_for_function("!document.getElementById('content').checkVisibility()")
        page.locator("#toggle").click()
        page.wait_for_function("document.getElementById('content').checkVisibility()")
        if instrument:
            assert page.evaluate("window.__fenceReads") == 0
        assert not errors
        assert not deprecations


@pytest.mark.parametrize("width", [390, 1440])
def test_nested_summary_controls_do_not_toggle_the_disclosure(browser, width):
    with browser.new_context(viewport={"width": width, "height": 800}) as context:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content("""<!doctype html><details id="details">
          <summary id="summary">Panel <button type="button" id="copy">Copy</button>
            <a id="link" href="#target">Link</a></summary>
          <div>Contents</div>
        </details>""")
        page.add_script_tag(path=str(VENDOR.parent / "js/motion.js"))
        page.locator("#copy").click()
        assert not page.locator("#details").evaluate("el => el.open")
        page.locator("#link").click()
        assert not page.locator("#details").evaluate("el => el.open")
        page.locator("#summary").click(position={"x": 5, "y": 5})
        assert page.locator("#details").evaluate("el => el.open")
        page.locator("#copy").click()
        assert page.locator("#details").evaluate("el => el.open")
        page.locator("#summary").click(position={"x": 5, "y": 5})
        assert not page.locator("#details").evaluate("el => el.open")
        assert not errors

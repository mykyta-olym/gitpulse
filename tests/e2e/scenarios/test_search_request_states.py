"""The global search distinguishes remote failure, empty data and obsolete reads."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("search states need a running server", allow_module_level=True)


@pytest.fixture(params=[390, 1440])
def search_page(browser, context_for, live_server, request):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": request.param, "height": 1000},
        has_touch=request.param == 390,
        is_mobile=request.param == 390,
        service_workers="block",
    ) as context:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/?period=all&lang=en")
        page.wait_for_function("() => !!GP.openSearchPalette")
        page.evaluate("""() => {
          const fetch = window.fetch;
          window.__searchReads = [];
          window.fetch = (url, options) => String(url).includes('/dashboard/search?')
            ? new Promise(resolve => __searchReads.push({url: String(url), signal: options.signal,
              respond(data, status = 200) {resolve(new Response(JSON.stringify(data), {
                status, headers: {'Content-Type': 'application/json'}
              }));}})) : fetch(url, options);
          GP.openSearchPalette();
        }""")
        yield page
        assert errors == []


def _search(page, query: str, count: int = 1):
    page.locator("#searchModalInput").fill(query)
    page.wait_for_function("count => __searchReads.length === count", arg=count)


def _respond(page, index: int = 0, data=None, status: int = 200):
    page.evaluate(
        "([index, data, status]) => __searchReads[index].respond(data, status)",
        [index, data or {}, status],
    )


def test_failed_search_has_a_shared_error_and_retry(search_page):
    page = search_page
    _search(page, "@probe")
    assert page.locator("#searchModalResults").get_attribute("aria-busy") == "true"
    assert page.locator("#searchModalResults .gp-block-loading").count() == 1
    _respond(page, data={"detail": "Search service unavailable"}, status=503)
    page.wait_for_selector("#searchModalResults .gp-retry-btn")
    assert "Search service unavailable" in page.locator("#searchModalResults").inner_text()
    assert "No users found" not in page.locator("#searchModalResults").inner_text()
    assert page.locator("#searchModalResults").get_attribute("aria-busy") is None
    page.locator("#searchModalResults .gp-retry-btn").click()
    page.wait_for_function("() => __searchReads.length === 2")
    _respond(page, index=1, data={"users": [{"name": "Recovered user", "username": "probe"}]})
    page.wait_for_selector("#searchModalResults .gl-dropdown-item")
    assert "Recovered user" in page.locator("#searchModalResults").inner_text()
    assert page.locator("#searchModalResults .gp-block-loading").count() == 0
    assert page.locator("#searchModalResults").get_attribute("aria-busy") is None


def test_only_a_successful_empty_response_reports_no_matches(search_page):
    page = search_page
    _search(page, "#no-match")
    _respond(page)
    page.wait_for_selector("#searchModalResults .gl-dropdown-empty")
    assert "No students found" in page.locator("#searchModalResults").inner_text()
    assert page.locator("#searchModalResults .gp-retry-btn").count() == 0


def test_old_response_is_invalidated_before_the_next_debounce(search_page):
    page = search_page
    _search(page, "@old")
    page.evaluate("""() => {
      const input = document.getElementById('searchModalInput');
      input.value = '@new';
      input.dispatchEvent(new Event('input', {bubbles: true}));
      __searchReads[0].respond({users: [{name: 'Obsolete response', username: 'old'}]});
    }""")
    page.wait_for_timeout(60)
    assert "Obsolete response" not in page.locator("#searchModalResults").inner_text()
    assert page.evaluate("() => __searchReads[0].signal.aborted")
    page.wait_for_function("() => __searchReads.length === 2")
    _respond(page, index=1, data={"users": [{"name": "Current response", "username": "new"}]})
    page.wait_for_selector("#searchModalResults .gl-dropdown-item")
    assert "Current response" in page.locator("#searchModalResults").inner_text()


@pytest.mark.parametrize("destination", ["empty", "pages", "close"])
def test_cancelling_a_search_does_not_leave_loading_or_a_late_error(search_page, destination):
    page = search_page
    _search(page, "@old")
    if destination == "close":
        page.locator("#searchModalInput").press("Escape")
    else:
        page.locator("#searchModalInput").fill("" if destination == "empty" else ">Dashboard")
    _respond(page, data={"detail": "Obsolete failure"}, status=503)
    page.wait_for_timeout(300)
    assert page.evaluate("() => __searchReads[0].signal.aborted")
    assert page.locator("#searchModalResults").get_attribute("aria-busy") is None
    assert page.locator("#searchModalResults .gp-block-loading").count() == 0
    assert "Obsolete failure" not in page.locator("#searchModalResults").inner_text()


def test_hybrid_search_keeps_local_matches_when_the_remote_read_fails(search_page):
    page = search_page
    _search(page, "Dashboard")
    assert page.locator('#searchModalResults a[href="/dashboard/"]').count() == 1
    _respond(page, data={"detail": "Remote results unavailable"}, status=503)
    page.wait_for_selector("#searchModalResults .gp-retry-btn")
    assert page.locator('#searchModalResults a[href="/dashboard/"]').count() == 1

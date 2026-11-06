"""Fragment history keeps the current DOM; old anchor retries stay on their page."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs GITPULSE_E2E_BASE_URL", allow_module_level=True)


def _ready(page):
    page.wait_for_function("""() => !!window.GP?.navigateTo
      && !document.querySelector('#main-content.is-arriving, #main-content.is-navigating')""")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("full_href", [False, True])
@pytest.mark.parametrize("dirty", [False, True])
def test_fragment_back_and_forward_preserve_the_form(
    context_for, live_server, width, full_href, dirty
):
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    if dirty:
        field = page.locator('input[name="keyboard_shortcuts_enabled"]')
        field.set_checked(not field.is_checked())
        page.wait_for_function("() => GP.hasUnsavedState()")
    requests = []
    page.on(
        "request",
        lambda request: requests.append(request) if request.headers.get("hx-request") else None,
    )
    page.evaluate(
        """full => {
      window.__originalForm = document.querySelector('#preferencesForm');
      // Client-side filters also replace their current entry's query string.
      history.replaceState(null, '', '?client-filter=kept');
      const link = document.createElement('a');
      link.id = 'fragmentLink'; link.textContent = 'Syntax';
      link.href = (full ? location.pathname + location.search : '') + '#syntax-highlighting';
      document.querySelector('#main-content').prepend(link);
    }""",
        full_href,
    )
    page.locator("#fragmentLink").click()
    page.wait_for_function("() => location.hash === '#syntax-highlighting'")
    page.go_back()
    page.wait_for_function("() => location.hash === ''")
    page.wait_for_timeout(200)
    assert not page.locator("#gpConfirmDialog.active").count(), (
        "fragment history asked to discard edits"
    )
    assert page.evaluate("window.__originalForm === document.querySelector('#preferencesForm')")
    assert page.evaluate("GP.hasUnsavedState()") is dirty
    page.go_forward()
    page.wait_for_function("() => location.hash === '#syntax-highlighting'")
    page.wait_for_timeout(200)
    assert page.evaluate("window.__originalForm === document.querySelector('#preferencesForm')")
    assert not requests, "fragment history fetched a replacement page"
    page.evaluate("GP.clearAllDirtyReasons()")


@pytest.mark.parametrize("width", [390, 1440])
def test_a_missing_anchor_cannot_reset_the_next_page_scroll(context_for, live_server, width):
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/", wait_until="networkidle")
    page.evaluate("GP.navigateTo('/dashboard/preferences#missing-section')")
    page.wait_for_url("**/preferences#missing-section")
    page.evaluate("GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_url("**/dashboard/admin/users")
    _ready(page)
    before = page.evaluate("""() => {
      const scroller = document.querySelector('.gl-page-content');
      scroller.scrollTop = 600;
      return scroller.scrollTop;
    }""")
    assert before > 0, "the users page has no scrollable content"
    page.wait_for_timeout(1000)
    assert page.evaluate("document.querySelector('.gl-page-content').scrollTop") == pytest.approx(
        before, abs=1
    )


@pytest.mark.parametrize("width", [390, 1440])
def test_encoded_cross_page_fragments_use_the_local_scroller(context_for, live_server, width):
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/", wait_until="networkidle")
    page.evaluate("GP.navigateTo('/dashboard/preferences#%73yntax-highlighting')")
    page.wait_for_url("**/preferences#%73yntax-highlighting")
    _ready(page)
    page.wait_for_timeout(350)
    position = page.evaluate("""() => {
      const scroller = document.querySelector('.gl-page-content');
      return {offset: document.querySelector('#syntax-highlighting').getBoundingClientRect().top
        - scroller.getBoundingClientRect().top, scroll: scroller.scrollTop, windowY: scrollY};
    }""")
    assert position["scroll"] > 0
    assert position["offset"] == pytest.approx(16, abs=1)
    assert position["windowY"] == 0


def test_back_to_another_query_still_loads_that_page(context_for, live_server):
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    page.evaluate(
        """() => {
          window.__documentToken = 'stable';
          window.__originalForm = document.querySelector('#preferencesForm');
        }"""
    )
    page.evaluate("GP.navigateTo('/dashboard/preferences?history-test=1')")
    page.wait_for_url("**/preferences?history-test=1")
    _ready(page)
    assert page.evaluate("window.__originalForm !== document.querySelector('#preferencesForm')")
    page.evaluate("window.__queryForm = document.querySelector('#preferencesForm')")
    page.go_back()
    page.wait_for_function("() => location.search === ''")
    page.wait_for_function(
        "() => window.__queryForm !== document.querySelector('#preferencesForm')"
    )
    _ready(page)
    assert page.evaluate("window.__documentToken") == "stable"


@pytest.mark.parametrize("width", [390, 1440])
def test_refreshing_a_fragment_does_not_recentre_an_old_highlight(context_for, live_server, width):
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(
        live_server + "/dashboard/preferences?highlight=syntax-highlighting",
        wait_until="networkidle",
    )
    page.wait_for_timeout(350)
    before = page.evaluate("""() => {
      const scroller = document.querySelector('.gl-page-content');
      scroller.scrollTop = 1200;
      return scroller.scrollTop;
    }""")
    page.evaluate("""() => document.body.dispatchEvent(new CustomEvent('htmx:afterSettle', {
      bubbles: true, detail: {target: document.querySelector('#main-content')}
    }))""")
    page.wait_for_timeout(350)
    assert page.evaluate("document.querySelector('.gl-page-content').scrollTop") == pytest.approx(
        before, abs=1
    )


def test_back_after_a_client_filter_change_loads_the_previous_query(context_for, live_server):
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    page.evaluate("""() => {
      history.replaceState(null, '', '?client-filter=first');
      history.pushState(null, '', '#syntax-highlighting');
      history.replaceState(null, '', '?client-filter=second#syntax-highlighting');
      window.__filteredForm = document.querySelector('#preferencesForm');
    }""")
    page.go_back()
    page.wait_for_function("() => location.search === '?client-filter=first'")
    page.wait_for_function(
        "() => window.__filteredForm !== document.querySelector('#preferencesForm')"
    )
    _ready(page)


def test_cancelling_back_restores_the_current_query_and_fragment(context_for, live_server):
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/", wait_until="networkidle")
    page.evaluate("GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url("**/dashboard/preferences")
    _ready(page)
    field = page.locator('input[name="keyboard_shortcuts_enabled"]')
    field.set_checked(not field.is_checked())
    page.wait_for_function("() => GP.hasUnsavedState()")
    page.evaluate("""() => {
      history.replaceState(null, '', '?client-filter=kept#syntax-highlighting');
      window.__editedForm = document.querySelector('#preferencesForm');
    }""")
    page.go_back()
    page.locator("#gpConfirmDialog.active").wait_for()
    page.keyboard.press("Escape")
    page.wait_for_url("**/preferences?client-filter=kept#syntax-highlighting")
    assert page.evaluate("window.__editedForm === document.querySelector('#preferencesForm')")
    assert page.evaluate("GP.hasUnsavedState()")
    page.evaluate("GP.clearAllDirtyReasons()")

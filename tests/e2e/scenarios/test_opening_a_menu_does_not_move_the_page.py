"""Opening a menu must not move the page underneath it.

The per-page selector at the bottom of a table did. Its menu is `position:
absolute`, which takes it out of the FLOW but not out of the scroll
container's SCROLLABLE OVERFLOW - so while closed, a 170px menu sitting below
its toggle near the bottom of the page added 49px to the content's scroll
height. Opening it moves the menu to <body>, that 49px goes with it, and the
browser then clamps a scroll position that is suddenly past the end. The page
lurches upward at the exact moment the reader is aiming at a menu item.

Measured on User Management before the fix: scrollHeight 1150 -> 1101 and
scrollTop 342 -> 293 on one click.

This is geometry during an interaction, which nothing else in the suite looks
at: the page walk never clicks, and the controls walk clicks and re-audits
layout but does not watch the scroll position across the click.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_PAGES = ("/dashboard/admin/users", "/dashboard/admin/system", "/dashboard/admin/events")

_SNAPSHOT = """
() => {
  const sc = document.querySelector('.gl-page-content');
  return sc ? {top: Math.round(sc.scrollTop), height: Math.round(sc.scrollHeight)} : null;
}
"""


@pytest.mark.parametrize("path", _PAGES)
def test_the_per_page_menu_opens_without_moving_the_page(
    context_for, live_server: str, path: str
) -> None:
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    response = page.goto(live_server + path, wait_until="domcontentloaded")
    if not response or response.status >= 400:
        pytest.skip(f"{path} answered {response.status if response else 'nothing'}")
    page.wait_for_timeout(1800)
    # A first visit offers the page's tour in a card fixed at the bottom right -
    # over the per-page selector of a table that ends there (Events). A reader
    # closes it to reach the selector; a click through it made Playwright scroll
    # the page back and forth looking for an unobscured point, which read as
    # "opening the menu moved the page 0 -> 70".
    welcome_close = page.query_selector(".gp-tour-welcome-close")
    if welcome_close and welcome_close.is_visible():
        welcome_close.click()
        page.wait_for_timeout(400)

    # A page can hold more than one paginated table (Events has two), and the
    # first may sit in a card that is collapsed. Take the first selector a
    # reader could actually click.
    toggles = [
        t
        for t in page.query_selector_all(".gl-page-size-dropdown .gl-dropdown-toggle")
        if t.is_visible()
    ]
    if not toggles:
        pytest.skip(f"{path} has no per-page selector a reader can reach")
    toggle = toggles[0]

    # Put the control near the bottom of the scroller, which is the only place
    # the defect can show: the clamp only happens when the lost height was
    # below the current scroll position.
    toggle.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    before = page.evaluate(_SNAPSHOT)
    assert before is not None, "no scroll container to measure"
    toggle.click()
    page.wait_for_timeout(450)
    after = page.evaluate(_SNAPSHOT)

    menu = page.query_selector(".gl-dropdown-menu[data-gl-portal]")
    opened = bool(menu and (menu.bounding_box() or {}).get("height", 0) > 4)
    ctx.close()

    assert opened, f"the per-page menu did not open on {path} - nothing was tested"
    assert after["height"] == before["height"], (
        f"{path}: opening the menu changed the page's scroll height "
        f"{before['height']} -> {after['height']}"
    )
    assert after["top"] == before["top"], (
        f"{path}: opening the menu moved the page {before['top']} -> {after['top']}"
    )

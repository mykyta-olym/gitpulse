"""A setting the reader chooses has to change what the reader sees.

Three did not, and each failed silently - the value saved, came back on the next
request, and changed nothing:

* **Start with the sidebar collapsed** could not be turned on at all. The
  sidebar seeded `localStorage['sidebar-collapsed'] = 'false'` on the FIRST page
  load, and the account default was consulted only while that key was absent -
  so after any visit, on any device, the switch was dead for the life of the
  browser profile.
* **Time format** and **Use relative times** are applied to
  `time[data-localize-time]` and to nothing else, and exactly one template in
  the app emitted that element. Every other stamp was printed by `strftime` or
  `toLocaleString()`, which neither setting can reach.

Each test drives the real preferences endpoint and then reads the page, in the
order a reader meets it.
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

_SAVE = """async (body) => {
  try {
    await GP.apiCall('/dashboard/api/preferences', 'POST', body, {maxRetries: 0});
    return 200;
  } catch (e) { return (e && e.status) || String(e).slice(0, 40); }
}"""

_SIDEBAR = """() => {
  const s = document.querySelector('.gl-sidebar');
  return s ? {width: Math.round(s.getBoundingClientRect().width),
              collapsed: s.classList.contains('collapsed')} : null;
}"""

_STAMPS = """() => {
  const els = [...document.querySelectorAll('time[data-localize-time]')];
  return {total: els.length,
          localized: els.filter(e => e.dataset.localized === '1').length,
          texts: els.map(e => (e.textContent || '').trim())};
}"""


def _save(page, body) -> None:
    page.goto(
        f"{os.environ['GITPULSE_E2E_BASE_URL']}/dashboard/preferences",
        wait_until="domcontentloaded",
    )
    page.wait_for_timeout(1800)
    assert page.evaluate(_SAVE, body) == 200, f"the preferences endpoint refused {body}"


#: What every test here changes, at the account's defaults.
_DEFAULTS = {"sidebar_collapsed": False, "time_format": "system", "use_relative_times": True}


@pytest.fixture(autouse=True)
def _put_the_settings_back(context_for):
    """These tests change the e2e admin's own preferences, which live on its
    account row and outlast the test. Left collapsed, the sidebar's labels read
    as "unreachable text" to every layout walk of every later run - 26 of one
    walk's findings and 31 of another's were that, not a page."""
    yield
    _save(context_for("admin").new_page(), _DEFAULTS)


def test_the_collapsed_sidebar_can_be_turned_on_after_a_normal_visit(
    context_for, live_server: str
) -> None:
    """The order is the point: visit first, THEN change the setting."""
    page = context_for("admin").new_page()

    _save(page, {"sidebar_collapsed": False})
    page.goto(f"{live_server}/dashboard", wait_until="domcontentloaded")
    page.wait_for_timeout(1600)
    before = page.evaluate(_SIDEBAR)
    assert before, "the page has no sidebar to measure"
    assert not before["collapsed"], "the sidebar did not start expanded"

    _save(page, {"sidebar_collapsed": True})
    page.goto(f"{live_server}/dashboard", wait_until="domcontentloaded")
    page.wait_for_timeout(1600)
    after = page.evaluate(_SIDEBAR)

    assert after["collapsed"], (
        "turning on 'Start with the sidebar collapsed' changed nothing - the "
        f"sidebar is still {after['width']}px, as it was before"
    )
    assert after["width"] < before["width"]


def test_a_reader_who_collapses_it_by_hand_still_wins(context_for, live_server: str) -> None:
    """The account default is a default, not an override."""
    page = context_for("admin").new_page()
    _save(page, {"sidebar_collapsed": True})
    page.goto(f"{live_server}/dashboard", wait_until="domcontentloaded")
    page.wait_for_timeout(1600)
    assert page.evaluate(_SIDEBAR)["collapsed"]

    page.evaluate(
        "() => { const b = document.querySelector("
        "'.sidebar-toggle, #sidebarToggle, [data-sidebar-toggle]'); if (b) b.click(); }"
    )
    page.wait_for_timeout(700)
    page.goto(f"{live_server}/dashboard", wait_until="domcontentloaded")
    page.wait_for_timeout(1600)

    assert not page.evaluate(_SIDEBAR)["collapsed"], (
        "the reader expanded the sidebar and the account default collapsed it "
        "again on the next page - their own choice has to out-rank it"
    )


def test_the_time_settings_reach_a_page_that_shows_times(context_for, live_server: str) -> None:
    page = context_for("admin").new_page()

    _save(page, {"time_format": "24h", "use_relative_times": True})
    page.goto(f"{live_server}/dashboard/admin/system", wait_until="domcontentloaded")
    page.wait_for_timeout(2400)
    relative = page.evaluate(_STAMPS)
    assert relative["total"], (
        "this page shows timestamps but not one of them is an element the "
        "reader's time settings can act on"
    )
    assert relative["localized"] == relative["total"], (
        f"{relative['total'] - relative['localized']} stamps were never localised - "
        "markup built by page JS is not being picked up"
    )

    _save(page, {"time_format": "12h", "use_relative_times": False})
    page.goto(f"{live_server}/dashboard/admin/system", wait_until="domcontentloaded")
    page.wait_for_timeout(2400)
    absolute = page.evaluate(_STAMPS)

    assert absolute["texts"] != relative["texts"], (
        "switching to absolute 12h changed nothing on the page; it still reads "
        f"{relative['texts'][:2]}"
    )
    assert any("AM" in t or "PM" in t for t in absolute["texts"]), (
        f"12h was chosen and no stamp carries AM/PM: {absolute['texts'][:3]}"
    )


def test_every_page_that_prints_a_moment_uses_the_shared_element(
    context_for, live_server: str
) -> None:
    """A stamp printed any other way is one the settings cannot reach."""
    page = context_for("admin").new_page()
    _save(page, {"time_format": "12h", "use_relative_times": False})

    for path in ("/dashboard/admin/users", "/dashboard/admin/system"):
        page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
        page.wait_for_timeout(2200)
        seen = page.evaluate(_STAMPS)
        assert seen["total"], f"{path} shows no localisable timestamp at all"
        assert seen["localized"] == seen["total"], (
            f"{path} left {seen['total'] - seen['localized']} stamps unlocalised"
        )

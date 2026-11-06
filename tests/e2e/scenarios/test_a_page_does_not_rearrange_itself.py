"""What a reader sees on the first frame is what they keep seeing.

Five reports, all from the same walk through the course and group pages:

* the course header's actions were rendered a size smaller than every other
  page header's, so the one page that had just gained them looked wrong;
* a five-figure strip was added above the group's content and was not wanted;
* the page slid sideways while it loaded - the sidebar's collapsed state came
  from JavaScript AFTER the first paint, so the whole content well, header
  buttons and all, jumped ~190px left one frame in;
* the groups table spread six percentage columns across the full width whatever
  the rows held, and its Actions column did not stick like every other one;
* the number tiles inside a card had their chrome taken off.

The layout one is measured with the browser's own layout-shift observer, which
is the instrument that answers "did anything move" without an opinion.
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

_CLS = """
window.__cls = 0; window.__moved = [];
new PerformanceObserver((list) => {
  for (const e of list.getEntries()) {
    if (e.hadRecentInput) continue;
    window.__cls += e.value;
    (e.sources || []).forEach(s => {
      const n = s.node;
      if (n && n.nodeType === 1) {
        window.__moved.push(n.tagName.toLowerCase() + (n.id ? '#' + n.id : ''));
      }
    });
  }
}).observe({type: 'layout-shift', buffered: true});
"""

_SAVE = """async (body) => {
  try {
    await GP.apiCall('/dashboard/api/preferences', 'POST', body, {maxRetries: 0});
    return 200;
  } catch (e) { return (e && e.status) || String(e).slice(0, 40); }
}"""


def _first_course_link(page) -> str | None:
    """The course OVERVIEW, not one of its sub-pages.

    The row also links to `/courses/<id>/teachers`, which matched a plain
    substring search and sent every check to a page with none of this on it.
    """
    return page.evaluate(
        r"""() => {
          for (const a of document.querySelectorAll('a[href]')) {
            // Any link INTO a course; the overview is that link without its tail.
            const m = (a.getAttribute('href') || '')
              .match(/^(\/dashboard\/courses\/[0-9a-f-]{36})(\/|$)/);
            if (m) return m[1];
          }
          return null;
        }"""
    )


def _a_course(page, base: str) -> str:
    """The courses table is rendered by page JS, so poll rather than guess."""
    page.goto(f"{base}/dashboard/admin/courses", wait_until="domcontentloaded")
    for _ in range(12):
        page.wait_for_timeout(700)
        href = _first_course_link(page)
        if href:
            return href
    pytest.skip("this database has no course to open")
    raise AssertionError("unreachable")


def _save(page, base: str, body) -> None:
    page.goto(f"{base}/dashboard/preferences", wait_until="domcontentloaded")
    page.wait_for_timeout(1800)
    assert page.evaluate(_SAVE, body) == 200, f"the preferences endpoint refused {body}"


def test_the_page_does_not_slide_when_the_sidebar_starts_collapsed(
    context_for, live_server: str
) -> None:
    """The collapsed state has to be on the first painted frame.

    It used to be applied by sidebar.js after paint, so every page drew a 240px
    sidebar and then snapped it to 48px, dragging the content well - and the
    page header's buttons with it - across the screen. 0.115 CLS, measured.
    """
    ctx = context_for("admin")
    page = ctx.new_page()
    page.add_init_script(_CLS)

    _save(page, live_server, {"sidebar_collapsed": True})
    try:
        course = _a_course(page, live_server)

        page.goto(f"{live_server}{course}", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        width = page.evaluate(
            "() => { const s = document.querySelector('.gl-sidebar');"
            " return s ? Math.round(s.getBoundingClientRect().width) : null; }"
        )
    finally:
        # The setting lives on the e2e admin's account and outlasts this test:
        # left on, every later walk saw a collapsed sidebar and reported its
        # hidden labels as "unreachable text" - most of four tests' findings.
        _save(context_for("admin").new_page(), live_server, {"sidebar_collapsed": False})
    assert width is not None, "the page has no sidebar to measure"
    assert width < 120, f"the sidebar was asked to start collapsed and is {width}px wide"

    cls = page.evaluate("() => window.__cls")
    moved = page.evaluate("() => [...new Set(window.__moved)]")
    assert cls < 0.02, (
        f"the page rearranged itself while loading (CLS {cls:.4f}); these moved: {moved}"
    )
    assert "div#glPage" not in moved, "the whole content well slid sideways after paint"


def test_the_course_header_actions_are_the_size_every_header_uses(
    context_for, live_server: str
) -> None:
    page = context_for("admin").new_page()
    course = _a_course(page, live_server)
    page.goto(f"{live_server}{course}", wait_until="domcontentloaded")
    page.wait_for_timeout(2600)

    heights = page.evaluate(
        """() => [...document.querySelectorAll('.page-header-actions .btn')]
             .map(b => Math.round(b.getBoundingClientRect().height))"""
    )
    if not heights:
        pytest.skip("this role sees no actions on the course header")
    assert min(heights) >= 32, (
        f"the course header's buttons are smaller than the rest of the app: {heights}"
    )


def test_the_groups_table_sizes_to_its_content_and_pins_its_actions(
    context_for, live_server: str
) -> None:
    """Every other table with an Actions column pins it; this one did not."""
    page = context_for("admin").new_page()

    read = """() => {
      const t = document.getElementById('teamsTable');
      if (!t) return null;
      const cells = [...t.querySelectorAll('tbody tr:first-child td')];
      if (!cells.length) return null;
      return {last: getComputedStyle(cells[cells.length - 1]).position,
              layout: getComputedStyle(t).tableLayout};
    }"""

    # Not every course has groups; walk the list until one does, rather than
    # skipping on the first empty one and reporting nothing.
    page.goto(f"{live_server}/dashboard/admin/courses", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    courses = page.evaluate(
        r"""() => [...new Set([...document.querySelectorAll('a[href]')]
             .map(a => (a.getAttribute('href') || '')
               .match(/^(\/dashboard\/courses\/[0-9a-f-]{36})(\/|$)/))
             .filter(Boolean).map(m => m[1]))]"""
    )
    table = None
    for href in courses[:6]:
        page.goto(f"{live_server}{href}", wait_until="domcontentloaded")
        page.wait_for_timeout(2600)
        table = page.evaluate(read)
        if table is not None:
            break
    if table is None:
        pytest.skip("no course in this database has a group to render")
    assert table["last"] == "sticky", (
        "the Actions column does not stay in view when the groups table scrolls, "
        "though every other table with one does"
    )
    assert table["layout"] == "auto", (
        "the groups table is back on fixed percentage columns, which spend the "
        "full width whatever the rows hold"
    )


def test_the_numbers_inside_a_card_keep_their_own_chrome(context_for, live_server: str) -> None:
    page = context_for("admin").new_page()
    course = _a_course(page, live_server)
    page.goto(f"{live_server}{course}/activity", wait_until="domcontentloaded")
    page.wait_for_timeout(2600)

    tile = page.evaluate(
        """() => {
          const el = document.querySelector('.stats-grid > .gl-home-stat');
          if (!el) return null;
          const cs = getComputedStyle(el);
          return {border: parseFloat(cs.borderTopWidth), radius: parseFloat(cs.borderRadius)};
        }"""
    )
    if tile is None:
        pytest.skip("the activity page rendered no stat tiles")
    assert tile["border"] > 0, f"the tiles lost their border again: {tile}"
    assert tile["radius"] > 0, f"the tiles lost their rounded corners again: {tile}"

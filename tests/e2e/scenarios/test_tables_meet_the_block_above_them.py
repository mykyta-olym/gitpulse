"""A table under a header owns neither the top corners nor a second line.

Both of these are cascade questions, and a cascade question can only be settled
in a browser. The rounding rule in tables.css has been "fixed" twice from the
source - each time by adding a selector that read correctly and then lost to one
already there - and both times the table went on drawing a 12px top corner under
a square header, which is the notch of dark ground that gets reported from a
screenshot as "an unlit corner above CODE".

  * **Rounding** - where a table runs FLUSH to the edges of the block holding it
    (a card body with no padding, a disclosure's panel, a TAB PANEL under its
    strip) that block owns the top edge, and the table must not round it as
    well. Two radii on one corner is the defect: the card body clips at 8px
    while the table rounds at 12px, so 4px of arc shows the ground behind the
    header row.

    The tab-panel shape is the same bug in a third disguise, and it arrived with
    the cards that grew tabs (Users, System's Configuration, the student page's
    Issues): the strip is not the table's SIBLING - it is the panel's - so none
    of the sibling rules could see it. Measured before the fix: 12px on three of
    those panels. This walk did not look at tab panels either, which is why it
    passed while they were wrong.
  * **Header wrapping** - a table that can scroll sideways has no reason to wrap
    a column label. "GitLab User ID" over an 80px column made the users table's
    header row 92px tall while the table was already wider than its viewport.

    GITPULSE_E2E_BASE_URL=http://127.0.0.1:8000 \
      python -m pytest tests/e2e/scenarios/test_tables_meet_the_block_above_them.py -q
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

_PAGES = (
    "/dashboard/",
    "/dashboard/admin/users",
    "/dashboard/admin/courses",
    "/dashboard/admin/system",
    "/dashboard/admin/events",
)

# Floors, so a walk that reached nothing cannot report a clean bill of health.
_MIN_TABLES_UNDER_A_HEADER = 2
_MIN_HEADER_CELLS = 12

_ROUNDING = """
() => {
  const out = [];
  document.querySelectorAll('.table-responsive, .table-scrollable').forEach((t) => {
    const b = t.getBoundingClientRect();
    if (!b.width || !b.height) return;
    // The three shapes where the block holding the table owns the top edge: a
    // card body the table runs FLUSH to, a disclosure panel under its summary,
    // and a TAB PANEL under its tab strip. A table inset by a padded body is a
    // different shape and keeps its own corners.
    const body = t.closest('.card-body');
    const flush = body && parseFloat(getComputedStyle(body).paddingTop) === 0;
    const details = t.closest('details');
    const panel = t.closest('[data-tab-panel]');
    const disclosed = details && details.querySelector('summary');
    // Every table is reported, so the walk can tell "reached nothing" from
    // "reached tables that are all inset" - since the card bodies took their
    // padding back, no table here runs flush, and that is a clean result too.
    const owned = !!(flush || disclosed || panel);
    const under = disclosed ? details : (panel || body || t.parentElement);
    const cs = getComputedStyle(t);
    out.push({
      owned,
      sel: t.tagName.toLowerCase() + '.' + String(t.className).trim().split(/\\s+/)[0],
      block: String(under.className).trim().split(/\\s+/).slice(0, 2).join('.') || under.tagName,
      topLeft: parseFloat(cs.borderTopLeftRadius) || 0,
      topRight: parseFloat(cs.borderTopRightRadius) || 0,
    });
  });
  return out;
}
"""

_HEADERS = """
() => {
  const out = [];
  document.querySelectorAll('.table-responsive .data-table:not(.tbl-fixed) th').forEach((th) => {
    const b = th.getBoundingClientRect();
    if (!b.width || !b.height || !th.innerText.trim()) return;
    const cs = getComputedStyle(th);
    const line = parseFloat(cs.lineHeight) || 20;
    const pad = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
    out.push({
      text: th.innerText.trim().slice(0, 24),
      whiteSpace: cs.whiteSpace,
      height: Math.round(b.height),
      oneLine: Math.round(line + pad + 2),
    });
  });
  return out;
}
"""


def _open_everything(page) -> None:
    """Disclosures shut and cards collapsed hide exactly the tables under a
    header, which are the ones this file is about."""
    page.evaluate("() => document.querySelectorAll('details').forEach((d) => { d.open = true; })")
    headers = page.locator(".card-header--interactive")
    for i in range(headers.count()):
        header = headers.nth(i)
        body = header.locator("xpath=following-sibling::*[contains(@class,'card-body')][1]")
        if body.count() and not body.first.is_visible():
            header.click()
    page.wait_for_timeout(400)


def test_a_table_under_a_header_does_not_round_its_own_top(context_for, live_server: str) -> None:
    ctx = context_for("admin", 1440, 950)
    page = ctx.new_page()

    checked = 0
    bad: list[str] = []
    for path in _PAGES:
        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            continue
        page.wait_for_timeout(1200)
        _open_everything(page)
        for row in page.evaluate(_ROUNDING):
            checked += 1
            if row["owned"] and (row["topLeft"] or row["topRight"]):
                bad.append(
                    f"{path} {row['sel']} inside {row['block']}: "
                    f"{row['topLeft']:.0f}/{row['topRight']:.0f}px of top corner"
                )

    assert checked >= _MIN_TABLES_UNDER_A_HEADER, (
        f"only {checked} tables were reached - the walk found nothing to check"
    )
    assert not bad, (
        "a table rounds its top under a block that already owns that edge:\n" + "\n".join(bad)
    )


def test_a_scrolling_table_does_not_wrap_its_headers(context_for, live_server: str) -> None:
    ctx = context_for("admin", 1440, 950)
    page = ctx.new_page()

    checked = 0
    wrapped: list[str] = []
    for path in _PAGES:
        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            continue
        page.wait_for_timeout(1200)
        _open_everything(page)
        for row in page.evaluate(_HEADERS):
            checked += 1
            if row["whiteSpace"] != "nowrap" or row["height"] > row["oneLine"]:
                wrapped.append(
                    f'{path} "{row["text"]}": {row["whiteSpace"]}, '
                    f"{row['height']}px against {row['oneLine']}px for one line"
                )

    assert checked >= _MIN_HEADER_CELLS, (
        f"only {checked} header cells were reached - the walk found nothing to check"
    )
    assert not wrapped, "a column label wraps in a table that can scroll instead:\n" + "\n".join(
        wrapped
    )


# Longer than anything the catalogue holds, which is the point: the dev data has
# no outlier, so the cap has to be shown a value that would be one.
_OUTLIER = "Bartholomew Maximilian Konstantinopolsky-Vysokoblagorodny III of Kosice"


def test_one_long_value_does_not_take_the_column_with_it(context_for, live_server: str) -> None:
    """Auto layout sized a column to its widest cell, so one unbounded value made
    every other row scroll past a gap only one row needed. The users table is
    fixed-layout now, so no value can widen its column - and what a column does
    with a long value depends on whose it is (pages/admin.css, 2026-10-16): a
    PERSON's name wraps inside its column, because it is what the reader is there
    to read; a service account's machine name is cut, its tooltip holding the
    whole of it."""
    ctx = context_for("admin", 1440, 950)
    page = ctx.new_page()
    page.goto(live_server + "/dashboard/admin/users", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    seen = page.evaluate(
        """
        (value) => {
          const table = document.querySelector('#usersTable');
          const person = document.querySelector(
            '#usersTable tr:not(.user-row--bot) td.col-fullname .users-cell-value');
          if (!table || !person) return null;
          const was = table.getBoundingClientRect().width;
          const colWas = person.closest('td').getBoundingClientRect().width;
          person.textContent = value;
          const out = {
            grewBy: table.getBoundingClientRect().width - was,
            colGrewBy: person.closest('td').getBoundingClientRect().width - colWas,
            personCut: person.scrollWidth > person.clientWidth + 1,
            personLines: Math.round(person.getBoundingClientRect().height /
              (parseFloat(getComputedStyle(person).lineHeight) || 20)),
          };
          return out;
        }
        """,
        _OUTLIER,
    )
    assert seen, "the users table has no person's full-name cell to measure"
    assert abs(seen["colGrewBy"]) <= 1, (
        f"a {len(_OUTLIER)}-character name widened its column by {seen['colGrewBy']:.0f}px"
    )
    assert abs(seen["grewBy"]) <= 1, (
        f"a {len(_OUTLIER)}-character name widened the table by {seen['grewBy']:.0f}px"
    )
    assert not seen["personCut"], "a person's name was cut instead of wrapping in its column"
    assert seen["personLines"] >= 2, "the long name neither wrapped nor was cut"

    # The service accounts are a table tab of their own; a reader opens it.
    tab = page.query_selector('[data-value="bot"]')
    if tab and tab.is_visible():
        tab.click()
        page.wait_for_timeout(400)
    bot = page.evaluate(
        """
        (value) => {
          const cell = [...document.querySelectorAll(
            '#usersTable tr.user-row--bot td.col-fullname .users-cell-value')]
            .find((c) => c.offsetParent);
          if (!cell) return null;
          cell.textContent = value;
          const cs = getComputedStyle(cell);
          return {cut: cell.scrollWidth > cell.clientWidth + 1, textOverflow: cs.textOverflow,
                  tooltip: !!cell.getAttribute('data-tippy-content')};
        }
        """,
        _OUTLIER,
    )
    if bot:
        assert bot["cut"], "a service account's long name is not cut"
        assert bot["textOverflow"] == "ellipsis", "the cut value has no ellipsis"
        assert bot["tooltip"], "the cut value has no tooltip to read the rest by"

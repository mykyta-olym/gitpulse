"""A dense table may scroll sideways. A single column may not be unreadable.

The table design deliberately lets dense tables outgrow their container and
scroll - that is what `.table-scrollable` is for, and its own comment says
long text cells are "capped per-table with an ellipsis". What it cannot
tolerate is a column WIDER THAN THE CONTAINER ITSELF: at that point the reader
cannot see one cell in full at any scroll position, and every other column is
pushed out of the viewport behind it.

Feature Flags had exactly that. Its Description column is prose, so with the
single-line rule it took whatever its longest sentence needed - 2 531px - and
carried the table to 3 205px inside a 1 092px card. Reading one description
meant scrolling two thousand pixels sideways, and nothing else on the row was
visible while you did.
"""

from __future__ import annotations

import json
import os

import pytest

from tests.e2e.scenarios.conftest import ROLES

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_PAGES = (
    "/dashboard/",
    "/dashboard/admin/system",
    "/dashboard/admin/users",
    "/dashboard/admin/courses",
    "/dashboard/admin/events",
    "/dashboard/preferences",
)

_MEASURE = r"""
() => {
  const out = [];
  document.querySelectorAll('table').forEach((t) => {
    const ths = [...t.querySelectorAll('thead th')];
    if (!ths.length) return;
    // The box the table is laid out in: its nearest scroll wrapper, else its
    // offset parent. That is the width a reader actually has.
    const wrap = t.closest('.table-responsive, .table-scroll, .card-body') || t.parentElement;
    const avail = wrap ? wrap.clientWidth : 0;
    if (avail < 50) return;
    ths.forEach((th) => {
      const w = Math.round(th.getBoundingClientRect().width);
      if (w > avail) {
        out.push({
          table: t.id || (t.className || '').toString().split(/\s+/)[0] || 'table',
          column: (th.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          columnWidth: w, available: Math.round(avail),
        });
      }
    });
  });
  return out;
}
"""


@pytest.mark.parametrize("role", ROLES)
def test_no_single_column_is_wider_than_the_space_it_has(
    context_for, live_server: str, role: str
) -> None:
    ctx = context_for(role, 1440, 900)
    page = ctx.new_page()
    problems: list[str] = []
    reached = 0

    for path in _PAGES:
        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            continue
        reached += 1
        page.wait_for_timeout(1200)
        for finding in page.evaluate(_MEASURE):
            problems.append(f"{path} {json.dumps(finding, ensure_ascii=False)}")

    ctx.close()
    assert reached, f"a {role} reached none of the pages - this walk proves nothing"
    assert not problems, (
        "a column is wider than the space the reader has, so it can never be "
        "seen in full:\n  " + "\n  ".join(dict.fromkeys(problems))
    )

"""A filter sits over the thing it filters, on the same edges.

The users toolbar - a search box and the role tab strip - lives in the card
HEADER, and the table it filters lives in the card BODY. The two carry
different horizontal padding, 12px against 24px, so the controls ran 12px
wider on each side than the rows underneath them: measured 273..1389 against
the table's 285..1377. Against the card edge that reads as no margin at all,
which is how it was reported - "the search and the filter have no space, they
are right up against the table".

Nothing in the suite could see it. The page walk checks a page holds together,
the rhythm walk compares pages to each other, and neither compares two
elements on ONE page to each other.
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

#: A control may sit within a pixel of its table - rounding, not misalignment.
_TOLERANCE_PX = 1

_EDGES = """
() => {
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left: Math.round(r.left), right: Math.round(r.right)};
  };
  const table = document.querySelector('#usersTable');
  const wrap = table && table.closest('.table-responsive, .table-scroll');
  const search = document.querySelector('.table-controls .search-box');
  const pills = [...document.querySelectorAll('.users-role-filter .tab-btn')];
  return {
    table: box(wrap),
    search: box(search),
    lastPill: box(pills[pills.length - 1]),
  };
}
"""


def test_the_users_filter_sits_on_the_table_s_edges(context_for, live_server: str) -> None:
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    response = page.goto(live_server + "/dashboard/admin/users", wait_until="domcontentloaded")
    assert response is not None
    assert response.status < 400, f"users page answered {response.status}"
    page.wait_for_timeout(1800)

    edges = page.evaluate(_EDGES)
    ctx.close()

    assert edges["table"], "no users table to align against"
    assert edges["search"], "no search box on the users page"
    assert edges["lastPill"], "no role filter on the users page"

    left_gap = edges["search"]["left"] - edges["table"]["left"]
    right_gap = edges["table"]["right"] - edges["lastPill"]["right"]
    assert abs(left_gap) <= _TOLERANCE_PX, (
        f"the search box starts {left_gap:+d}px from the table's left edge "
        f"(search {edges['search']}, table {edges['table']})"
    )
    assert abs(right_gap) <= _TOLERANCE_PX, (
        f"the last role pill ends {-right_gap:+d}px from the table's right edge "
        f"(pill {edges['lastPill']}, table {edges['table']})"
    )

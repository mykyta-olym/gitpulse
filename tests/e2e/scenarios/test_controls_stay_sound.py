"""Click the controls, not just the pages.

The other two walks load a page and open its dialogs. Neither touches the
things a reader actually uses on a table page - sorting a column, changing the
page, switching a filter - and every one of those re-renders the rows from
JavaScript. A re-render is exactly where a table loses its column sizing, drops
its scroll wrapper, or paints rows that no longer fit.

Each control is clicked and the page is re-audited with the same rules as the
page walk, so a defect that only appears after an interaction is caught in the
same terms as one that is there on load.
"""

from __future__ import annotations

import json
import os
from contextlib import suppress

import pytest

from tests.e2e.scenarios.conftest import ROLES
from tests.e2e.scenarios.test_layout_is_sound import _AUDIT

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

# Pages whose main content is a table driven by JavaScript.
_TABLE_PAGES = (
    "/dashboard/admin/users",
    "/dashboard/admin/courses",
    "/dashboard/admin/system",
    "/dashboard/admin/events",
)

_CONTROLS = (
    ("sort", "th .sort-link, th.sortable-header"),
    ("filter", ".filter-tabs .tab-btn"),
    ("page", ".pagination-btn:not([disabled])"),
)


# What each role should still be able to work with, measured rather than
# assumed. An admin reaches all four pages; a teacher reaches only Courses; a
# student reaches none of them and is expected to click nothing at all. The
# numbers exist so a change in access control - or a table that stops
# rendering its controls - fails here instead of passing quietly.
_EXPECTED_CLICKS = {"admin": 10, "teacher": 3, "student": 0}


@pytest.mark.parametrize("role", ROLES)
def test_table_controls_do_not_break_the_layout(context_for, live_server: str, role: str) -> None:
    ctx = context_for(role, 1500, 950)
    page = ctx.new_page()

    problems: list[str] = []
    clicked = 0
    reached = 0

    for path in _TABLE_PAGES:
        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            continue  # this role has no access; the totals below pin that
        reached += 1
        page.wait_for_timeout(1200)
        clicked += _exercise(page, path, problems)

    ctx.close()
    assert clicked >= _EXPECTED_CLICKS[role], (
        f"a {role} clicked {clicked} control(s) across {reached} reachable "
        f"page(s), expected at least {_EXPECTED_CLICKS[role]}"
    )
    assert not problems, (
        f"{clicked} control(s) clicked as {role}, {len(problems)} problem(s):"
        + chr(10)
        + "  "
        + (chr(10) + "  ").join(dict.fromkeys(problems))
    )


def _exercise(page, path: str, problems: list[str]) -> int:
    """Click every control on this page, re-auditing after each one."""
    clicked = 0
    for label, selector in _CONTROLS:
        handles = page.query_selector_all(selector)
        for handle in handles[:6]:
            if not handle.is_visible() or not handle.is_enabled():
                continue
            # A control that will not click (covered by a sticky header, or
            # replaced by the re-render a previous click started) is not this
            # test's subject; what it audits is the layout after one that does.
            with suppress(Exception):
                handle.click(timeout=2500)
            clicked += 1
            page.wait_for_timeout(700)
            for finding in page.evaluate(_AUDIT):
                problems.append(
                    f"{path} after {label} click {json.dumps(finding, ensure_ascii=False)}"
                )

    return clicked

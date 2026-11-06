"""People and service accounts are one table, not two.

They are the same entity with the same eight columns - both halves rendered
`users_table_head()`, so the colgroup, the headers and the `<td>` classes were
identical and a bot row differed from a person row by a badge and two tooltips.
Rendered twice, they needed two tab panels, two paginators and two partials,
and the search box and the sort headers reached only whichever was open.

So the split was a filter. It is one now: the pill row that already said
Admin / Teacher / Student says Service Accounts too.

Rendered here rather than grepped, because what matters is what the page comes
out as.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.main import templates


def _tabs(html: str) -> list[str]:
    """The tabs themselves - the strip around them carries `filter-tabs`."""
    return re.findall(r'class="tab-btn[^"]*"', html)


def _user(username: str, *, role: str = "student", bot: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"id-{username}",
        username=username,
        full_name=username.title(),
        email=f"{username}@student.university.edu",
        role=role,
        is_active=True,
        gitlab_user_id=1,
        created_at=None,
        is_bot=bot,
    )


def _render(*, bots: list[SimpleNamespace]) -> str:
    ctx: dict[str, Any] = {
        "users": [_user("ada"), _user("linus", role="teacher")],
        "bot_users": bots,
        "is_admin": True,
        "current_user": {"user": "someone-else"},
        "request": SimpleNamespace(query_params={}, state=SimpleNamespace(csp_nonce="")),
        "csp_nonce": "",
    }
    template = templates.env.get_template("partials/admin/_users_content.html")
    return template.render(**ctx)


@pytest.fixture(scope="module")
def with_bots() -> str:
    return _render(bots=[_user("project_12_bot", role="student", bot=True)])


@pytest.fixture(scope="module")
def without_bots() -> str:
    return _render(bots=[])


def test_one_card_one_table(with_bots: str) -> None:
    assert with_bots.count("users-management-card") == 1, "the page is two cards again"
    assert "<details" not in with_bots, "the bots are back in a collapsed panel"
    assert with_bots.count("<table") == 1, "the bots are back in a table of their own"
    assert "data-tab-panel" not in with_bots, "two tabs for one table"


def test_both_kinds_are_rows_of_it(with_bots: str) -> None:
    body = with_bots.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    assert 'data-bot="0"' in body
    assert 'data-bot="1"' in body
    assert "project_12_bot" in body
    assert "ada" in body
    assert body.count("<tr") == 3


def test_a_service_account_says_so_on_its_row(with_bots: str) -> None:
    """One table only works if the reader can tell the kinds apart in it."""
    rows = re.findall(r'<tr class="user-row.*?</tr>', with_bots, re.S)
    bot_row = next(r for r in rows if 'data-bot="1"' in r)
    person_row = next(r for r in rows if 'data-bot="0"' in r)
    assert "badge" in bot_row
    assert ">Bot<" in bot_row
    assert ">Bot<" not in person_row


def test_a_service_account_says_so_once(with_bots: str) -> None:
    """The Role column says Bot; a second badge beside the name only took 40px
    of a 150px column from the name."""
    rows = re.findall(r'<tr class="user-row.*?</tr>', with_bots, re.S)
    bot_row = next(r for r in rows if 'data-bot="1"' in r)
    assert bot_row.count(">Bot<") == 1


def test_the_view_that_replaced_the_tab(with_bots: str) -> None:
    assert 'data-value="bot"' in with_bots, "no way to see only the service accounts"
    assert len(_tabs(with_bots)) == 5


def test_no_such_view_when_there_are_no_service_accounts(without_bots: str) -> None:
    """A view that can only ever show nothing is noise."""
    assert 'data-value="bot"' not in without_bots
    assert len(_tabs(without_bots)) == 4
    assert without_bots.count("<table") == 1
    assert without_bots.count("users-management-card") == 1


def test_one_toolbar_over_the_one_table(with_bots: str) -> None:
    assert with_bots.count('id="userSearch"') == 1
    assert with_bots.count("users-role-filter") == 1
    assert with_bots.count("pagination-controls") == 1


def test_a_machine_name_cannot_set_the_width_of_a_column() -> None:
    """The cost of putting the service accounts in the people's table.

    A GitLab service account is named `project_12345_bot_1a2b3c4d5e6f7890` - 33
    characters, where a student login is 7 - and it carries that same string as
    its full name and inside its address. Auto layout sizes a column to its
    WIDEST cell, so the moment those rows joined the table, three columns grew
    by 147px, 93px and 67px: measured at 1490px of table inside a 1206px
    wrapper, against 1206px for the same table holding people alone. Status and
    Created fell off the right edge and the sticky Actions column painted over
    Role and Status.

    The cap goes on the bot ROWS, not on the columns - capping the columns made
    every student's address short to pay for a handful of machine names.
    """
    css = (
        Path(__file__).resolve().parents[2] / "src/app/templates/static/css/pages/admin.css"
    ).read_text(encoding="utf-8")
    assert "tr.user-row--bot .user-username" in css, (
        "nothing stops a service account name from setting the username column's width"
    )
    assert "tr.user-row--bot .users-cell-value" in css, (
        "a service account's full name and address still size their columns"
    )
    # No tighter ceiling on the address than the 42ch outlier cap: a 36ch one
    # cut ORDINARY 38-character student addresses on every page, and an
    # address is what a reader is here to read. The table scrolls inside its
    # wrapper when the sum does not fit (149px at 1366px, none at 1600px).
    assert "td.col-email .users-cell-value" not in css, (
        "a per-column cap on the address is back; it cut ordinary student emails"
    )
    # ...and the value asks its column for the width of its text: a block with
    # overflow hidden asks for none, so the column stayed at its hint and
    # clipped the address anyway.
    rule = css[css.index(".users-cell-value {") : css.index("}", css.index(".users-cell-value {"))]
    assert "display: inline-block" in rule


def test_a_bot_cap_never_outgrows_a_fixed_column() -> None:
    """Above 1180px the table is `table-layout: fixed`: the column sets the
    width, and the 20ch / 28ch caps were wider than the columns - a bot's full
    name ran 120px past its cell, over the address beside it, and the address
    under the Role badge. The caps belong to the auto-layout widths only."""
    css = (
        Path(__file__).resolve().parents[2] / "src/app/templates/static/css/pages/admin.css"
    ).read_text(encoding="utf-8")
    for selector in ("tr.user-row--bot .user-username {", "tr.user-row--bot .users-cell-value {"):
        at = css.index(selector)
        media = css.rfind("@media", 0, at)
        between = css[media:at]
        assert between.startswith("@media (max-width: 1180px)"), f"{selector}: fixed columns"
        assert between.count("{") - between.count("}") == 1, f"{selector}: outside the block"

"""The issues a member is on are one list, not two.

Authored and assigned were two tabs over the same table of the same entity with
the same five columns, differing in exactly one: "Assigned to" on the authored
tab, "Opened by" on the assigned tab - so each tab hid the half the other
showed, and "is this one mine to do, or mine to follow?" was a question about
which tab you were looking at.

Worse, they came from two queries that could both return the same issue: one
the member opened AND was assigned appeared in both tabs, in two rows carrying
the same `id="issue-N"` - which is what the in-page issue<->MR links resolve
against, so the anchor could land on either copy.

Rendered here rather than grepped, because what matters is what the page comes
out as.
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any

import jinja2
import pytest

from app.main import templates


class _Blank(jinja2.Undefined):
    """Everything the rest of this long page needs and this test does not."""

    def __getattr__(self, name: str) -> _Blank:
        return self

    def __getitem__(self, name: Any) -> _Blank:
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> _Blank:
        return self

    def __iter__(self) -> Any:
        return iter(())

    def __str__(self) -> str:
        return ""

    def __html__(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return False

    def __len__(self) -> int:
        return 0

    def __gt__(self, other: Any) -> bool:
        return False

    def __lt__(self, other: Any) -> bool:
        return False

    def __ge__(self, other: Any) -> bool:
        return False

    def __le__(self, other: Any) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return False

    def __ne__(self, other: Any) -> bool:
        return True

    def __hash__(self) -> int:
        return 0


def _issue(iid: int, author: str, assignee: str, *, me: str = "Ada") -> dict[str, Any]:
    return {
        "issue": SimpleNamespace(
            gitlab_iid=iid, title=f"Issue {iid}", state="opened", updated_at=None
        ),
        "project_path": "grp/proj",
        "author_name": author,
        "author_username": author,
        "author_is_teacher": False,
        "assignee_name": assignee,
        "assignee_username": assignee,
        "assignee_is_teacher": True,
        "is_author": author == me,
        "is_assignee": assignee == me,
    }


@pytest.fixture(scope="module")
def card() -> str:
    """The issues card, with one issue of each kind - theirs, someone else's,
    and the one that used to be listed twice."""
    env = templates.env.overlay(undefined=_Blank)
    html = env.get_template("partials/student/_detail_content.html").render(
        issues_involving=[
            _issue(1, "Ada", "Grace"),
            _issue(2, "Linus", "Ada"),
            _issue(3, "Ada", "Ada"),
        ],
        gitlab_url="https://gitlab.example",
        mr_iid_by_issue_iid={},
        local_time=lambda value: "-",
        is_own_profile=False,
        member_role_label="Student",
    )
    section = html[html.index('data-tour="student-issues"') :]
    return section.split("COMMIT HISTORY", 1)[0]


def test_it_is_one_table(card: str) -> None:
    assert card.count("<table") == 1, "the two tabs are back"
    assert "data-tab-panel" not in card


def test_the_row_names_both_sides(card: str) -> None:
    """Neither tab could show who opened it AND who has it."""
    headers = [
        re.sub(r"<[^>]+>|\s+", " ", h).strip()
        for h in re.findall(r"<th[^>]*>(.*?)</th>", card, re.S)
    ]
    assert len(headers) == 6, headers
    body = card.split("<tbody", 1)[1]
    first_row = body.split("<tr", 2)[1]
    assert "Ada" in first_row, "the author is not on the row"
    assert "Grace" in first_row, "the assignee is not on the row"


def test_an_issue_appears_once_however_many_sides_of_it_you_are_on(card: str) -> None:
    ids = re.findall(r'id="(issue-\d+)"', card)
    assert ids == ["issue-1", "issue-2", "issue-3"]
    assert len(ids) == len(set(ids)), (
        "an issue the member both opened and was assigned is listed twice, under "
        "the same id - which is what the in-page issue<->MR anchors resolve against"
    )


def test_the_filter_that_replaced_the_tabs(card: str) -> None:
    assert re.findall(r'data-value="(\w+)"', card) == ["all", "author", "assignee"]
    sides = re.findall(r'data-side="([^"]*)"', card)
    assert sides == ["author", "assignee", "author assignee"], (
        "a row has to say which side(s) of the issue the member is on, or the "
        "pills have nothing to filter by"
    )


def test_one_query_feeds_it() -> None:
    """Two statements over one table, differing only in which side they filtered
    on, is the split this removed."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "src/app/api/dashboard/students/profile.py"
    ).read_text(encoding="utf-8")
    assert "async def _issues_involving(" in source
    assert "issues_authored_stmt" not in source
    assert "issues_assigned_stmt" not in source
    assert '"is_author"' in source
    assert '"is_assignee"' in source

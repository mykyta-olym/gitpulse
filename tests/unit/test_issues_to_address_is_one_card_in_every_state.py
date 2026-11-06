"""One card, whatever there is to say in it.

"Issues to Address" has five states - a template fork, an empty repository, no
scored members, everything passing, and the real chart - and it used to carry a
copy of the card in each of them: five `{% call card %}` blocks repeating the
same title and the same `id='projectBottlenecksCard'`. That id is the handle the
project page's live-data refresh swaps, so the element it replaces was defined
in five places and could drift in four of them without anyone noticing.

The branch picks what to say now; the card is written once.

Rendered here in every state, because "one card" is a claim about the output.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.main import templates

TEMPLATE = "partials/project/_issues_to_address.html"


def _student(name: str) -> SimpleNamespace:
    return SimpleNamespace(id=f"id-{name}", full_name=name.title(), gitlab_username=name)


def _snapshot(**checks: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(checks_detail=checks)


def _render(**ctx: Any) -> str:
    base: dict[str, Any] = {
        "scored_students": [],
        "snapshots": {},
        "memberships": {},
        "user_roles": {},
        "csp_nonce": "",
        "request": SimpleNamespace(query_params={}, state=SimpleNamespace(csp_nonce="")),
    }
    base.update(ctx)
    return templates.env.get_template(TEMPLATE).render(**base)


#: Every state the panel can be in. The second element is a label, not an
#: assertion: "chart" marks the one state that renders the real panel instead of
#: an empty one. The copy itself is translated - these tests run in the default
#: locale - so the messages are compared to each other rather than to strings.
STATES: dict[str, tuple[dict[str, Any], str]] = {
    "template fork": ({"template_fork": True}, "empty-commit"),
    "empty repository": ({"repo_empty": True}, "empty-issues"),
    "no scored members": ({}, "empty-user"),
    "everything passing": (
        {
            "scored_students": [_student("ada")],
            "snapshots": {"id-ada": _snapshot(has_mr={"pass": True, "expected": True})},
        },
        "empty-todos-all-done",
    ),
    "issues to show": (
        {
            "scored_students": [_student("ada")],
            "snapshots": {
                "id-ada": _snapshot(
                    has_mr={
                        "pass": False,
                        "expected": True,
                        "name": "Opened a merge request",
                        "weight": 0.3,
                        "detail": "none found",
                    }
                )
            },
        },
        "chart",
    ),
}


@pytest.mark.parametrize("state", list(STATES))
def test_exactly_one_card_carries_the_panel(state: str) -> None:
    ctx, _ = STATES[state]
    html = _render(**ctx)
    assert html.count("projectBottlenecksCard") == 1, (
        f"the {state} state renders the card {html.count('projectBottlenecksCard')} times - "
        "the live-data refresh replaces one element, not several"
    )
    assert html.count("card-header") == 1, f"the {state} state grew a second card"


def test_each_state_still_says_its_own_thing() -> None:
    """Sharing one card must not cost the four blank states their own wording -
    that wording is the only thing telling a teacher WHY the panel is blank.

    Compared to each other rather than to fixed strings: the copy is translated
    and these tests run in the default locale, so what can be asserted is that
    four different situations still produce four different messages."""
    titles = {}
    for state, (ctx, marker) in STATES.items():
        if marker == "chart":
            continue
        html = _render(**ctx)
        title = html.split('class="empty-state-title">', 1)[1].split("<", 1)[0].strip()
        assert title, f"the {state} state renders an empty state with no title"
        titles[state] = title
    assert len(set(titles.values())) == len(titles), f"two states now share one message: {titles}"


def test_the_state_with_issues_renders_the_chart_not_an_empty_state() -> None:
    ctx, _ = STATES["issues to show"]
    html = _render(**ctx)
    assert "issues-chart-wrap" in html
    assert "empty-state-title" not in html


def test_the_title_is_written_once() -> None:
    """Five copies of `{% set _ct %}` is how the four empty states each ended up
    with their own title to keep in step."""
    src = (templates.env.loader.get_source(templates.env, TEMPLATE))[0]  # type: ignore[union-attr]
    assert src.count("{% set _ct %}") == 1, "the card title is being repeated per branch again"
    assert src.count("{% call card(") == 2, (
        "there should be exactly two card call sites: the empty one and the real one"
    )

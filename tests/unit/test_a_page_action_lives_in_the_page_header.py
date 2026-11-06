"""Page-header actions keep scoped permissions on fresh and cached renders.

Course/group pages do not compute totals for removed cards; sync status still
uses the shared contributor count.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SHELL = REPO / "src/app/templates/course_detail.html"
FRAGMENT = REPO / "src/app/templates/partials/course/_detail_content.html"
HANDLER = REPO / "src/app/api/dashboard/courses/routes.py"


@pytest.fixture(scope="module")
def shell() -> str:
    return SHELL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fragment() -> str:
    return FRAGMENT.read_text(encoding="utf-8")


class TestTheActionsMovedToTheHeader:
    @pytest.mark.parametrize(
        "action",
        ["addTeamModal", "importGitlabCourseModal", "triggerSyncAll", "runChecksModal"],
    )
    def test_the_header_carries_it(self, shell: str, action: str) -> None:
        header = shell.split("{% call page_header(", 1)[1].split("{% endcall %}", 1)[0]
        assert action in header, f"{action} is not among the page's own actions any more"

    def test_the_loose_bar_is_gone(self, fragment: str) -> None:
        assert "course-actions-bar" not in fragment, (
            "the four buttons are back in a bar between the tabs and the card"
        )

    def test_the_tour_can_still_find_them(self, shell: str) -> None:
        """Each button anchors a step of the course tour by `data-tour`."""
        for anchor in ("add-group", "import-gitlab", "sync-all", "run-checks"):
            assert f"'tour': '{anchor}'" in shell, f"the tour anchor {anchor} was lost"

    def test_they_are_still_locked_while_a_process_runs(self, shell: str) -> None:
        """`process-lock-when` is what stops a second Sync All being fired over
        a running one; it has to survive the move."""
        header = shell.split("{% call page_header(", 1)[1].split("{% endcall %}", 1)[0]
        assert header.count("process-lock-when") >= 1
        assert "'process-lock-scope': 'course:' ~ course.id" in header


class TestTheShellIsToldWhoIsLooking:
    def test_both_render_paths_pass_the_permissions(self) -> None:
        """The cache-hit path and the freshly-rendered path both render the same
        shell; a `can_edit` missing from either one silently hides the actions."""
        src = HANDLER.read_text(encoding="utf-8")
        pattern = r'page_template="course_detail\.html",\s*\n(?:.*\n)*?\s*page_ctx=\{[^}]*\}'
        calls = re.findall(pattern, src)
        assert len(calls) == 2, f"expected two course-page renders, found {len(calls)}"
        for call in calls:
            assert '"can_edit"' in call
            assert '"course_role"' in call


class TestTheDeadQueryIsGone:
    def test_the_course_page_no_longer_counts_contributors_it_never_shows(self) -> None:
        src = HANDLER.read_text(encoding="utf-8")
        detail = src.split("async def course_detail(", 1)[1].split("\n@router", 1)[0]
        assert "total_distinct_contributors(" not in detail, (
            "the course page is asking the database for a number no template renders"
        )
        assert "total_distinct_students" not in detail

    def test_the_helper_itself_stays_for_its_real_callers(self) -> None:
        teams = (REPO / "src/app/api/dashboard/teams/routes.py").read_text(encoding="utf-8")
        assert "total_distinct_contributors(" not in teams
        for path in ("sync.py", "sync_stream.py"):
            sync = (REPO / "src/app/api" / path).read_text(encoding="utf-8")
            assert "await total_distinct_contributors(" in sync, f"{path} lost its count"

    def test_the_refresh_counts_contributors_as_the_page_does(self) -> None:
        """The refresh counted each group's contributors over all time, the page
        over the semester - so the first refresh swapped every group's number
        for a larger one. Both ask the one helper now."""
        src = HANDLER.read_text(encoding="utf-8")
        detail = src.split("async def course_detail(", 1)[1].split("\n@router", 1)[0]
        live = src.split("async def course_live_data(", 1)[1].split("\n@router", 1)[0]
        for body in (detail, live):
            assert "await group_contributors(db, course, " in body
        assert "team_contributor_counts(" not in live
        assert "total_distinct_contributors(" not in live

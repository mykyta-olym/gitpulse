"""The Assistant page renders in each state a teacher meets it in.

Not connected: the steps to make a bot token, and a Connect button. Connected:
who the bot is and when its token expires. Archived: every control disabled,
each saying why. Its activity table follows the address on the first frame -
``?tool=conflict`` paints the conflict rows only, before any script runs - and
"Prepare exercise" is disabled with a reason until it can work.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from starlette.requests import Request

from app.api.dashboard._helpers import _templates
from app.i18n import get_template_i18n_context
from app.models.assistant import TOOLS, AssistantTask, CourseAssistant
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.services.assistant import account

COURSE_ID = uuid.uuid4()
STATIC_JS = Path(__file__).parents[2] / "src/app/templates/static/js"


def _request(query: str = "") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/dashboard/courses/{COURSE_ID}/assistant",
            "raw_path": f"/dashboard/courses/{COURSE_ID}/assistant".encode(),
            "query_string": query.encode(),
            "headers": [],
            "root_path": "",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 1),
            "app": None,
        }
    )


def _course(active: bool = True) -> Course:
    course = Course(
        id=COURSE_ID, code="ZSI", name="Zaklady", academic_year="2025/2026", semester="summer"
    )
    course.is_active = active
    course.description = ""
    course.settings = CourseSettings(course_id=COURSE_ID)
    return course


def _connected() -> CourseAssistant:
    return CourseAssistant(
        course_id=COURSE_ID,
        bot_token="enc:v1:x",
        bot_user_id=5,
        bot_username="group_7_bot",
        bot_name="ZSI assistant",
        connected_at=datetime.now(UTC),
        connected_by="teacher",
        token_expires_at=datetime.now(UTC) + timedelta(days=3),
        push_review_enabled=True,
        min_commit_title_length=10,
        conflict_enabled=True,
        conflict_file_path="README.md",
        mr_review_enabled=True,
        mr_bot_merges=False,
        exercise_file_template="ulohy/{username}.txt",
        comment_language="sk",
        last_exercise_run={
            "at": "2026-10-19T10:00:00+00:00",
            "by": "teacher",
            "projects": [
                {"path": "zsi/team-a", "created": 3, "skipped": 0},
                {"path": "zsi/team-b", "created": 0, "skipped": 0, "error": "403 Forbidden"},
            ],
        },
    )


def _row(tool: str, state: str, **fields: Any) -> dict[str, Any]:
    task = AssistantTask(
        id=uuid.uuid4(),
        tool=tool,
        key=str(uuid.uuid4()),
        state=state,
        student_username="jana",
        updated_at=datetime.now(UTC),
        history=[],
        detail={},
        **fields,
    )
    return {
        "task": task,
        "student_name": "Jana Nova",
        "student_gitlab_id": 77,
        "avatar_url": "",
        "team": "Team A",
        "project_path": "zsi/team-a",
        "issue_url": "https://g/i" if task.issue_iid else None,
        "mr_url": "https://g/m" if task.mr_iid else None,
        "commit_url": "https://g/c" if task.commit_sha else None,
        "last_action": "error" if state == "failed" else "commented",
        "last_note": "403 Forbidden" if state == "failed" else "",
        "last_url": None,
    }


ACTIVITY = [
    _row("push_review", "needs_work", branch="main", commit_sha="a" * 40),
    _row("conflict", "planted", branch="work", commit_sha="b" * 40, file_path="README.md"),
    _row("mr_review", "failed", issue_iid=4, mr_iid=2, file_path="ulohy/jana.txt"),
]


def _render(
    assistant: CourseAssistant | None,
    *,
    active: bool = True,
    query: str = "",
    activity=ACTIVITY,
    has_webhook: bool = True,
    webhook_silent: bool = False,
    branch_rule: str = "",
    required_sections: tuple[str, ...] = (),
) -> str:
    request = _request(query)
    context: dict[str, Any] = {
        "request": request,
        "course": _course(active),
        "course_role": "owner",
        "assistant": assistant,
        "can_act": assistant is not None and assistant.can_act(datetime.now(UTC)),
        "branch_rule": branch_rule,
        "required_sections": required_sections,
        "has_webhook": has_webhook,
        "webhook_silent": webhook_silent,
        "languages": [("sk", "Slovenčina"), ("en", "English")],
        "problems": account.problems(assistant),
        "exercise_run": account.last_exercise_run(assistant),
        "tools": account.tools_of(assistant),
        "tool_names": TOOLS,
        "projects": [{"id": str(uuid.uuid4()), "path": "zsi/team-a", "team": "Team A"}],
        "activity": activity,
        "activity_limit": account.ACTIVITY_LIMIT,
        "csrf_token": "test-csrf",
        "csp_nonce": "test-nonce",
        "is_admin": False,
        "is_teacher": True,
        "can_edit": True,
        **get_template_i18n_context(request),
        "feature_classroom_assistant": True,
    }
    return _templates(request).env.get_template("course_assistant.html").render(**context)


def _button(html: str, element_id: str) -> str:
    match = re.search(rf'<button[^>]*id="{element_id}"[^>]*>', html)
    assert match, f"#{element_id} is not on the page"
    return match.group(0)


def _reason(html: str, element_id: str) -> str | None:
    """The reason a disabled button gives: its `.gl-tip-wrap`'s tooltip (a
    disabled control receives no hover, so the wrapper carries it)."""
    match = re.search(
        rf'<span class="gl-tip-wrap" data-tippy-content="([^"]+)">\s*<button[^>]*id="{element_id}"',
        html,
    )
    return match.group(1) if match else None


def test_not_connected_shows_how_to_make_a_bot() -> None:
    html = _render(None, activity=[])
    assert 'id="btnConnectBot"' in html
    assert 'class="setup-steps"' in html
    assert 'id="btnDisconnectBot"' not in html
    assert "disabled" in _button(html, "btnPrepareExercise")
    assert _reason(html, "btnPrepareExercise") == "Najprv pripojte bot účet."
    assert 'id="assistantExerciseModal"' not in html
    assert 'id="assistantActivityTable"' in html
    assert 'class="table-empty-row"' in html
    assert 'id="paginationControls"' in html
    # An empty panel shows the small state every empty list shows (72 px, one
    # line), not the page-sized one with a heading.
    assert 'class="table-empty-state"' in html
    assert 'class="empty-state' not in html


def test_connected_shows_the_bot_and_its_expiry() -> None:
    html = _render(_connected())
    assert "@group_7_bot" in html
    assert 'id="btnDisconnectBot"' in html
    assert 'id="btnReplaceToken"' in html
    assert "badge-warning" in html  # the token expires in three days
    assert "zsi/team-b" in html
    assert "403 Forbidden" in html
    assert "disabled" not in _button(html, "btnPrepareExercise")
    assert 'id="assistantExerciseModal"' in html


def test_the_tab_is_in_the_course_navigation() -> None:
    html = _render(_connected())
    assert f'href="/dashboard/courses/{COURSE_ID}/assistant"' in html
    assert 'aria-current="page"' in html


@pytest.mark.parametrize(
    ("is_admin", "course_role", "shown"),
    [
        (False, "owner", True),
        (False, "teacher", True),
        (True, None, True),
        # A teacher who sees the course only as a team's mentor: the page
        # refuses them (_access._runs_course), so there is no tab to it.
        (False, None, False),
        (False, "student", False),
    ],
)
def test_the_tab_is_for_whoever_runs_the_course(
    is_admin: bool, course_role: str | None, shown: bool
) -> None:
    request = _request("")
    context: dict[str, Any] = {
        "course": _course(True),
        "active_tab": "overview",
        "can_edit": True,
        "is_admin": is_admin,
        "course_role": course_role,
        **get_template_i18n_context(request),
        "feature_classroom_assistant": True,
    }
    nav = _templates(request).env.get_template("partials/course/_course_nav.html")
    html = nav.render(**context)
    assert (f'href="/dashboard/courses/{COURSE_ID}/assistant"' in html) is shown


def test_who_merges_is_the_teachers_choice() -> None:
    html = _render(_connected())
    box = re.search(r'<input[^>]*name="mr_bot_merges"[^>]*>', html)
    assert box, "the merge choice is not on the page"
    assert "checked" not in box.group(0), "by default the student merges"
    assert "R10" in html


def test_the_teacher_is_told_the_exercise_counts_in_grading() -> None:
    """Its issue, branch and merge request are ordinary work that R01, R02,
    R04, R05 and R11 count, so where it is prepared matters."""
    html = _render(_connected())
    assert "sa v kontrolách R01 až R13 počítajú ako každé iné" in html


def test_the_save_bar_is_the_shared_one_and_starts_disabled() -> None:
    html = _render(_connected())
    assert '<div class="settings-sticky-footer">' in html
    assert "disabled" in _button(html, "btnSaveAssistantTools")
    # The same pair as the course Settings bar: save, or go back to the course.
    cancel = re.search(r'<a[^>]*id="btnCancelAssistantTools"[^>]*>', html)
    assert cancel, "the save bar has no Cancel"
    assert f'href="/dashboard/courses/{COURSE_ID}"' in cancel.group(0)


def test_the_tour_can_find_every_step() -> None:
    """Like every other course tab, the page has its tour, and each step's
    element is on the page."""
    tours = Path(__file__).parents[2] / "src/app/templates/static/js/_parts/tours"
    engine = (tours / "00-engine.js").read_text(encoding="utf-8")
    assert r"\/assistant\/?$/.test(p)) return 'course_assistant'" in engine
    tour = (tours / "20-courses.js").read_text(encoding="utf-8")
    assert "pages: ['course_assistant']" in tour
    html = _render(_connected())
    for anchor in ("assistant-bot", "assistant-tools", "assistant-exercise", "assistant-activity"):
        assert f'[data-tour~="{anchor}"]' in tour
        assert re.search(rf'data-tour="[^"]*\b{anchor}\b', html), anchor


def test_an_archived_course_disables_every_control_with_a_reason() -> None:
    html = _render(_connected(), active=False)
    for element_id in ("btnReplaceToken", "btnDisconnectBot", "btnPrepareExercise"):
        assert "disabled" in _button(html, element_id)
        assert (_reason(html, element_id) or "").startswith("Tento kurz je archivovaný")
    assert 'id="assistantTokenForm"' not in html
    assert re.search(r'<input[^>]*name="conflict_file_path"[^>]*disabled', html)


def test_every_row_is_rendered_with_its_state() -> None:
    html = _render(_connected())
    assert html.count('class="assistant-row') == 3
    assert "badge-danger" in html  # the refused one
    assert "403 Forbidden" in html


def test_the_group_has_a_column_of_its_own() -> None:
    """Not squeezed under the username, where it wrapped onto a third line."""
    html = _render(_connected())
    assert 'data-sort-key="team"' in html
    assert html.count('<td class="col-assistant-team" data-sort-value="team a">Team A</td>') == 3
    assert "@jana · " not in html


def test_the_activity_card_refreshes_like_every_live_card() -> None:
    """A Refresh in its header, as on Job History and Webhooks, and the
    address its redraw comes from."""
    html = _render(_connected())
    assert 'id="btnRefreshAssistantActivity"' in html
    assert f'data-refresh-url="/dashboard/courses/{COURSE_ID}/assistant/activity"' in html
    script = (STATIC_JS / "pages/course-assistant.js").read_text(encoding="utf-8")
    assert "GP.refreshRegion({" in script
    assert "d.event === 'assistant_activity'" in script
    # Only the body is redrawn: the header's Refresh stays the same element,
    # so it shows working -> "Done" -> back, as Job History's does.
    assert ".querySelector('#assistantActivityCard > .card-body')" in script
    # A save says "Done" on its button before the reload, as Settings' does:
    # the toast is raised on this page, not only handed to the next one.
    assert "GP.flashToast" not in script
    assert "GP.showToast(message, 'success');" in script


def test_the_address_picks_the_view_on_the_first_frame() -> None:
    html = _render(_connected(), query="tool=conflict")
    rows = re.findall(r'<tr class="assistant-row([^"]*)"[^>]*data-tool="([a-z_]+)"', html)
    hidden = {tool for cls, tool in rows if "d-none" in cls}
    shown = {tool for cls, tool in rows if "d-none" not in cls}
    assert shown == {"conflict"}
    assert hidden == {"push_review", "mr_review"}


def test_an_unknown_view_falls_back_to_all() -> None:
    html = _render(_connected(), query="tool=nonsense")
    assert "d-none" not in "".join(re.findall(r'<tr class="assistant-row[^"]*"', html))


def _startup_warning(html: str) -> Any:
    found = re.search(r'<script[^>]*id="gp-page-config"[^>]*>(.*?)</script>', html, re.DOTALL)
    assert found, "the page has no page config"
    return json.loads(found.group(1)).get("startupWarning")


class TestWhatStopsTheAssistantIsSaidFirst:
    def test_no_webhook_is_the_events_pages_toast(self) -> None:
        """Said as the Events page says it: a warning the page raises once
        when it opens, not a block in the page."""
        html = _render(_connected(), has_webhook=False)
        warning = _startup_warning(html)
        assert warning["message"].startswith("Webhooky nie sú nakonfigurované. ")
        assert "Nastavenia, Webhooky" in warning["message"]
        assert 'class="alert ' not in html
        script = (STATIC_JS / "pages/course-assistant.js").read_text(encoding="utf-8")
        assert "GP.showToast(warning.message, 'warning'" in script
        assert "{ once: true }" in script

    def test_an_archived_course_raises_no_webhook_toast(self) -> None:
        assert _startup_warning(_render(_connected(), has_webhook=False, active=False)) is None

    def test_a_course_with_a_webhook_raises_none(self) -> None:
        assert _startup_warning(_render(_connected())) is None

    def test_a_webhook_that_went_silent_is_the_events_pages_toast_too(self) -> None:
        """The Events page's second case: a webhook that has received nothing
        for 48 hours - the assistant then hears nothing either."""
        warning = _startup_warning(_render(_connected(), webhook_silent=True))
        assert warning["message"].startswith("Webhook kurzu nedostal z GitLabu za 48 hodín")
        assert "jeho tajomstvo" in warning["message"]
        assert _startup_warning(_render(_connected(), webhook_silent=True, active=False)) is None

    def test_tools_on_without_a_bot(self) -> None:
        assistant = CourseAssistant(course_id=COURSE_ID, push_review_enabled=True)
        assert "Nie je pripojený žiadny bot" in _render(assistant, activity=[])

    def test_a_token_gitlab_refused(self) -> None:
        assistant = _connected()
        assistant.token_rejected_at = datetime.now(UTC)
        html = _render(assistant)
        assert "GitLab už neprijíma token bota" in html
        assert "disabled" in _button(html, "btnPrepareExercise")
        assert _reason(html, "btnPrepareExercise") == "Token bota nefunguje. Najprv pripojte nový."

    def test_an_expired_token_is_said_once(self) -> None:
        assistant = _connected()
        assistant.token_expires_at = datetime.now(UTC) - timedelta(days=1)
        html = _render(assistant)
        assert "Platnosť tokenu bota vypršala" in html
        assert "Token vypršal" not in html, "the alert says it; no badge says it again"
        assert "Token expired" not in html

    def test_nothing_is_said_when_all_is_well(self) -> None:
        html = _render(_connected())
        assert 'class="alert ' not in html


class TestTheExerciseRun:
    def test_a_run_in_progress_holds_the_button(self) -> None:
        assistant = _connected()
        assistant.last_exercise_run = {
            "status": "running",
            "at": datetime.now(UTC).isoformat(),
            "by": "teacher",
            "projects": [],
        }
        html = _render(assistant)
        assert "Pripravuje sa" in html
        assert _reason(html, "btnPrepareExercise") == "Cvičenie sa práve pripravuje."
        # The top bar follows it; nobody is asked to reload the page.
        assert "Priebeh ukazuje horná lišta" in html

    def test_a_run_that_could_not_start_says_why(self) -> None:
        """The token went bad between the click and the run: said at once,
        not "Preparing" until the run goes stale."""
        assistant = _connected()
        assistant.last_exercise_run = {
            "at": datetime.now(UTC).isoformat(),
            "by": "teacher",
            "projects": [],
            "error": "The bot token does not work. Connect a new one first.",
        }
        html = _render(assistant)
        assert "Nepripravené" in html
        assert "Token bota nefunguje. Najprv pripojte nový." in html
        assert "Pripravuje sa" not in html

    def test_a_run_that_never_finished_says_so(self) -> None:
        assistant = _connected()
        assistant.last_exercise_run = {
            "status": "running",
            "at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "by": "teacher",
            "projects": [],
        }
        html = _render(assistant)
        assert "Nedokončené" in html
        assert _reason(html, "btnPrepareExercise") is None, "a dead run does not block a new one"

    def test_students_without_a_gitlab_account_are_counted(self) -> None:
        assistant = _connected()
        assert assistant.last_exercise_run is not None
        assistant.last_exercise_run["projects"][0]["unassignable"] = 2
        assert "bez účtu GitLab v GitPulse: 2" in _render(assistant)


def test_the_course_rules_the_review_adds_are_named() -> None:
    html = _render(_connected(), branch_rule=r"^issue-\d+", required_sections=("## Co", "## Preco"))
    assert r"<code>^issue-\d+</code> (R02)" in html
    assert "<code>## Co</code>, <code>## Preco</code> (R05)" in html


def test_the_comment_language_is_a_choice() -> None:
    html = _render(_connected())
    assert re.search(r'<input type="hidden" name="comment_language"[^>]*value="sk"', html)


def test_a_waiting_task_says_what_it_waits_for() -> None:
    waiting = _row("conflict", "waiting", branch="work", file_path="README.md")
    waiting["task"].detail = {"waiting_for": "edit"}
    missing = _row("conflict", "waiting", branch="fix", file_path="docs/x.md")
    missing["task"].detail = {"waiting_for": "file"}
    html = _render(_connected(), activity=[waiting, missing])
    assert "Čaká, kým vetva zmení <code>README.md</code>" in html
    assert "Súbor v repozitári nie je: <code>docs/x.md</code>" in html

"""An archived course must be read-only on the server, in every scenario.

The UI dims the write buttons on an archived course, but a stale tab, a
bookmarked form post or a direct API call must be rejected too.  These are
source-level assertions: each course-scoped *write* handler has to carry an
archived guard, so adding a new mutation without one fails here instead of
silently letting an archived course be edited in production.

Guard vocabulary (any one counts):
  * ``ensure_course_active``  - shared 409 helper (app.services.courses)
  * ``_archived_block``       - course-checks JSONResponse variant
  * an explicit ``course.is_active`` / ``not course.is_active`` branch
"""

import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

import app.api.courses as api_courses
import app.api.dashboard.courses.settings as dash_course_settings
import app.api.dashboard.projects.llm as dash_projects_llm
import app.api.dashboard.teams.llm as dash_teams_llm
import app.api.dashboard.teams.routes as dash_teams
import app.api.projects as api_projects
import app.api.sync as api_sync
import app.api.teams as api_teams
from app.services.gitlab_import import persistence as _gitlab_import_persistence

_GUARDS = (
    "ensure_course_active",
    "_archived_block",
    "course.is_active",
    "_ensure_not_archived",
)

# Every handler that writes something owned by a course. Permanent deletes are
# deliberately absent: purging an archived course (and its groups/projects) is
# how archived data is cleaned up, and the course-level purge already *requires*
# the course to be archived first.
WRITE_HANDLERS: list[tuple[str, Callable[..., object]]] = [
    ("sync: group sync", api_sync.trigger_sync),
    ("sync: project sync", api_sync.trigger_project_sync),
    ("sync: group run-checks", api_sync.run_selected_checks),
    ("sync: course run-checks", api_sync.run_selected_checks_all),
    ("sync: course sync-all", api_sync.trigger_sync_all),
    ("teams: create", api_teams.create_team),
    ("teams: update", api_teams.update_team),
    ("teams: delete", api_teams.delete_team),
    ("teams: reactivate", api_teams.reactivate_team),
    ("projects: link", api_projects.register_project),
    ("projects: unlink", api_projects.delete_project),
    ("projects: reactivate", api_projects.reactivate_project),
    ("courses: update", api_courses.update_course),
    ("courses: update settings", api_courses.update_course_settings),
    ("dashboard: settings save", dash_course_settings.course_settings_save),
    ("dashboard: full-config import", dash_course_settings.full_config_import),
    ("dashboard: member exclusion toggle", dash_teams.toggle_member_exclusion),
    ("dashboard: project LLM analyze", dash_projects_llm.project_llm_analyze),
    ("dashboard: single-MR LLM analyze", dash_projects_llm.project_llm_analyze_single_mr),
    ("dashboard: team LLM analyze", dash_teams_llm.trigger_llm_analysis),
    ("import: resolve target course", _gitlab_import_persistence._get_or_create_course),
]


@pytest.mark.parametrize(
    ("label", "handler"), WRITE_HANDLERS, ids=lambda v: v if isinstance(v, str) else ""
)
def test_course_write_handler_rejects_archived(label: str, handler: Callable[..., object]) -> None:
    source = inspect.getsource(handler)
    assert any(guard in source for guard in _GUARDS), (
        f"{label} ({handler.__module__}.{handler.__name__}) mutates course-owned data "
        f"but has no archived-course guard. Add `await ensure_course_active(db, <course_id>)`."
    )


def test_import_does_not_silently_unarchive_a_course() -> None:
    """Importing a GitLab group must never flip ``is_active`` back to True.

    That was the loophole: ``_get_or_create_course`` set ``course.is_active =
    True`` on the resolved course, so re-importing into (or matching) an
    archived course quietly brought it back to life.
    """
    source = inspect.getsource(_gitlab_import_persistence._get_or_create_course)
    assert "is_active = True" not in source


def test_pressing_an_unavailable_control_says_why_whatever_made_it_unavailable() -> None:
    """A control put out of reach explains itself when pressed, not only when hovered.

    The reason rides on a `.gl-tip-wrap` around the control, because a disabled
    control emits no pointer events of its own - and the tooltip that carries it
    is hover-only (`touch: false`), so on a phone a press is the ONLY way to ask.
    The click handler used to answer for exactly one cause, the archived lock:
    anything disabled by a running process or a permission had its reason sitting
    on the wrapper with nothing to read it out, so it stayed mute and the reader
    could not tell "not allowed yet" from "broken".
    """
    guard = (
        Path(__file__).resolve().parents[2]
        / "src/app/templates/static/js/_parts/core/48-archived-course.js"
    ).read_text(encoding="utf-8")
    handler = guard.split("Pressing something unavailable answers with WHY", 1)[1]
    handler = handler.split("}, true);", 1)[0]
    assert "data-archived-locked" in handler, "the archived lock still answers"
    assert "wrap.dataset.disabledReason" in handler, "so does every other reason"
    assert "closest('.gl-tip-wrap')" in handler, "a disabled control is reached via its wrapper"

"""What every tool shares: the event's context, who acted, and the task row."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.compliance.patterns import resolve_patterns
from app.models.assistant import AssistantTask, CourseAssistant
from app.models.course import Course
from app.models.course_settings import DEFAULT_BRANCH_PATTERN, CourseSettings
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team_member import TeamMember
from app.services.gitlab.client_types import GitLabAPIError

# Task states. The page colours them; the tools move between them.
WAITING = "waiting"  # watching, nothing to do yet
PLANTED = "planted"  # the colleague's conflicting commit is in
ASSIGNED = "assigned"  # the issue is open, no merge request yet
NEEDS_WORK = "needs_work"  # the last review asked for changes
APPROVED = "approved"  # approved, merging once GitLab allows it
PASSED = "passed"  # done, and done right
MERGED_UNREVIEWED = "merged_unreviewed"  # merged before the review approved it
FAILED = "failed"  # GitLab refused what the assistant tried

#: States a tool no longer acts on.
FINISHED = frozenset({PASSED, MERGED_UNREVIEWED})

_HISTORY_LIMIT = 50


@dataclass(frozen=True)
class Context:
    """The event's course, project and assistant."""

    course: Course
    project: GitLabProject
    assistant: CourseAssistant
    default_branch: str
    #: The project's page in GitLab, for the links the teacher follows.
    web_url: str
    #: The course's branch-naming rule, when it grades one (R02).
    branch_rule: str = ""
    #: The MR description sections the course requires, when it does (R05).
    required_sections: tuple[str, ...] = ()

    @property
    def gitlab_id(self) -> int:
        return self.project.gitlab_project_id

    def commit_url(self, sha: str) -> str:
        return f"{self.web_url}/-/commit/{sha}"

    def merge_request_url(self, iid: int) -> str:
        return f"{self.web_url}/-/merge_requests/{iid}"


def course_rules(settings: CourseSettings | None) -> tuple[str, tuple[str, ...]]:
    """The branch rule and MR sections the course grades by - empty for a
    check the course has switched off, so the assistant never asks for more
    than the course itself does."""
    if settings is None:
        return "", ()
    patterns = resolve_patterns(settings)
    enabled = set(settings.enabled_checks or [])
    branch = patterns.branch_pattern if "R02" in enabled else ""
    sections = tuple(patterns.required_sections) if "R05" in enabled else ()
    return branch, sections


def branch_rule_to_name(rule: str) -> str:
    """The branch rule as a student or a teacher is told it: the default one
    (any name but main and the like) goes without saying."""
    return "" if rule == DEFAULT_BRANCH_PATTERN else rule


def counted_member() -> tuple[ColumnElement[bool], ...]:
    """A team member the course counts as a student: active, not a teacher or
    a mentor, and not excluded from scoring by the teacher."""
    return (
        TeamMember.is_active.is_(True),
        TeamMember.is_teacher.is_(False),
        TeamMember.is_mentor.is_(False),
        TeamMember.excluded_from_scoring.is_(False),
    )


async def acting_student(
    session: AsyncSession, project: GitLabProject, gitlab_user_id: Any, username: Any
) -> Student | None:
    """The project team's student who did this - or None for a teacher, a
    mentor, someone excluded from scoring, the bot itself, or someone
    GitPulse does not know."""
    match = []
    if isinstance(gitlab_user_id, int):
        match.append(Student.gitlab_user_id == gitlab_user_id)
    if isinstance(username, str) and username:
        match.append(Student.gitlab_username == username)
    if not match:
        return None
    stmt = (
        select(Student)
        .join(TeamMember, TeamMember.student_id == Student.id)
        .where(TeamMember.team_id == project.team_id, *counted_member())
        .where(or_(*match))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def lock(session: AsyncSession, project_id: uuid.UUID, tool: str, key: str) -> None:
    """Serialise work on one task until the transaction ends.

    Two events for the same merge request can be handled at the same moment
    (a push and a comment), and both would review it and post twice. The
    advisory lock is released by the commit that records what was done.
    """
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"assistant:{project_id}:{tool}:{key}"},
    )


async def find_task(
    session: AsyncSession, project_id: uuid.UUID, tool: str, key: str
) -> AssistantTask | None:
    stmt = select(AssistantTask).where(
        AssistantTask.project_id == project_id,
        AssistantTask.tool == tool,
        AssistantTask.key == key,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def new_task(ctx: Context, tool: str, key: str, state: str, **fields: Any) -> AssistantTask:
    fields.setdefault("detail", {})
    fields.setdefault("history", [])
    return AssistantTask(
        course_id=ctx.course.id,
        project_id=ctx.project.id,
        tool=tool,
        key=key,
        state=state,
        **fields,
    )


def record(task: AssistantTask, action: str, note: str = "", url: str | None = None) -> None:
    """Append one step to what the teacher sees the assistant did."""
    entry = {"at": datetime.now(UTC).isoformat(), "action": action, "note": note[:300]}
    if url:
        entry["url"] = url
    # A new list, so the JSONB column is seen as changed.
    task.history = [*(task.history or []), entry][-_HISTORY_LIMIT:]


def set_detail(task: AssistantTask, **values: Any) -> None:
    task.detail = {**(task.detail or {}), **values}


def finish(task: AssistantTask, state: str) -> None:
    task.state = state
    task.completed_at = datetime.now(UTC)


def is_transient(exc: GitLabAPIError) -> bool:
    """Worth retrying: GitLab unreachable, overloaded or failing - not a refusal."""
    return exc.status_code == 0 or exc.status_code == 429 or exc.status_code >= 500


def refused(task: AssistantTask, exc: GitLabAPIError) -> None:
    """GitLab said no (no permission, a protected branch, a stale sha): the
    teacher sees why in the task's history; retrying would get the same no."""
    task.state = FAILED
    record(task, "error", str(exc))

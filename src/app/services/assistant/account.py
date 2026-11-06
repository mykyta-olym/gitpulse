"""Setting the assistant up - what the course's Assistant page does.

Connecting a token is an explicit teacher action, so it is the one place the
web process talks to GitLab here: it asks who the token is and what it may do,
before anything is stored.
"""

import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.i18n import SUPPORTED_LOCALES
from app.models.assistant import (
    DEFAULT_COMMENT_LANGUAGE,
    DEFAULT_CONFLICT_FILE,
    DEFAULT_EXERCISE_FILE_TEMPLATE,
    DEFAULT_MIN_COMMIT_TITLE_LENGTH,
    AssistantTask,
    CourseAssistant,
)
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.security.token_encryption import encrypt_token
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.exercise import USERNAME_FIELD
from app.services.audit import write_audit
from app.services.gitlab.client_types import GitLabAPIError

logger = logging.getLogger(__name__)

#: The activity table shows the latest this many; older rows stay stored.
ACTIVITY_LIMIT = 500

MIN_TITLE_LENGTH = (1, 72)


class TokenRejectedError(Exception):
    """The token cannot be the bot's; ``reason`` says why, for the page."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


async def assistant_for(session: AsyncSession, course_id: uuid.UUID) -> CourseAssistant | None:
    stmt = select(CourseAssistant).where(CourseAssistant.course_id == course_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def ensure_assistant(session: AsyncSession, course_id: uuid.UUID) -> CourseAssistant:
    """The course's assistant row - every column has a default, so a course
    that never had one gets one the first time a teacher changes something."""
    assistant = await assistant_for(session, course_id)
    if assistant is None:
        assistant = CourseAssistant(course_id=course_id)
        session.add(assistant)
        await session.flush()
    return assistant


def _expiry(value: Any) -> datetime | None:
    """GitLab's ``expires_at`` (a date) as the moment the token stops working."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.combine(date.fromisoformat(value[:10]), datetime.min.time(), tzinfo=UTC)
    except ValueError:
        return None


async def connect(
    session: AsyncSession, course_id: uuid.UUID, token: str, *, actor: str
) -> CourseAssistant:
    """Store ``token`` as the course bot's once GitLab confirms it can act."""
    token = token.strip()
    settings = get_settings()
    if not token:
        raise TokenRejectedError("empty")
    # Watching and acting stay apart: the sync token is read-only on purpose.
    if settings.gitlab_api_token and token == settings.gitlab_api_token:
        raise TokenRejectedError("read_token")
    try:
        async with BotGitLabClient(settings.gitlab_url, token) as bot:
            user = await bot.current_user()
            info = await bot.token_info()
    except GitLabAPIError as exc:
        raise TokenRejectedError(
            "invalid" if exc.status_code in (401, 403) else "unreachable"
        ) from exc
    if not user or not user.get("id"):
        raise TokenRejectedError("invalid")
    scopes = (info or {}).get("scopes")
    if isinstance(scopes, list) and "api" not in scopes:
        raise TokenRejectedError("scope")

    assistant = await ensure_assistant(session, course_id)
    assistant.bot_token = encrypt_token(token, settings.secret_key)
    assistant.bot_user_id = int(user["id"])
    assistant.bot_username = str(user.get("username") or "")[:100] or None
    assistant.bot_name = str(user.get("name") or "")[:200] or None
    assistant.bot_avatar_url = str(user.get("avatar_url") or "")[:500] or None
    assistant.token_expires_at = _expiry((info or {}).get("expires_at"))
    assistant.token_rejected_at = None
    assistant.connected_at = datetime.now(UTC)
    assistant.connected_by = actor[:100]
    await write_audit(
        session,
        action="assistant.connected",
        actor=actor,
        entity_type="course",
        entity_id=assistant.course_id,
        detail={
            "summary": f"@{assistant.bot_username}",
            "bot_username": assistant.bot_username,
            "bot_user_id": assistant.bot_user_id,
        },
    )
    await session.commit()
    return assistant


async def disconnect(session: AsyncSession, assistant: CourseAssistant, *, actor: str) -> None:
    """Forget the token; every tool stops until one is connected again."""
    username = assistant.bot_username
    assistant.bot_token = None
    assistant.bot_user_id = None
    assistant.bot_username = None
    assistant.bot_name = None
    assistant.bot_avatar_url = None
    assistant.token_expires_at = None
    assistant.token_rejected_at = None
    assistant.connected_at = None
    assistant.connected_by = None
    await write_audit(
        session,
        action="assistant.disconnected",
        actor=actor,
        entity_type="course",
        entity_id=assistant.course_id,
        detail={"summary": f"@{username}" if username else "", "bot_username": username},
    )
    await session.commit()


async def mark_token_rejected(
    session: AsyncSession, assistant_id: uuid.UUID, ciphertext: str | None
) -> None:
    """GitLab refused the bot's token: stop the assistant until a new one.

    Only for the token that was refused - a teacher may have connected a new
    one while the job ran, and that one must not inherit the refusal.
    """
    refused = (
        await session.execute(
            update(CourseAssistant)
            .where(
                CourseAssistant.id == assistant_id,
                CourseAssistant.bot_token == ciphertext,
                CourseAssistant.token_rejected_at.is_(None),
            )
            .values(token_rejected_at=datetime.now(UTC))
            .returning(CourseAssistant.course_id, CourseAssistant.bot_username)
        )
    ).first()
    if refused is not None:
        # Once, when it is first refused: the teachers' feed says it.
        await write_audit(
            session,
            action="assistant.token_rejected",
            actor="system",
            entity_type="course",
            entity_id=refused.course_id,
            detail={"summary": f"@{refused.bot_username}" if refused.bot_username else ""},
        )
    await session.commit()
    logger.warning("assistant_token_rejected assistant=%s", assistant_id)


def is_repo_path(path: str) -> bool:
    """A path inside the repository: relative, no ``..``, no empty segment."""
    if not path or len(path) > 300 or path.startswith("/") or "\\" in path:
        return False
    if any(ch in path for ch in "\0\r\n"):
        return False
    return all(part not in ("", ".", "..") for part in path.split("/"))


@dataclass(frozen=True)
class Tools:
    """The tools form, read and checked."""

    push_review_enabled: bool
    min_commit_title_length: int
    conflict_enabled: bool
    conflict_file_path: str
    mr_review_enabled: bool
    mr_bot_merges: bool
    exercise_file_template: str
    comment_language: str

    def errors(self) -> list[str]:
        found = []
        if self.comment_language not in SUPPORTED_LOCALES:
            found.append("comment_language")
        low, high = MIN_TITLE_LENGTH
        if not low <= self.min_commit_title_length <= high:
            found.append("min_commit_title_length")
        if not is_repo_path(self.conflict_file_path):
            found.append("conflict_file_path")
        template = self.exercise_file_template
        if USERNAME_FIELD not in template or not is_repo_path(
            template.replace(USERNAME_FIELD, "user")
        ):
            found.append("exercise_file_template")
        return found


def tools_of(assistant: CourseAssistant | None) -> Tools:
    """What the tools form shows - the defaults for a course with no row yet."""
    if assistant is None:
        return Tools(
            push_review_enabled=False,
            min_commit_title_length=DEFAULT_MIN_COMMIT_TITLE_LENGTH,
            conflict_enabled=False,
            conflict_file_path=DEFAULT_CONFLICT_FILE,
            mr_review_enabled=False,
            mr_bot_merges=False,
            exercise_file_template=DEFAULT_EXERCISE_FILE_TEMPLATE,
            comment_language=DEFAULT_COMMENT_LANGUAGE,
        )
    return Tools(
        push_review_enabled=assistant.push_review_enabled,
        min_commit_title_length=assistant.min_commit_title_length,
        conflict_enabled=assistant.conflict_enabled,
        conflict_file_path=assistant.conflict_file_path,
        mr_review_enabled=assistant.mr_review_enabled,
        mr_bot_merges=assistant.mr_bot_merges,
        exercise_file_template=assistant.exercise_file_template,
        comment_language=assistant.comment_language,
    )


def read_tools(form: Any) -> Tools:
    def text(name: str) -> str:
        return str(form.get(name) or "").strip()

    try:
        min_length = int(text("min_commit_title_length"))
    except ValueError:
        min_length = 0
    return Tools(
        push_review_enabled=text("push_review_enabled") == "true",
        min_commit_title_length=min_length,
        conflict_enabled=text("conflict_enabled") == "true",
        conflict_file_path=text("conflict_file_path"),
        mr_review_enabled=text("mr_review_enabled") == "true",
        mr_bot_merges=text("mr_bot_merges") == "true",
        exercise_file_template=text("exercise_file_template"),
        comment_language=text("comment_language") or DEFAULT_COMMENT_LANGUAGE,
    )


def _set_tools(assistant: CourseAssistant, tools: Tools) -> None:
    """The one place the tool settings are written onto the row - the form,
    a semester transfer and a configuration file all go through it."""
    for name, value in asdict(tools).items():
        setattr(assistant, name, value)


def tools_config(assistant: CourseAssistant | None) -> dict[str, Any]:
    """The tools as the course's configuration file carries them: settings
    only - never the bot or its token, which belong to one course's group."""
    return asdict(tools_of(assistant))


def tools_from_config(
    current: CourseAssistant | None, data: dict[str, Any]
) -> tuple[Tools | None, list[str]]:
    """Tools from a configuration file's ``assistant`` section, over what the
    course has now (a field the file leaves out stays as it is). None and the
    fields that do not check out when they do not."""
    merged = asdict(tools_of(current))
    bad = [
        name
        for name, value in data.items()
        if name in merged and type(value) is not type(merged[name])
    ]
    if bad:
        return None, bad
    merged.update({name: value for name, value in data.items() if name in merged})
    tools = Tools(**merged)
    errors = tools.errors()
    return (None, errors) if errors else (tools, [])


async def import_tools(
    session: AsyncSession, course_id: uuid.UUID, data: dict[str, Any]
) -> list[str]:
    """Apply a configuration file's ``assistant`` section; the fields it got
    wrong (and then nothing is applied)."""
    current = await assistant_for(session, course_id)
    tools, bad = tools_from_config(current, data)
    if tools is None:
        return bad
    _set_tools(current or await ensure_assistant(session, course_id), tools)
    return []


async def save_tools(
    session: AsyncSession, assistant: CourseAssistant, tools: Tools, *, actor: str
) -> None:
    _set_tools(assistant, tools)
    await write_audit(
        session,
        action="assistant.tools_saved",
        actor=actor,
        entity_type="course",
        entity_id=assistant.course_id,
        detail={
            "push_review": tools.push_review_enabled,
            "conflict": tools.conflict_enabled,
            "mr_review": tools.mr_review_enabled,
            "mr_bot_merges": tools.mr_bot_merges,
        },
    )
    await session.commit()


#: A token this close to its expiry date is flagged on the page.
_EXPIRY_WARNING_DAYS = 14


def token_state(assistant: CourseAssistant | None) -> str | None:
    """``expired`` / ``expiring`` / ``ok`` - None when GitLab gave no expiry."""
    if assistant is None or assistant.token_expires_at is None:
        return None
    left = assistant.token_expires_at - datetime.now(UTC)
    if left.total_seconds() <= 0:
        return "expired"
    return "expiring" if left.days < _EXPIRY_WARNING_DAYS else "ok"


def problems(assistant: CourseAssistant | None) -> list[str]:
    """What keeps a course's assistant from acting, or soon will.

    The one answer the Assistant page (its top alerts) and the dashboard's
    "Items that need your attention" both give: ``token_rejected`` /
    ``token_expired`` / ``no_bot`` (tools on, no bot) stop it - one of them at
    most, the first that holds - and ``token_expiring`` / ``run_stale`` (a
    Prepare exercise that never finished) will.
    """
    if assistant is None:
        return []
    found: list[str] = []
    connected = assistant.is_connected
    tools_on = (
        assistant.push_review_enabled or assistant.conflict_enabled or assistant.mr_review_enabled
    )
    state = token_state(assistant)
    if connected and assistant.token_rejected_at:
        found.append("token_rejected")
    elif connected and state == "expired":
        found.append("token_expired")
    elif tools_on and not connected:
        found.append("no_bot")
    elif connected and state == "expiring":
        found.append("token_expiring")
    run = last_exercise_run(assistant)
    if run is not None and run["state"] == "stale":
        found.append("run_stale")
    return found


#: A run still "running" after this long died without writing its result.
_RUN_STALE_AFTER = timedelta(minutes=15)


def last_exercise_run(assistant: CourseAssistant | None) -> dict[str, Any] | None:
    """The last "Prepare exercise" run for the page: its time as a datetime and
    its state - ``running``, ``stale`` (it never finished) or ``done``."""
    run = assistant.last_exercise_run if assistant else None
    if not run:
        return None
    try:
        at: datetime | None = datetime.fromisoformat(str(run.get("at")))
    except ValueError:
        at = None
    state = "done"
    if run.get("status") == "running":
        fresh = at is not None and datetime.now(UTC) - at < _RUN_STALE_AFTER
        state = "running" if fresh else "stale"
    return {**run, "at": at, "state": state}


async def start_exercise_run(
    session: AsyncSession, assistant: CourseAssistant, *, actor: str
) -> dict[str, Any] | None:
    """Mark a run as started, so the page says so until its result lands.
    Returns the record it replaced, for undoing when the queue refuses."""
    previous = assistant.last_exercise_run
    assistant.last_exercise_run = {
        "status": "running",
        "at": datetime.now(UTC).isoformat(),
        "by": actor,
        "projects": [],
    }
    await session.commit()
    return previous


async def stop_exercise_run(
    session: AsyncSession, assistant: CourseAssistant, *, actor: str, reason: str
) -> None:
    """A run that could not start ends now, with why - not "Preparing" until
    it goes stale a quarter of an hour later."""
    assistant.last_exercise_run = {
        "at": datetime.now(UTC).isoformat(),
        "by": actor,
        "projects": [],
        "error": reason,
    }
    await session.commit()


async def carry_over(
    session: AsyncSession, source_course_id: uuid.UUID, new_course_id: uuid.UUID
) -> None:
    """A course transferred to a new semester keeps how its assistant is set
    up - the tools and their settings - but not the bot: a token belongs to one
    course's group, and the new semester connects its own."""
    source = await assistant_for(session, source_course_id)
    if source is None:
        return
    carried = CourseAssistant(course_id=new_course_id)
    _set_tools(carried, tools_of(source))
    session.add(carried)
    await session.flush()


async def course_projects(session: AsyncSession, course_id: uuid.UUID) -> list[dict[str, Any]]:
    """The course's live projects, for the exercise dialog."""
    stmt = (
        select(GitLabProject.id, GitLabProject.gitlab_project_path, Team.name)
        .join(Team, Team.id == GitLabProject.team_id)
        .where(
            Team.course_id == course_id,
            Team.is_active.is_(True),
            GitLabProject.is_active.is_(True),
        )
        .order_by(Team.name, GitLabProject.gitlab_project_path)
    )
    return [
        {"id": str(pid), "path": path, "team": team}
        for pid, path, team in (await session.execute(stmt)).all()
    ]


async def activity(session: AsyncSession, course_id: uuid.UUID) -> list[dict[str, Any]]:
    """The newest tasks first, each with what the table shows."""
    gitlab_url = get_settings().gitlab_url.rstrip("/")
    stmt = (
        select(
            AssistantTask,
            GitLabProject.gitlab_project_path,
            Team.name,
            Student.full_name,
            Student.gitlab_user_id,
        )
        .join(GitLabProject, GitLabProject.id == AssistantTask.project_id)
        .join(Team, Team.id == GitLabProject.team_id)
        .outerjoin(Student, Student.id == AssistantTask.student_id)
        .where(AssistantTask.course_id == course_id)
        .order_by(AssistantTask.updated_at.desc())
        .limit(ACTIVITY_LIMIT)
    )
    rows = []
    for task, path, team, name, gitlab_user_id in (await session.execute(stmt)).all():
        web = f"{gitlab_url}/{path}"
        last = (task.history or [{}])[-1]
        rows.append(
            {
                "task": task,
                "student_name": name or task.student_username,
                "student_gitlab_id": gitlab_user_id,
                "team": team,
                "project_path": path,
                "issue_url": f"{web}/-/issues/{task.issue_iid}" if task.issue_iid else None,
                "mr_url": f"{web}/-/merge_requests/{task.mr_iid}" if task.mr_iid else None,
                "commit_url": f"{web}/-/commit/{task.commit_sha}" if task.commit_sha else None,
                "last_action": last.get("action"),
                "last_note": last.get("note") or "",
                "last_url": last.get("url"),
            }
        )
    return rows

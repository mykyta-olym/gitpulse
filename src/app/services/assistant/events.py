"""Which webhook events the assistant acts on, and handing them to its tools.

The webhook pipeline stores and processes every event as before; once one is
processed, ``wants`` decides - with one query, and none at all while the
feature is off - whether the event's course runs a tool that cares. Only then
is the assistant job queued, so a course without an assistant costs nothing.

The assistant ignores what its own account did (its comments, its commit, its
approval), or it would answer itself. The one exception is GitLab's merge
event: when the bot merged, or the pipeline it waited for passed, that event is
how the exercise learns the merge happened.

A token past its expiry, or one GitLab refused, stops the assistant: every
event would only collect the same 401. A refusal is confirmed (``GET /user``)
and recorded on the course, and the Assistant page asks for a new token.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.assistant import CourseAssistant
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.webhook_event import WebhookEvent
from app.security.token_encryption import decrypt_token
from app.services.assistant import account, conflict, mr_review, push_review, texts
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.tasks import Context, acting_student, course_rules

logger = logging.getLogger(__name__)

KINDS = frozenset({"push", "merge_request", "note"})


def _tool_on(assistant: CourseAssistant, kind: str) -> bool:
    """A tool for this kind is on - and the bot's token can still act."""
    if not assistant.can_act(datetime.now(UTC)):
        return False
    if kind == "push":
        return assistant.push_review_enabled or assistant.conflict_enabled
    return assistant.mr_review_enabled


async def _load(
    session: AsyncSession, gitlab_project_id: int
) -> tuple[Course, GitLabProject, CourseAssistant] | None:
    """The project's course and assistant - when it is live and connected."""
    stmt = (
        select(Course, GitLabProject, CourseAssistant)
        .join(Team, Team.course_id == Course.id)
        .join(GitLabProject, GitLabProject.team_id == Team.id)
        .join(CourseAssistant, CourseAssistant.course_id == Course.id)
        .where(
            GitLabProject.gitlab_project_id == gitlab_project_id,
            GitLabProject.is_active.is_(True),
            Team.is_active.is_(True),
            Course.is_active.is_(True),
            CourseAssistant.bot_token.is_not(None),
        )
    )
    row = (await session.execute(stmt)).first()
    return (row[0], row[1], row[2]) if row else None


async def wants(session: AsyncSession, gitlab_project_id: int, kind: str) -> bool:
    if kind not in KINDS or not get_settings().feature_classroom_assistant:
        return False
    loaded = await _load(session, gitlab_project_id)
    return loaded is not None and _tool_on(loaded[2], kind)


def _actor(kind: str, payload: dict[str, Any]) -> tuple[Any, Any]:
    """Who caused the event: GitLab's id and username for them."""
    if kind == "push":
        return payload.get("user_id"), payload.get("user_username")
    user = payload.get("user") or {}
    return user.get("id"), user.get("username")


async def handle(session: AsyncSession, event: WebhookEvent) -> uuid.UUID | None:
    """Run the tools the event is for; the course they ran for, if any - its
    Assistant page is told, so its activity table shows what was done."""
    kind = event.gitlab_object_kind or ""
    payload = event.payload or {}
    settings = get_settings()
    if kind not in KINDS or not settings.feature_classroom_assistant:
        return None
    loaded = await _load(session, event.gitlab_project_id)
    if loaded is None or not _tool_on(loaded[2], kind):
        return None
    course, project, assistant = loaded
    token = decrypt_token(assistant.bot_token, settings.secret_key)
    if not token:
        logger.warning("assistant_token_unreadable course=%s", course.id)
        return None

    actor_id, actor_username = _actor(kind, payload)
    by_bot = actor_id is not None and actor_id == assistant.bot_user_id
    student = None if by_bot else await acting_student(session, project, actor_id, actor_username)
    branch_rule, sections = course_rules(course.settings)
    ctx = Context(
        course,
        project,
        assistant,
        default_branch=(payload.get("project") or {}).get("default_branch")
        or project.default_branch,
        web_url=f"{settings.gitlab_url.rstrip('/')}/{project.gitlab_project_path}",
        branch_rule=branch_rule,
        required_sections=sections,
    )
    ciphertext = assistant.bot_token
    async with BotGitLabClient(settings.gitlab_url, token) as bot:
        with texts.speaking(assistant.comment_language):
            if kind == "push":
                if student is not None:
                    if assistant.push_review_enabled:
                        await push_review.handle(session, ctx, bot, payload, student)
                    if assistant.conflict_enabled:
                        await conflict.handle(session, ctx, bot, payload, student)
            elif kind == "merge_request":
                await mr_review.on_merge_request(session, ctx, bot, payload, by_bot=by_bot)
            elif student is not None:
                await mr_review.on_note(session, ctx, bot, payload, student)
        if await bot.token_rejected():
            await account.mark_token_rejected(session, assistant.id, ciphertext)
    return course.id

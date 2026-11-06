"""RQ jobs of the classroom assistant (``app.services.assistant``).

``run_assistant`` follows a processed webhook event; ``prepare_exercise`` is
the teacher's "Prepare exercise" action. Both talk to GitLab as the course's
bot account, so neither runs in a web request.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import async_session_ctx, dispose_engine, init_engine
from app.models.assistant import CourseAssistant
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.webhook_event import WebhookEvent
from app.security.token_encryption import decrypt_token
from app.services.assistant import account, events, exercise, texts
from app.services.assistant.client import BotGitLabClient
from app.workers.idempotency import idempotent_job
from app.workers.progress import publish_dashboard_update, publish_progress

logger = logging.getLogger(__name__)


@idempotent_job
def run_assistant(event_id: str) -> None:
    asyncio.run(_run_assistant(event_id))


async def _run_assistant(event_id: str) -> None:
    init_engine(str(get_settings().database_url))
    try:
        async with async_session_ctx() as session:
            event = await session.get(WebhookEvent, uuid.UUID(event_id))
            if event is None:
                logger.error("assistant_event_missing event=%s", event_id)
                return
            course_id = await events.handle(session, event)
        if course_id is not None:
            # The course's Assistant page refreshes its activity table.
            publish_dashboard_update("course", str(course_id), "assistant_activity")
    finally:
        await dispose_engine()


@idempotent_job
def prepare_exercise(
    course_id: str, project_ids: list[str], actor: str, job_id: str | None = None
) -> None:
    asyncio.run(_prepare_exercise(course_id, project_ids, actor, job_id))


async def _track(session: AsyncSession, job_id: str | None, status: str, message: str) -> None:
    """The run's BackgroundJob - what the top bar follows and Job History lists."""
    job = await session.get(BackgroundJob, uuid.UUID(job_id)) if job_id else None
    if job is None or job_id is None:
        return
    now = datetime.now(UTC)
    job.status = status
    extra: dict[str, object] = {"progress": 0}
    if status == "running":
        job.started_at = now
    else:
        job.completed_at = now
        job.duration_ms = int((now - (job.started_at or job.enqueued_at)).total_seconds() * 1000)
        if status == "failed":
            job.error_message = message
            extra["error_message"] = message
        else:
            job.result_summary = message
            extra = {"progress": 100, "result_summary": message}
    await session.commit()
    publish_progress(job_id, status, message, extra=extra)


async def _course_projects(
    session: AsyncSession, course_id: uuid.UUID, project_ids: list[str]
) -> list[GitLabProject]:
    """The chosen projects that are still the course's and still live."""
    stmt = (
        select(GitLabProject)
        .join(Team, Team.id == GitLabProject.team_id)
        .where(
            Team.course_id == course_id,
            Team.is_active.is_(True),
            GitLabProject.is_active.is_(True),
            GitLabProject.id.in_([uuid.UUID(p) for p in project_ids]),
        )
        .order_by(GitLabProject.gitlab_project_path)
    )
    return list((await session.execute(stmt)).scalars())


async def _prepare_exercise(
    course_id: str, project_ids: list[str], actor: str, job_id: str | None = None
) -> None:
    settings = get_settings()
    init_engine(str(settings.database_url))
    try:
        async with async_session_ctx() as session:
            await _track(session, job_id, "running", "Preparing the exercise...")
            course = await session.get(Course, uuid.UUID(course_id))
            stmt = select(CourseAssistant).where(CourseAssistant.course_id == uuid.UUID(course_id))
            assistant = (await session.execute(stmt)).scalar_one_or_none()
            token = decrypt_token(assistant.bot_token, settings.secret_key) if assistant else None
            # What could have changed since the click: said at once, on the
            # page and in the top bar, not "Preparing" until the run goes stale.
            reason = ""
            if course is None or not course.is_active:
                reason = "This course is archived and read-only. Reactivate it to make changes."
            elif assistant is None or not token:
                reason = "Connect the bot account first."
            elif not assistant.can_act(datetime.now(UTC)):
                reason = "The bot token does not work. Connect a new one first."
            if reason or course is None or assistant is None or not token:
                logger.warning("assistant_exercise_not_ready course=%s: %s", course_id, reason)
                if assistant is not None:
                    await account.stop_exercise_run(session, assistant, actor=actor, reason=reason)
                await _track(session, job_id, "failed", reason)
                return
            projects = await _course_projects(session, course.id, project_ids)
            ciphertext = assistant.bot_token

            def progress(done: int, total: int) -> None:
                if job_id:
                    publish_progress(
                        job_id,
                        "running",
                        "Preparing the exercise...",
                        extra={"progress": int(done * 100 / max(total, 1))},
                    )

            try:
                async with BotGitLabClient(settings.gitlab_url, token) as bot:
                    with texts.speaking(assistant.comment_language):
                        results = await exercise.prepare(
                            session,
                            course,
                            assistant,
                            bot,
                            projects,
                            actor=actor,
                            gitlab_url=settings.gitlab_url,
                            progress=progress,
                        )
                    if await bot.token_rejected():
                        await account.mark_token_rejected(session, assistant.id, ciphertext)
            except Exception:
                await session.rollback()
                failed = "Preparing the exercise failed. Try again."
                await account.stop_exercise_run(session, assistant, actor=actor, reason=failed)
                await _track(session, job_id, "failed", failed)
                raise
            refused = any(r.get("error") for r in results)
            await _track(
                session,
                job_id,
                "completed",
                "Exercise prepared - GitLab refused some projects"
                if refused
                else "Exercise prepared",
            )
        publish_dashboard_update("course", course_id, "assistant_activity")
    finally:
        await dispose_engine()

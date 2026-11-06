"""GitLab user/student enrichment background helpers.

Extracted from ``admin.py`` to keep that module focused on HTTP routes.
Pure helper functions invoked by the enrichment route handlers; no router
is defined here.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy import or_, select

from app.api.dashboard._helpers import (
    _clear_enrichment_status,
    _set_enrichment_status,
    logger,
)
from app.config import get_settings
from app.models.background_job import BackgroundJob
from app.models.student import Student
from app.models.user import User


class _EnrichmentCancelledError(Exception):
    """Raised when the admin cancels the cooperative enrichment task."""


async def _sync_roles_from_config(db: Any) -> int:
    """Re-sync ``User.role`` from GITLAB_ADMIN_USERNAMES / GITLAB_TEACHER_USERNAMES.

    Returns the number of roles updated.
    """
    settings = get_settings()
    admin_set = {u.lower() for u in settings.gitlab_admin_usernames}
    teacher_set = {u.lower() for u in settings.gitlab_teacher_usernames}
    all_config_names = admin_set | teacher_set
    if not all_config_names:
        return 0
    all_users_stmt = select(User).where(
        or_(
            sa_func.lower(User.gitlab_username).in_(all_config_names),
            sa_func.lower(User.username).in_(all_config_names),
        )
    )
    all_users = (await db.execute(all_users_stmt)).scalars().all()
    roles_updated = 0
    for u in all_users:
        uname = ((u.gitlab_username or u.username) or "").lower()
        if uname in admin_set:
            target = "admin"
        elif uname in teacher_set:
            target = "teacher"
        else:
            continue
        if not u.gitlab_username and u.username:
            u.gitlab_username = u.username
        if u.role != target and not u.role_locked:
            u.role = target
            roles_updated += 1
    if roles_updated:
        await db.flush()
        logger.info("role_sync_updated", count=roles_updated)
    return roles_updated


async def _finish_enrichment_job(
    job_id: str,
    status: str,
    result_summary: str | None = None,
    error_message: str | None = None,
) -> None:
    """Update the ``BackgroundJob`` record for enrichment when it finishes."""

    from app.db.session import async_session_ctx

    try:
        async with async_session_ctx() as db:
            job = await db.get(BackgroundJob, job_id)
            if job:
                completed_at = datetime.now(UTC)
                job.status = status
                job.completed_at = completed_at
                if job.started_at:
                    job.duration_ms = int(
                        (completed_at - job.started_at).total_seconds() * 1000,
                    )
                if result_summary:
                    job.result_summary = result_summary
                if error_message:
                    job.error_message = error_message
                await db.commit()
            else:
                logger.warning(
                    "enrichment_job_not_found",
                    job_id=job_id,
                )
    except Exception:
        logger.warning("failed_to_update_enrichment_job", job_id=job_id, exc_info=True)


def _found_email(data: dict[str, Any]) -> Any:
    return data.get("email") or data.get("public_email") or data.get("commit_email")


def _lacks_email(email: str | None) -> bool:
    return not email or email == "PRIVATE"


class _Enrichment:
    """One enrichment run: its counters, and the cooperative cancel check."""

    def __init__(self, db: Any, client: Any, job_id: str) -> None:
        self.db = db
        self.client = client
        self.job_id = job_id
        self.sem = asyncio.Semaphore(10)
        self.per_item_timeout = get_settings().gitlab_enrichment_per_item_timeout
        self.total = 0
        self.processed = 0
        self.names_enriched = 0
        self.emails_enriched = 0
        self.errors = 0

    def status(self, status: str, message: str, total: int | None = None) -> None:
        _set_enrichment_status(
            status=status,
            message=message,
            total=self.total if total is None else total,
            processed=self.processed,
            names_enriched=self.names_enriched,
            emails_enriched=self.emails_enriched,
            errors=self.errors,
        )

    async def raise_if_cancelled(self, pending: list[asyncio.Task[Any]] | None = None) -> None:
        status = (
            await self.db.execute(
                select(BackgroundJob.status).where(BackgroundJob.id == self.job_id)
            )
        ).scalar_one_or_none()
        if status == "cancelled":
            for task in pending or []:
                if not task.done():
                    task.cancel()
            raise _EnrichmentCancelledError

    async def run(self, items: list[Any], one: Any, label: str, *, progress: bool) -> None:
        """Enrich ``items`` concurrently (bounded), adding up what each found;
        a timeout or error counts as one error."""
        tasks = [asyncio.ensure_future(one(item)) for item in items]
        for coro in asyncio.as_completed(tasks):
            await self.raise_if_cancelled(tasks)
            try:
                e, n, err = await asyncio.wait_for(coro, timeout=self.per_item_timeout)
            except TimeoutError:
                err, e, n = 1, 0, 0
                logger.warning(f"enrich_{label}_timeout")
            except Exception as exc:
                err, e, n = 1, 0, 0
                logger.debug(f"enrich_{label}_error: %s", exc)
            self.emails_enriched += e
            self.names_enriched += n
            self.errors += err
            if progress:
                self.processed += 1
                self.status("running", f"Enriching: {self.processed}/{self.total}")
            await self.raise_if_cancelled(tasks)

    async def user(self, user: User) -> tuple[int, int, int]:
        """(emails_found, names_found, error_count) for one User."""
        from app.services.arena_email import lookup_email

        e_found = n_found = err = 0
        search_name = user.gitlab_username or user.username
        if not search_name:
            return e_found, n_found, err
        try:
            async with self.sem:
                search_results = await self.client._get_list(
                    "/users",
                    params={"username": search_name},
                )
            if search_results:
                gitlab_user = search_results[0]
                if not user.gitlab_username:
                    user.gitlab_username = search_name
                if not user.gitlab_user_id and gitlab_user.get("id"):
                    user.gitlab_user_id = gitlab_user["id"]
                if _lacks_email(user.email):
                    email = _found_email(gitlab_user) or await lookup_email(
                        search_name, get_settings()
                    )
                    if email:
                        user.email = email
                        e_found = 1
                if not user.full_name:
                    name = gitlab_user.get("name")
                    if name and name != search_name:
                        user.full_name = name
                        n_found = 1
            elif _lacks_email(user.email):
                email = await lookup_email(search_name, get_settings())
                if email:
                    user.email = email
                    e_found = 1
        except Exception as exc:
            logger.warning("Failed to enrich user %s: %s", search_name, exc)
            err = 1
        return e_found, n_found, err

    async def student(self, student: Student) -> tuple[int, int, int]:
        """(emails_found, names_found, error_count) for one Student."""
        from app.services.arena_email import lookup_email

        e_found = n_found = err = 0
        try:
            user_data = None
            if student.gitlab_user_id is not None:
                async with self.sem:
                    user_data = await self.client.get_user(student.gitlab_user_id)
            elif student.gitlab_username:
                async with self.sem:
                    results = await self.client._get_list(
                        "/users",
                        params={"username": student.gitlab_username},
                    )
                if results:
                    user_data = results[0]
                    if user_data.get("id"):
                        student.gitlab_user_id = user_data["id"]
            if user_data:
                if _lacks_email(student.email):
                    email = _found_email(user_data)
                    if not email and student.gitlab_username:
                        email = await lookup_email(student.gitlab_username, get_settings())
                    if email:
                        student.email = email
                        e_found = 1
                if not student.full_name:
                    name = user_data.get("name")
                    if name and name != student.gitlab_username:
                        student.full_name = name
                        n_found = 1
            elif _lacks_email(student.email) and student.gitlab_username:
                email = await lookup_email(student.gitlab_username, get_settings())
                if email:
                    student.email = email
                    e_found = 1
        except Exception as exc:
            logger.warning(
                "Failed to enrich student %s: %s",
                student.gitlab_username,
                exc,
            )
            err = 1
        return e_found, n_found, err

    def message(self, roles_updated: int = 0) -> str:
        error_note = f" ({self.errors} errors)" if self.errors else ""
        if self.names_enriched == 0 and self.emails_enriched == 0 and self.errors == 0:
            return "Data already up to date" + (
                f" ({roles_updated} roles updated)" if roles_updated else ""
            )
        role_note = f", {roles_updated} roles updated" if roles_updated else ""
        return (
            f"Enriched {self.names_enriched} names, {self.emails_enriched} emails"
            f"{role_note}{error_note}"
        )


def _missing_details() -> Any:
    return or_(
        Student.email.is_(None),
        Student.email == "PRIVATE",
        Student.full_name.is_(None),
    )


async def _students_from_users(db: Any) -> None:
    """A student without email or name takes it from the enriched User of
    the same GitLab username."""
    students = list(
        (
            await db.execute(
                select(Student)
                .where(_missing_details(), Student.gitlab_username.isnot(None))
                .limit(5000)
            )
        )
        .scalars()
        .all()
    )
    if not students:
        return
    users = {
        u.gitlab_username: u
        for u in (
            await db.execute(
                select(User).where(User.gitlab_username.in_([s.gitlab_username for s in students]))
            )
        )
        .scalars()
        .all()
    }
    for student in students:
        linked = users.get(student.gitlab_username)
        if not linked:
            continue
        if _lacks_email(student.email) and not _lacks_email(linked.email):
            student.email = linked.email
        if not student.full_name and linked.full_name:
            student.full_name = linked.full_name
    await db.flush()


async def _users_from_students(db: Any, students: list[Student]) -> None:
    """...and a User without email or name takes it from its enriched Student."""
    gl_usernames = [s.gitlab_username for s in students if s.gitlab_username]
    if not gl_usernames:
        return
    users = {
        u.gitlab_username: u
        for u in (await db.execute(select(User).where(User.gitlab_username.in_(gl_usernames))))
        .scalars()
        .all()
    }
    for student in students:
        linked_user = users.get(student.gitlab_username)
        if not linked_user:
            continue
        if not _lacks_email(student.email) and _lacks_email(linked_user.email):
            linked_user.email = student.email
        if student.full_name and not linked_user.full_name:
            linked_user.full_name = student.full_name


async def _run_gitlab_enrichment(
    gitlab_url: str, gitlab_token: str, api_timeout: int, job_id: str
) -> None:
    """Background task to run GitLab enrichment with progress tracking.

    Uses concurrent API calls (bounded by a semaphore) to speed up
    enrichment dramatically vs the old serial approach.
    """
    from app.db.session import async_session_ctx
    from app.services.gitlab.client import GitLabClient

    client = GitLabClient(
        base_url=gitlab_url,
        private_token=gitlab_token,
        timeout=min(api_timeout, 10),
        max_retries=0,
    )
    run: _Enrichment | None = None
    try:
        async with async_session_ctx() as db:
            run = _Enrichment(db, client, job_id)
            users_to_enrich = list(
                (
                    await db.execute(
                        select(User)
                        .where(
                            or_(
                                User.email.is_(None),
                                User.email == "PRIVATE",
                                User.full_name.is_(None),
                                User.gitlab_user_id.is_(None),
                            ),
                        )
                        .limit(5000)
                    )
                )
                .scalars()
                .all()
            )
            run.total = len(users_to_enrich) or 1
            run.status("running", f"Enriching: 0/{run.total}")
            await run.raise_if_cancelled()
            if users_to_enrich:
                await run.run(users_to_enrich, run.user, "user", progress=True)
                await db.flush()
            await run.raise_if_cancelled()

            await _students_from_users(db)
            run.status("completed", run.message())
            await run.raise_if_cancelled()

            students_to_enrich = list(
                (await db.execute(select(Student).where(_missing_details()).limit(5000)))
                .scalars()
                .all()
            )
            if students_to_enrich:
                await run.run(students_to_enrich, run.student, "student", progress=False)
                await run.raise_if_cancelled()
                await _users_from_students(db, students_to_enrich)

            roles_updated = await _sync_roles_from_config(db)
            await run.raise_if_cancelled()
            await db.commit()

        await _finish_enrichment_job(job_id, "completed", run.message(roles_updated))
        logger.info(
            "gitlab_enrichment_completed",
            total=run.total,
            names_enriched=run.names_enriched,
            emails_enriched=run.emails_enriched,
            roles_updated=roles_updated,
            errors=run.errors,
        )
        _enrichment_display_s = 30
        await asyncio.sleep(_enrichment_display_s)
        _clear_enrichment_status()

    except _EnrichmentCancelledError:
        cancel_msg = "Enrichment cancelled."
        if run is not None:
            run.status("cancelled", cancel_msg)
        await _finish_enrichment_job(job_id, "cancelled", None, cancel_msg)
        await asyncio.sleep(10)
        _clear_enrichment_status()
    except Exception as e:
        logger.exception("GitLab enrichment failed")
        fail_msg = f"Enrichment failed: {str(e)[:100]}"
        if run is not None:
            run.status("failed", fail_msg, total=0)
        else:
            _set_enrichment_status(
                status="failed",
                message=fail_msg,
                total=0,
                processed=0,
                names_enriched=0,
                emails_enriched=0,
                errors=0,
            )
        await _finish_enrichment_job(job_id, "failed", None, fail_msg)
    finally:
        with suppress(Exception):
            await client.close()

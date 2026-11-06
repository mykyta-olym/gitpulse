"""Email-enrichment helpers for GitLab group import.

Bulk-fills missing Student/User emails using DB-only cross-linking,
Arena KPI lookups, and the GitLab user API.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.user import User
from app.services.gitlab.client import GitLabClient
from app.services.gitlab_import.normalize import _normalize_optional

logger = structlog.get_logger(__name__)


async def _enrich_user_emails_from_students(db: AsyncSession) -> None:
    """Fast DB-only enrichment: copy emails from Student records to User records.

    The reverse of ``_enrich_student_emails_fast``.  When User records
    are created during member sync with null/PRIVATE emails but the
    corresponding Student already has a real email (from Arena or
    GitLab API enrichment), this fills in the gap.
    """

    stmt = (
        select(User)
        .where(
            or_(User.email.is_(None), User.email == "PRIVATE", User.email == ""),
            User.gitlab_username.isnot(None),
        )
        .limit(5000)
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    if not users:
        return

    usernames = [u.gitlab_username for u in users if u.gitlab_username]
    if not usernames:
        return

    student_stmt = select(Student).where(Student.gitlab_username.in_(usernames))
    student_result = await db.execute(student_stmt)
    student_map = {s.gitlab_username: s for s in student_result.scalars().all()}

    enriched = 0
    for user in users:
        if not user.gitlab_username:
            continue
        student = student_map.get(user.gitlab_username)
        if not student:
            continue
        has_real = student.email and student.email != "PRIVATE"
        if has_real:
            user.email = student.email
            enriched += 1
        if not user.full_name and student.full_name:
            user.full_name = student.full_name

    await db.flush()
    if enriched:
        logger.info("Fast-enriched %d/%d user emails from student records", enriched, len(users))


async def _enrich_student_emails_fast(db: AsyncSession) -> None:
    """Fast DB-only enrichment: match student emails from OAuth user records."""

    stmt = (
        select(Student)
        .where(
            or_(
                Student.email.is_(None),
                Student.email == "PRIVATE",
                Student.email == "",
                Student.full_name.is_(None),
            )
        )
        .limit(5000)
    )
    result = await db.execute(stmt)
    students = list(result.scalars().all())
    if not students:
        return

    # Bulk-fetch all matching users in one query
    usernames = [s.gitlab_username for s in students if s.gitlab_username]
    if not usernames:
        return
    user_stmt = select(User).where(User.gitlab_username.in_(usernames))
    user_result = await db.execute(user_stmt)
    user_map = {u.gitlab_username: u for u in user_result.scalars().all()}

    enriched = 0
    for student in students:
        user = user_map.get(student.gitlab_username)
        if not user:
            continue
        is_missing = not student.email or student.email == "PRIVATE"
        has_real = user.email and user.email != "PRIVATE"
        if is_missing and has_real:
            student.email = user.email
            enriched += 1
        if not student.full_name and user.full_name:
            student.full_name = user.full_name

    await db.flush()
    if enriched:
        logger.info("Fast-enriched %d/%d student emails from user records", enriched, len(students))


async def _enrich_student_emails_arena(db: AsyncSession) -> None:
    """Bulk-enrich student emails via Arena KPI API.

    Runs as a dedicated pass with bounded concurrency so the Arena
    server is not overwhelmed.  Uses a shared httpx client for
    connection pooling.  Also propagates discovered emails to the
    corresponding User records.
    """
    import httpx as _httpx

    from app.config import get_settings as _gs
    from app.services.arena_email import lookup_email

    settings = _gs()
    if not settings.arena_email_api_enabled:
        return

    stmt = (
        select(Student)
        .where(
            or_(Student.email.is_(None), Student.email == "PRIVATE", Student.email == ""),
        )
        .limit(5000)
    )
    result = await db.execute(stmt)
    students = list(result.scalars().all())
    if not students:
        return

    # Pre-fetch User records for back-propagation
    usernames = [s.gitlab_username for s in students if s.gitlab_username]
    user_map: dict[str, Any] = {}
    if usernames:
        user_stmt = select(User).where(
            User.gitlab_username.in_(usernames),
            or_(User.email.is_(None), User.email == "PRIVATE", User.email == ""),
        )
        user_result = await db.execute(user_stmt)
        user_map = {u.gitlab_username: u for u in user_result.scalars().all() if u.gitlab_username}

    sem = asyncio.Semaphore(2)
    enriched = 0

    async with _httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
    ) as shared_client:

        async def _lookup_one(student: Student) -> None:
            nonlocal enriched
            try:
                async with sem:
                    email = await lookup_email(
                        student.gitlab_username,
                        settings,
                        client=shared_client,
                    )
                if email and "@" in email and email.lower() != "private":
                    student.email = email
                    enriched += 1
                    # Back-propagate to User record
                    user = user_map.get(student.gitlab_username)
                    if user and (not user.email or user.email == "PRIVATE"):
                        user.email = email
            except Exception:
                logger.debug("Arena lookup failed for %s", student.gitlab_username)

        tasks = [asyncio.ensure_future(_lookup_one(s)) for s in students if s.gitlab_username]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300,
            )
        except TimeoutError:
            logger.warning(
                "Arena enrichment timed out after 300s - %d/%d done",
                enriched,
                len(students),
            )

    await db.flush()
    if enriched:
        logger.info("Arena-enriched %d/%d student emails", enriched, len(students))


async def _enrich_user_emails_arena(db: AsyncSession) -> None:
    """Bulk-enrich User-record emails via Arena KPI API.

    Mirrors ``_enrich_student_emails_arena`` but targets the ``users``
    table so inherited members (who may not have Student records) also
    get their emails resolved.
    """
    import httpx as _httpx

    from app.config import get_settings as _gs
    from app.services.arena_email import lookup_email

    settings = _gs()
    if not settings.arena_email_api_enabled:
        return

    stmt = (
        select(User)
        .where(
            or_(User.email.is_(None), User.email == "PRIVATE", User.email == ""),
            User.gitlab_username.isnot(None),
        )
        .limit(5000)
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    if not users:
        return

    sem = asyncio.Semaphore(2)
    enriched = 0

    async with _httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
    ) as shared_client:

        async def _lookup_one(user: User) -> None:
            nonlocal enriched
            uname = user.gitlab_username
            if not uname:
                return
            try:
                async with sem:
                    email = await lookup_email(uname, settings, client=shared_client)
                if email and "@" in email and email.lower() != "private":
                    user.email = email
                    enriched += 1
            except Exception:
                logger.debug("Arena user lookup failed for %s", uname)

        tasks = [asyncio.ensure_future(_lookup_one(u)) for u in users if u.gitlab_username]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300,
            )
        except TimeoutError:
            logger.warning(
                "Arena user enrichment timed out after 300s - %d/%d done",
                enriched,
                len(users),
            )

    await db.flush()
    if enriched:
        logger.info("Arena-enriched %d/%d user emails", enriched, len(users))


async def _enrich_student_emails(
    db: AsyncSession,
    client: GitLabClient,
    on_progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> None:
    """Try to fill missing student emails and full names from GitLab user API.

    Uses concurrent API calls (bounded semaphore) for speed, and emits
    SSE progress events via *on_progress* so the import modal stays alive.
    """

    stmt = (
        select(Student)
        .where(
            or_(
                Student.email.is_(None),
                Student.email == "PRIVATE",
                Student.email == "",
                Student.full_name.is_(None),
            )
        )
        .limit(5000)
    )
    result = await db.execute(stmt)
    students_to_enrich = list(result.scalars().all())

    if not students_to_enrich:
        return

    total = len(students_to_enrich)
    logger.info("Enriching details for %d students (missing email or full_name)", total)

    def _email_missing(e: str | None) -> bool:
        return not e or e == "PRIVATE"

    # Strategy 1: Bulk match from the users table (single query)
    usernames = [s.gitlab_username for s in students_to_enrich if s.gitlab_username]
    user_map: dict[str, Any] = {}
    if usernames:
        user_stmt = select(User).where(User.gitlab_username.in_(usernames))
        user_result = await db.execute(user_stmt)
        user_map = {u.gitlab_username: u for u in user_result.scalars().all() if u.gitlab_username}

    for student in students_to_enrich:
        user = user_map.get(student.gitlab_username)
        if not user:
            continue
        if _email_missing(student.email) and not _email_missing(user.email):
            student.email = user.email
        if not student.full_name and user.full_name:
            student.full_name = user.full_name

    # Strategy 2: Concurrent GitLab API + Arena fallback for remaining
    still_missing = [
        s
        for s in students_to_enrich
        if (_email_missing(s.email) or not s.full_name) and s.gitlab_user_id is not None
    ]

    if still_missing:
        sem = asyncio.Semaphore(10)
        processed = 0

        async def _enrich_one(student: Any) -> None:
            nonlocal processed
            try:
                async with sem:
                    user_data = await asyncio.wait_for(
                        client.get_user(student.gitlab_user_id),
                        timeout=15,
                    )
                if user_data:
                    if _email_missing(student.email):
                        email = (
                            _normalize_optional(user_data.get("email"))
                            or _normalize_optional(user_data.get("public_email"))
                            or _normalize_optional(user_data.get("commit_email"))
                        )
                        if email:
                            student.email = email
                        else:
                            from app.config import get_settings as _gs
                            from app.services.arena_email import lookup_email

                            arena_email = await lookup_email(student.gitlab_username, _gs())
                            if arena_email:
                                student.email = arena_email
                            else:
                                student.email = "PRIVATE"
                        # Back-propagate to User record
                        if student.email and student.email != "PRIVATE":
                            user = user_map.get(student.gitlab_username)
                            if user and _email_missing(user.email):
                                user.email = student.email
                    if not student.full_name:
                        full_name = _normalize_optional(user_data.get("name"))
                        if full_name:
                            student.full_name = full_name
            except Exception:
                logger.debug("Could not fetch user %s from GitLab API", student.gitlab_username)
            finally:
                processed += 1

            # Emit progress every 5 students to keep SSE alive
            if on_progress and processed % 5 == 0:
                await on_progress(
                    {
                        "type": "stage",
                        "message": f"Enriching emails... ({processed}/{len(still_missing)})",
                    }
                )

        tasks = [asyncio.ensure_future(_enrich_one(s)) for s in still_missing]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=90,
            )
        except TimeoutError:
            logger.warning(
                "GitLab email enrichment timed out after 90s - %d/%d processed",
                processed,
                len(still_missing),
            )

    await db.flush()

    # Bulk cross-link enriched student data back to User records
    if usernames:
        user_stmt2 = select(User).where(User.gitlab_username.in_(usernames))
        user_result2 = await db.execute(user_stmt2)
        user_map2 = {u.gitlab_username: u for u in user_result2.scalars().all()}
        for student in students_to_enrich:
            user = user_map2.get(student.gitlab_username)
            if not user:
                continue
            if not _email_missing(student.email) and _email_missing(user.email):
                user.email = student.email
            if student.full_name and not user.full_name:
                user.full_name = student.full_name
        await db.flush()

    enriched_email = sum(1 for s in students_to_enrich if not _email_missing(s.email))
    enriched_name = sum(1 for s in students_to_enrich if s.full_name)
    logger.info(
        "Enriched %d/%d emails, %d/%d full_names",
        enriched_email,
        total,
        enriched_name,
        total,
    )

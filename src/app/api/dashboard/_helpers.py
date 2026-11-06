"""Shared helpers for dashboard routes."""

import asyncio
import json
import secrets
import uuid
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import Request, Response
from fastapi.templating import Jinja2Templates
from rq import Queue
from sqlalchemy import func, or_, select
from starlette.background import BackgroundTask

from app.compliance.check_registry import (
    CATEGORIES,
    CHECK_DEFS,
    CHECK_DEFS_MAP,
    CONFIGURABLE,
    DESCRIPTIONS,
    WEIGHT_FIELDS,
)
from app.config import get_settings
from app.dependencies import DbSession
from app.models.course_settings import CourseSettings
from app.models.student import Student
from app.redis_pool import get_redis as _pool_get_redis
from app.security.gitlab_oauth import GitLabUser

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


async def course_settings_for(
    db: DbSession, course_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, CourseSettings]:
    """The settings rows for these courses, loaded once per request.

    Three panels each issued the same
    `select(CourseSettings).where(course_id.in_(active_ids))` for the SAME ids
    on a single render - the deadline strip, the attention list and the
    student context - and this table accounted for seven of the dashboard's
    forty-six queries.

    SQLAlchemy's identity map holds the objects but still re-runs the
    statement, so the RESULT is what has to be kept. The session lives exactly
    one request, which makes its `.info` the right lifetime: nothing survives
    into the next render, so a settings change is never served stale.

    The mapping is shared, so callers read it and do not mutate it.
    """
    if not course_ids:
        return {}
    cache: dict[tuple[str, ...], dict[uuid.UUID, CourseSettings]] = db.info.setdefault(
        "course_settings_cache", {}
    )
    key = tuple(sorted(str(cid) for cid in course_ids))
    hit = cache.get(key)
    if hit is None:
        result = await db.execute(
            select(CourseSettings).where(CourseSettings.course_id.in_(course_ids))
        )
        hit = {cs.course_id: cs for cs in result.scalars().all()}
        cache[key] = hit
    return hit


async def people_by_name(
    db: DbSession, names: Sequence[str | None]
) -> dict[str, dict[str, object]]:
    """Role, service-account flag and avatar of the people behind these usernames.

    For a page that shows people as bare usernames - a ticket's submitter,
    its assignee, a comment's author - and should say what KIND of person each
    is, with the same badge User Management wears: Teacher, Admin, Student,
    Bot. A name is matched on either the GitPulse or the GitLab username,
    because tickets store whichever the writer had. One query for the page.
    Names the app does not know are simply absent.
    """
    from app.models.user import User

    wanted = {n for n in names if n}
    if not wanted:
        return {}
    rows = await db.execute(
        select(User.username, User.gitlab_username, User.role, User.is_bot, User.avatar_url).where(
            or_(User.username.in_(wanted), User.gitlab_username.in_(wanted))
        )
    )
    found: dict[str, dict[str, object]] = {}
    for username, gitlab_username, role, is_bot, avatar_url in rows.all():
        info: dict[str, object] = {
            "role": role or "student",
            "is_bot": bool(is_bot),
            "avatar_url": avatar_url or "",
        }
        for key in (username, gitlab_username):
            if key in wanted and key not in found:
                found[key] = info
    return found


# -- Canonical threshold defaults from DB model (never hardcode elsewhere) --
_DEFAULT_GREEN_THRESHOLD: float = CourseSettings.green_threshold.default.arg
_DEFAULT_YELLOW_THRESHOLD: float = CourseSettings.yellow_threshold.default.arg

# Safe ceiling for semester length when course settings are unavailable.
# TUKE FEI = 13 teaching weeks; exam period (skuskove obdobie) is tracked
# separately and never folded into this counter.
_DEFAULT_SEMESTER_WEEKS: int = 13

# Maximum allowed size for JSON configuration imports (bytes).
_MAX_CONFIG_IMPORT_BYTES: int = 2 * 1024 * 1024  # 2 MB


def _threshold_pcts(cs: CourseSettings | None) -> tuple[int, int]:
    """Return (green_pct, yellow_pct) as integers 0-100.

    Uses the course settings if available, otherwise falls back to
    the DB column defaults - no hardcoded magic numbers.
    """
    g = (cs.green_threshold if cs else _DEFAULT_GREEN_THRESHOLD) * 100
    y = (cs.yellow_threshold if cs else _DEFAULT_YELLOW_THRESHOLD) * 100
    return int(g), int(y)


def _semester_weeks_from_settings(cs: CourseSettings | None) -> int:
    """Derive semester length in **teaching** weeks from course settings.

    The ``_DEFAULT_SEMESTER_WEEKS`` (13) constant is the TUKE FEI floor:
    a teacher-configured ``weekly_deadlines`` array can only *extend* the
    semester past 13 weeks, never *shorten* it. Previously a course that
    had deadlines for only weeks 1..12 silently displayed a 12-week
    semester (and the Week N picker capped at 12) - this is wrong,
    because a teacher omitting a deadline for week 13 does not change
    the academic calendar.

    We deliberately do NOT bump the counter from ``get_current_week``
    either, because that confuses the regular teaching window with the
    post-semester exam period (``skuskove obdobie``) and silently inflates
    the Semester Week stat card from 13/13 -> 14/14 -> 15/15 ... as time
    passes.

    Returns ``_DEFAULT_SEMESTER_WEEKS`` (13) if no settings are available.
    """
    weeks = _DEFAULT_SEMESTER_WEEKS
    if not cs:
        return weeks
    # weekly_deadlines may extend (never shorten) the default.
    if cs.weekly_deadlines:
        try:
            wk_max = max(int(d.get("week", 0)) for d in cs.weekly_deadlines if isinstance(d, dict))
            if wk_max > weeks:
                weeks = wk_max
        except (ValueError, TypeError):
            pass
    return weeks


async def _course_data_staleness(
    db: "AsyncSession", course_id: uuid.UUID
) -> tuple[bool, datetime | None, int | None, int, int]:
    """Return freshness and current-week coverage for a course.

    A course is considered stale when at least one active group has no
    current-week team metric snapshot. This avoids the misleading old
    behavior where one fresh group sync could hide stale charts for the
    rest of the course, or individually synced groups could still show a
    whole-course "not synced" message.
    """

    from app.models.team import Team
    from app.models.team_metric_snapshot import TeamMetricSnapshot

    latest_at: datetime | None = None
    try:
        now = datetime.now(UTC)
        today = now.date()
        monday = today - timedelta(days=today.weekday())
        monday_start = datetime.combine(monday, datetime.min.time(), tzinfo=UTC)

        row = await db.execute(
            select(func.max(TeamMetricSnapshot.computed_at)).where(
                TeamMetricSnapshot.course_id == course_id
            )
        )
        latest_at = row.scalar_one_or_none()

        total_active_groups = int(
            await db.scalar(
                select(func.count(Team.id)).where(
                    Team.course_id == course_id,
                    Team.is_active.is_(True),
                )
            )
            or 0
        )
        current_week_groups = int(
            await db.scalar(
                select(func.count(func.distinct(TeamMetricSnapshot.team_id)))
                .join(Team, Team.id == TeamMetricSnapshot.team_id)
                .where(
                    Team.course_id == course_id,
                    Team.is_active.is_(True),
                    TeamMetricSnapshot.computed_at >= monday_start,
                )
            )
            or 0
        )
    except Exception:
        logger.debug("course_data_staleness_failed", exc_info=True)
        return True, None, None, 0, 0

    if latest_at is None:
        return True, None, None, 0, total_active_groups

    captured_date = latest_at.date()
    days_old = (today - captured_date).days
    is_stale = (
        current_week_groups < total_active_groups
        if total_active_groups > 0
        else captured_date < monday
    )
    return is_stale, latest_at, days_old, current_week_groups, total_active_groups


# Explicit re-export aliases for check registry constants.
# Consumer modules import these names from _helpers.
_R_CHECK_CATEGORIES = CATEGORIES
_R_CHECK_CONFIGURABLE = CONFIGURABLE
_R_CHECK_DESCRIPTIONS = DESCRIPTIONS
_R_CHECK_WEIGHT_FIELDS = WEIGHT_FIELDS

__all__ = [
    "CHECK_DEFS",
    "CHECK_DEFS_MAP",
    "_DEFAULT_GREEN_THRESHOLD",
    "_DEFAULT_SEMESTER_WEEKS",
    "_DEFAULT_YELLOW_THRESHOLD",
    "_MAX_CONFIG_IMPORT_BYTES",
    "_R_CHECK_CATEGORIES",
    "_R_CHECK_CONFIGURABLE",
    "_R_CHECK_DESCRIPTIONS",
    "_R_CHECK_WEIGHT_FIELDS",
    "_clear_enrichment_status",
    "_conflict_redirect",
    "_course_data_staleness",
    "_csrf_token",
    "_enqueue_or_inline",
    "_extended_checks",
    "_feature_disabled_response",
    "_format_time_ago",
    "_get_enrichment_status",
    "_get_redis",
    "_is_own_student_profile",
    "_not_found_response",
    "_parse_form_timestamp",
    "_redis_channel_listener",
    "_resolve_login_role_from_project_context",
    "_role_context",
    "_role_priority",
    "_save_oauth_state",
    "_semester_weeks_from_settings",
    "_set_enrichment_status",
    "_student_match_condition",
    "_sync_oauth_user_to_db",
    "_templates",
    "_threshold_pcts",
    "_try_start_enrichment",
    "_validate_oauth_state",
    "logger",
    "save_oauth_state",
    "validate_oauth_state",
]

# -- Enrichment progress tracking (Redis-backed for multi-worker) --
_ENRICH_KEY = "gp:enrichment_status"
_ENRICH_TTL = 600  # 10 min safety expiry


def _get_enrichment_status() -> dict[str, Any] | None:
    """Get current enrichment status from Redis (shared across workers)."""
    try:
        raw = _get_redis().get(_ENRICH_KEY)
        if raw:
            result: dict[str, Any] = json.loads(raw)
            return result
    except Exception:
        logger.debug("enrichment_status_read_failed", exc_info=True)
    return None


def _set_enrichment_status(
    status: str,
    message: str,
    total: int = 0,
    processed: int = 0,
    names_enriched: int = 0,
    emails_enriched: int = 0,
    errors: int = 0,
) -> None:
    """Set enrichment status in Redis + pub/sub for SSE streaming."""
    pct = round(processed / total * 100) if total > 0 else 0
    payload = {
        "status": status,
        "message": message,
        "total": total,
        "processed": processed,
        "percent": pct,
        "names_enriched": names_enriched,
        "emails_enriched": emails_enriched,
        "errors": errors,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    try:
        _get_redis().setex(_ENRICH_KEY, _ENRICH_TTL, json.dumps(payload))
    except Exception:
        logger.debug("enrichment_status_write_failed", exc_info=True)

    # Also publish to Redis pub/sub for SSE streaming
    try:
        from app.workers.progress import publish_progress

        publish_progress(
            job_id="enrichment",
            status=status,
            message=message,
            extra={
                "total": total,
                "processed": processed,
                "names_enriched": names_enriched,
                "emails_enriched": emails_enriched,
                "errors": errors,
                "percent": pct,
            },
            enrichment=True,
        )
    except Exception:
        logger.debug("sse_enrichment_broadcast_failed", exc_info=True)


def _clear_enrichment_status() -> None:
    """Clear enrichment status and lock from Redis."""
    try:
        r = _get_redis()
        r.delete(_ENRICH_KEY, f"{_ENRICH_KEY}:lock")
    except Exception:
        logger.debug("enrichment_status_clear_failed", exc_info=True)


def _try_start_enrichment() -> bool:
    """Atomically check if enrichment is idle and set to running.

    Uses Redis SETNX (SET NX) for atomic lock acquisition to prevent
    race conditions between concurrent callers.

    Returns True if lock was acquired (caller should proceed),
    False if enrichment is already running.
    """
    enrich_lock_key = f"{_ENRICH_KEY}:lock"
    try:
        r = _get_redis()
        # Atomic lock: SET NX with TTL - only succeeds if key doesn't exist
        acquired = r.set(enrich_lock_key, "1", nx=True, ex=_ENRICH_TTL)
        if not acquired:
            # Lock exists - check if enrichment is actually still running
            current_raw = r.get(_ENRICH_KEY)
            if current_raw:
                current = json.loads(current_raw)
                if current.get("status") == "running":
                    return False
            # Status is not "running" but lock exists (stale lock) - reclaim it
            # Use SET XX to atomically overwrite only if key exists
            r.set(enrich_lock_key, "1", xx=True, ex=_ENRICH_TTL)

        payload = {
            "status": "running",
            "message": "Starting GitLab enrichment...",
            "total": 0,
            "processed": 0,
            "names_enriched": 0,
            "emails_enriched": 0,
            "errors": 0,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        r.setex(_ENRICH_KEY, _ENRICH_TTL, json.dumps(payload))
        return True
    except Exception:
        logger.debug("enrichment_try_start_failed", exc_info=True)
        return True  # allow start if Redis is temporarily unavailable


async def _extended_checks(
    db: "AsyncSession",
    course_id: uuid.UUID | None,
) -> list[tuple[str, str, str]]:
    """Return CHECK_DEFS extended with active custom checks for the course."""
    if course_id is None:
        return list(CHECK_DEFS)

    from app.models.custom_check import CustomCheck

    stmt = (
        select(CustomCheck)
        .where(CustomCheck.course_id == course_id, CustomCheck.is_active.is_(True))
        .order_by(CustomCheck.sort_order, CustomCheck.check_code)
    )
    result = await db.execute(stmt)
    custom = result.scalars().all()
    extended: list[tuple[str, str, str]] = list(CHECK_DEFS)
    for cc in custom:
        extended.append((f"__custom__{cc.check_code}", cc.check_code, cc.name))
    return extended


def _format_time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'time ago' string."""
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    return dt.strftime("%b %d, %Y")


def _templates(request: Request) -> Jinja2Templates:
    from app.main import templates  # avoid circular import

    return templates


def _not_found_response(
    request: Request,
    entity_type: str,
    message: str | None = None,
    suggestion: str | None = None,
) -> Response:
    """Return the standard 404 error page for a missing (or hidden) entity.

    The same ``errors/error.html`` the exception handlers render, so a course
    that does not exist looks exactly like a route that does not exist - not a
    second, in-app "Course Not Found" card with its own layout. Access denials
    keep the 404 status on purpose: the page must not reveal that the entity
    exists.
    """
    from app.i18n import translate_text
    from app.middleware.error_pages import error_context

    locale = getattr(request.state, "locale", "sk")
    entity = translate_text(locale, entity_type)
    if not message:
        tail = translate_text(locale, "doesn't exist or may have been deleted.")
        message = f"{translate_text(locale, 'This')} {entity.lower()} {tail}"
    else:
        message = translate_text(locale, message)
    return _templates(request).TemplateResponse(
        request,
        "errors/error.html",
        {
            "request": request,
            # "Page not found" over a message that names the entity - GitLab's
            # wording for a missing project. "Kurz Nenájdené" glued a noun to a
            # neuter adjective.
            **error_context(
                404,
                message=message,
                suggestions=[translate_text(locale, suggestion)] if suggestion else [],
            ),
        },
        status_code=404,
    )


def _parse_form_timestamp(form: Any, field: str = "expected_updated_at") -> datetime | None:
    """Parse an ISO timestamp from a form field, returning ``None`` on failure."""
    raw = str(form.get(field, "")).strip()
    if not raw:
        return None
    with suppress(ValueError):
        return datetime.fromisoformat(raw)
    return None


def _conflict_redirect(redirect_url: str) -> Response:
    """Return a 303 redirect with ``?error=conflict`` for stale form POSTs."""
    sep = "&" if "?" in redirect_url else "?"
    return Response(
        status_code=303,
        headers={"Location": f"{redirect_url}{sep}error=conflict"},
    )


def _csrf_token(session_data: dict[str, str] | None = None, request: Request | None = None) -> str:
    """Generate CSRF token for template forms.

    For pre-login forms (no session), derives a UA + IP + day-rotating
    nonce so the token is tied to the requesting browser, network
    endpoint, and the current calendar day.  Must stay in sync with
    the matching derivation in ``app.dependencies.verify_csrf``.
    """
    settings = get_settings()
    if not settings.feature_security_hardening:
        return ""
    from app.security.csrf import generate_csrf_token

    if session_data is None:
        import hashlib as _hl
        from datetime import UTC as _UTC
        from datetime import datetime as _dt

        ua = request.headers.get("User-Agent", "unknown") if request else "unknown"
        ip = request.client.host if (request and request.client) else "unknown"
        day = _dt.now(_UTC).strftime("%Y%m%d")
        material = f"{ua}|{ip}|{day}|{settings.secret_key}".encode()
        nonce = _hl.sha256(material).hexdigest()[:32]
        # The CSRF token format is ``user:timestamp:signature``. Keep the
        # synthetic identity delimiter-free so parsing stays unambiguous.
        session_data = {"user": f"login_nonce-{nonce}"}
    return generate_csrf_token(session_data, settings.secret_key)


def _role_context(session_data: dict[str, str]) -> dict[str, Any]:
    """Get role-based context for templates."""
    role = session_data.get("role", "student")
    return {
        "user_role": role,
        "is_admin": role == "admin",
        "is_teacher": role in ("admin", "teacher"),
        "is_student": role == "student",
        "can_edit": role in ("admin", "teacher"),
        "username": session_data.get("user", ""),
        "gitlab_username": session_data.get("gitlab_username", ""),
        "avatar_url": session_data.get("avatar_url", ""),
        "full_name": session_data.get("full_name", ""),
        "theme_preference": session_data.get("theme_preference", "system"),
        # The rest of the preferences page. These are hydrated per request in
        # dependencies.py (and already re-validated there), so a template can
        # use them directly to set a class or pick a format.
        "accent_theme": session_data.get("accent_theme", "default"),
        "syntax_theme": session_data.get("syntax_theme", "dark"),
        "layout_width": session_data.get("layout_width", "fixed"),
        # Stored as "1"/"0" in the session (which is dict[str, str]); converted
        # back to a real bool here so a template can use it directly - "0" would
        # be TRUTHY in Jinja and would silently invert the setting.
        "keyboard_shortcuts_enabled": session_data.get("keyboard_shortcuts_enabled", "1") != "0",
        "default_homepage": session_data.get("default_homepage", "dashboard"),
        "first_day_of_week": session_data.get("first_day_of_week", "system"),
        "use_relative_times": session_data.get("use_relative_times", "1") != "0",
        "time_format": session_data.get("time_format", "system"),
        # "" (no override) reads as falsy in the template, which is exactly the
        # test base.html makes before emitting a custom property.
        "diff_color_removed": session_data.get("diff_color_removed", ""),
        "diff_color_added": session_data.get("diff_color_added", ""),
        "default_page_size": session_data.get("default_page_size", "50"),
        "sidebar_collapsed": session_data.get("sidebar_collapsed", "0") == "1",
        "default_period": session_data.get("default_period", "remembered"),
    }


def _student_match_condition(
    session_data: dict[str, str],
) -> Any:
    """Build SQLAlchemy OR condition matching the logged-in user to a Student.

    Matches by gitlab_user_id, gitlab_username, login username, and email
    for resilience against GitLab username renames or mismatches.
    """

    gitlab_username = session_data.get("gitlab_username", "")
    username = session_data.get("user", "")
    email = session_data.get("email", "")
    gitlab_user_id_str = session_data.get("gitlab_user_id", "")

    conditions = []
    if gitlab_user_id_str:
        with suppress(ValueError, TypeError):
            conditions.append(Student.gitlab_user_id == int(gitlab_user_id_str))
    if gitlab_username:
        conditions.append(Student.gitlab_username == gitlab_username)
    if username and username != gitlab_username:
        conditions.append(Student.gitlab_username == username)
    if email:
        conditions.append(Student.email == email)
    if not conditions:
        # Fallback - impossible match
        conditions.append(Student.gitlab_username == "")
    return or_(*conditions)


def _is_own_student_profile(
    student: Any,
    session_data: dict[str, str],
) -> bool:
    """Check if the logged-in user is viewing their OWN student profile."""
    gitlab_username = session_data.get("gitlab_username", "")
    username = session_data.get("user", "")
    email = session_data.get("email", "")
    s_gl = getattr(student, "gitlab_username", "") or ""
    s_email = getattr(student, "email", "") or ""

    if s_gl and s_gl in (gitlab_username, username):
        return True
    return bool(s_email and email and s_email == email)


# -- Auth pages --

# OAuth state storage in Redis for distributed state
_STATE_TTL = 900  # 15 minutes - enough for slow GitLab responses
_STATE_PREFIX = "oauth_state:"


def _get_redis() -> Any:
    """Get Redis connection backed by shared connection pool."""
    return _pool_get_redis()


def _save_oauth_state(state: str, *, next_url: str = "") -> bool:
    """Save OAuth state to Redis (synchronous, call via to_thread).

    *next_url* is an optional post-login redirect path stored alongside
    the state so the callback can send the user back to their original page.

    Returns ``True`` on success, ``False`` when Redis is unavailable.
    Callers must check the return value - a ``False`` result means the
    generated state was never stored, and any OAuth URL built from it will
    fail ``validate_oauth_state`` with a "session expired" error.
    """
    try:
        redis = _get_redis()
        value = next_url or "1"
        redis.setex(f"{_STATE_PREFIX}{state}", _STATE_TTL, value)
        return True
    except Exception as e:
        logger.warning("Failed to save OAuth state to Redis", error=str(e))
        return False


def _validate_oauth_state(state: str) -> bool | str:
    """Validate and consume OAuth state from Redis atomically.

    Uses GETDEL for atomic get-and-delete to prevent TOCTOU race
    condition where two concurrent callbacks could both validate
    the same state token (replay attack).

    Returns ``False`` on failure, or the stored redirect-URL string
    (which may be ``"1"`` if no redirect was saved).
    """
    try:
        redis = _get_redis()
        key = f"{_STATE_PREFIX}{state}"
        # GETDEL: atomic get + delete - prevents replay attacks
        result = redis.getdel(key)
        if result is None:
            return False
        return result.decode() if isinstance(result, bytes) else str(result)
    except AttributeError:
        # Fallback for older Redis versions without GETDEL
        try:
            redis = _get_redis()
            key = f"{_STATE_PREFIX}{state}"
            pipe = redis.pipeline(True)
            pipe.get(key)
            pipe.delete(key)
            results = pipe.execute()
            if results[0] is None:
                return False
            return results[0].decode() if isinstance(results[0], bytes) else str(results[0])
        except Exception:
            logger.warning("oauth_state_validation_failed", state=state[:8], exc_info=True)
            return False
    except Exception:
        logger.warning("oauth_state_validation_failed", state=state[:8], exc_info=True)
        return False


async def save_oauth_state(state: str, *, next_url: str = "") -> bool:
    """Async wrapper - run blocking Redis save in a thread.

    Returns ``True`` on success, ``False`` when Redis is unavailable.
    """
    return await asyncio.to_thread(_save_oauth_state, state, next_url=next_url)


async def validate_oauth_state(state: str) -> bool | str:
    """Async wrapper - run blocking Redis validation in a thread."""
    return await asyncio.to_thread(_validate_oauth_state, state)


# -- Lightweight Redis-based notifications --
_NOTIFY_PREFIX = "gp_notify:"
_NOTIFY_TTL = 60 * 60 * 24 * 30  # 30 days


def _push_notification(username: str, message: str, notif_type: str = "success") -> None:
    """Push a one-time notification for *username* (consumed on next page load)."""
    if not username:
        return
    redis = None
    try:
        redis = _get_redis()
        key = f"{_NOTIFY_PREFIX}{username}"
        redis.rpush(key, json.dumps({"message": message, "type": notif_type}))
        redis.expire(key, _NOTIFY_TTL)
    except Exception:
        logger.debug("push_notification_failed", username=username, exc_info=True)
    finally:
        if redis is not None:
            redis.close()


def _pop_notifications(username: str) -> list[dict[str, str]]:
    """Consume all pending notifications for *username*. Returns list of dicts."""
    if not username:
        return []
    redis = None
    try:
        redis = _get_redis()
        key = f"{_NOTIFY_PREFIX}{username}"
        pipe = redis.pipeline()
        pipe.lrange(key, 0, -1)
        pipe.delete(key)
        results = pipe.execute()
        raw_items: list[bytes | str] = results[0] if results else []
        notifications: list[dict[str, str]] = []
        for item in raw_items:
            with suppress(Exception):
                notifications.append(json.loads(item))
        return notifications
    except Exception:
        logger.debug("pop_notifications_failed", username=username, exc_info=True)
        return []
    finally:
        if redis is not None:
            redis.close()


class _EnqueueResult:
    """Return value of _enqueue_or_inline: background task + optional RQ job_id."""

    __slots__ = ("background", "job_id")

    def __init__(self, background: BackgroundTask | None = None, job_id: str | None = None):
        self.background = background
        self.job_id = job_id


def _enqueue_or_inline(
    settings: Any,
    rq_task_path: str,
    rq_args: tuple[Any, ...],
    inline_fn: Callable[[], Awaitable[None]],
) -> _EnqueueResult:
    """Enqueue an RQ job or fall back to inline BackgroundTask in dev mode.

    In development mode (no RQ worker), always runs inline.
    In production, attempts RQ enqueue with inline fallback on failure.
    Returns _EnqueueResult with optional job_id for SSE tracking.
    """
    if settings.is_development:
        return _EnqueueResult(background=BackgroundTask(inline_fn))
    try:
        conn = _pool_get_redis()
        try:
            q = Queue("default", connection=conn)
            job = q.enqueue(
                rq_task_path,
                *rq_args,
                job_timeout=settings.rq_default_timeout,
            )
            return _EnqueueResult(job_id=job.id if job else None)
        finally:
            pass  # pool manages connections
    except Exception:
        logger.warning("RQ unavailable - running %s inline", rq_task_path)
        return _EnqueueResult(background=BackgroundTask(inline_fn))


async def _sync_oauth_user_to_db(
    user: GitLabUser,
    role: str,
    secret_key: str,
    access_token: str = "",
    refresh_token: str = "",
    token_expires_at: datetime | None = None,
) -> tuple[bool, bool]:
    """Sync OAuth user to the users table for RBAC management.

    Creates a new user if not exists, or updates existing user's info.
    Returns (is_active, is_new_user).
    OAuth users don't have passwords - they use GitLab for auth.
    Also stores access_token and refresh_token for API calls and session refresh.
    Tokens are encrypted at rest via Fernet.
    """
    from app.db.session import async_session_ctx
    from app.models.user import User
    from app.security.token_encryption import encrypt_token

    try:
        async with async_session_ctx() as db:
            # Check if user exists by gitlab_username
            stmt = select(User).where(User.gitlab_username == user.username)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Update existing user - only fill empty email, but always sync
                # name and avatar from GitLab (source of truth for identity).
                if user.email and (not existing_user.email or existing_user.email == "PRIVATE"):
                    existing_user.email = user.email
                # Name and avatar always come from GitLab profile
                if user.name:
                    existing_user.full_name = user.name
                if user.avatar_url:
                    existing_user.avatar_url = user.avatar_url
                # Store GitLab numeric user ID if not already set
                if user.id is not None and not existing_user.gitlab_user_id:
                    existing_user.gitlab_user_id = user.id
                # Only upgrade role, never downgrade (admin stays admin)
                # Respect role_locked - admin override must not be reverted
                if (
                    _role_priority(role) > _role_priority(existing_user.role)
                    and not existing_user.role_locked
                ):
                    existing_user.role = role
                # Don't override is_active - admin deactivation must be respected
                # Store OAuth tokens (encrypted at rest)
                if access_token:
                    existing_user.gitlab_access_token = encrypt_token(access_token, secret_key)
                if refresh_token:
                    existing_user.gitlab_refresh_token = encrypt_token(refresh_token, secret_key)
                if token_expires_at:
                    existing_user.gitlab_token_expires_at = token_expires_at
                logger.info(
                    "oauth_user_updated",
                    username=user.username,
                    role=existing_user.role,
                    synced_name=user.name,
                    synced_email=user.email or "(empty)",
                    has_refresh_token=bool(refresh_token),
                    is_active=existing_user.is_active,
                )
                return existing_user.is_active, False
            # Create new user (no password for OAuth users)
            new_user = User(
                username=user.username,
                full_name=user.name or None,
                email=user.email or None,  # Convert empty string to None
                avatar_url=user.avatar_url or None,
                password_hash=f"oauth:{secrets.token_hex(32)}",  # Placeholder, not usable
                role=role,
                is_active=True,
                gitlab_username=user.username,
                gitlab_user_id=user.id or None,
                gitlab_access_token=(
                    encrypt_token(access_token, secret_key) if access_token else None
                ),
                gitlab_refresh_token=(
                    encrypt_token(refresh_token, secret_key) if refresh_token else None
                ),
                gitlab_token_expires_at=token_expires_at,
            )
            db.add(new_user)
            logger.info(
                "oauth_user_created",
                username=user.username,
                role=role,
                synced_name=user.name,
                synced_email=user.email or "(empty)",
                has_refresh_token=bool(refresh_token),
            )
            return True, True  # New users are always active
    except Exception:
        logger.exception("oauth_user_sync_failed", username=user.username)
        raise


def _role_priority(role: str) -> int:
    """Get numeric priority for role comparison (higher = more privileges)."""
    priorities = {"student": 0, "teacher": 2, "admin": 3}
    return priorities.get(role, 0)


async def _resolve_login_role_from_project_context(
    db: DbSession,
    *,
    gitlab_username: str,
    oauth_role: str,
) -> str:
    """Refine OAuth-derived role using imported course/project data.

    Priority:
    1. Keep OAuth admin/teacher assignments.
    2. Upgrade to teacher if user is listed as course teacher in imported courses.
    3. Upgrade to stored RBAC user role (if higher).
    4. Keep default (student) otherwise.
    """
    effective_role = oauth_role

    # Check CourseMembership: if user has any staff role (teacher+) in any course -> teacher.
    from app.models.course_membership import CourseMembership
    from app.models.user import User

    user_stmt = select(User).where(User.gitlab_username == gitlab_username).limit(1)
    user_result = await db.execute(user_stmt)
    db_user = user_result.scalar_one_or_none()

    if db_user:
        # If admin has locked this user's role, return it immediately
        # without any auto-detection overrides.
        if db_user.role_locked:
            return db_user.role

        cm_stmt = (
            select(CourseMembership.id)
            .where(
                CourseMembership.user_id == db_user.id,
                CourseMembership.role.in_(("owner", "teacher")),
            )
            .limit(1)
        )
        cm_result = await db.execute(cm_stmt)
        if cm_result.scalar_one_or_none() is not None and _role_priority(
            "teacher",
        ) > _role_priority(effective_role):
            effective_role = "teacher"

    # Respect explicit DB role assignments (e.g., admin override).
    db_role = db_user.role if db_user else None
    if db_role and _role_priority(db_role) > _role_priority(effective_role):
        effective_role = db_role

    return effective_role


# -- Shared Redis pub/sub listener for SSE streams --


async def _redis_channel_listener(
    channels: str | list[str],
    queue: "asyncio.Queue[dict[str, Any]]",
) -> None:
    """Listen on one or more Redis pub/sub channels, pushing JSON messages to *queue*.

    Shared implementation used by SSE endpoints across dashboard modules.
    Always runs as a background ``asyncio.Task``.
    """
    chan_list = [channels] if isinstance(channels, str) else channels
    try:
        conn = _pool_get_redis()
        pubsub = conn.pubsub()
        for ch in chan_list:
            pubsub.subscribe(ch)
        try:
            while True:
                message = await asyncio.to_thread(pubsub.get_message, timeout=2)
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        queue.put_nowait(data)
                    except (json.JSONDecodeError, asyncio.QueueFull):
                        pass
                await asyncio.sleep(0.1)
        finally:
            for ch in chan_list:
                pubsub.unsubscribe(ch)
            pubsub.close()
            conn.close()
    except Exception:
        logger.debug("redis_channel_listener_ended", channels=chan_list)


# -- Feature-disabled response helper --


def _feature_disabled_response(
    request: Request,
    feature_name: str,
    message: str,
    config_hint: str | None,
    **extra_context: Any,
) -> Response:
    """Return a ``feature_disabled.html`` template response."""
    ctx: dict[str, Any] = {
        "request": request,
        "feature_name": feature_name,
        "message": message,
        "config_hint": config_hint,
        "csrf_token": _csrf_token(),
        **extra_context,
    }
    return _templates(request).TemplateResponse(
        request,
        "feature_disabled.html",
        ctx,
    )

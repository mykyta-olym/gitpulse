"""FastAPI dependency injection providers."""

import asyncio
import functools
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from redis import Redis as SyncRedis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import async_session_ctx
from app.i18n import (
    LOCALE_COOKIE_NAME,
    LOCALE_QUERY_PARAM,
    _current_locale_var,
    normalize_locale,
)
from app.security.bearer_auth import verify_bearer_token
from app.security.session_auth import get_boot_nonce, get_current_session

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)

# Exactly "#RRGGBB". These values reach a style attribute, so the check that
# lets them through has to be the strict one.
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def _choice_allowlists() -> dict[str, tuple[set[str], str]]:
    """Allowed values and the fallback for every "choice" preference.

    Read from the SAME field table the preferences endpoint validates against,
    so hydration and saving can never disagree about what is offerable. They
    already had, silently and in both directions: the hand-written copy that
    used to live in ``_hydrate`` never listed ``syntax_theme``'s "light" or
    "dark", so choosing either saved and then reverted on the next request, and
    ``default_homepage``'s copy still named "courses" and "activity" - options
    that are not offered - while dropping every real one but "dashboard".

    The import is deferred because ``app.api.dashboard.preferences`` imports
    this module at import time.
    """
    from app.api.dashboard.preferences import PREFERENCE_FIELDS

    return {
        field.name: ({choice.value for choice in field.choices}, field.default)
        for field in PREFERENCE_FIELDS
        if field.kind == "choice"
    }


# -- Settings --
SettingsDep = Annotated[Settings, Depends(get_settings)]


# -- Database Session --
async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a cancellation-safe async database session.

    Uses :func:`async_session_ctx` which shields rollback/close with
    ``anyio.CancelScope(shield=True)``.  This prevents the
    *"garbage collector cleaning up non-checked-in connection"* leak
    when ``CancelledError`` from Starlette's middleware cancel-scope
    interrupts DI cleanup on client disconnect.
    """
    async with async_session_ctx() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


# -- Session validation (central helper) --


def _validate_session(request: Request, settings: Settings) -> dict[str, str] | None:
    """Read + validate the session cookie, including boot-nonce check.

    Returns the session data dict, or ``None`` when the session is
    missing, expired, tampered, or belongs to a previous server process
    or a different deployment.
    """
    session_data = get_current_session(
        request,
        settings.secret_key,
        max_age=settings.session_max_age_seconds,
        app_base_url=settings.app_base_url,
        session_absolute_max_age=settings.session_absolute_max_age_seconds,
    )
    if session_data is None:
        return None
    # Unless persistent_sessions is on, reject cookies from a prior boot
    if not settings.persistent_sessions and session_data.get("bn") != get_boot_nonce():
        logger.info(
            "session_rejected_boot_nonce user=%s cookie_nonce=%s",
            session_data.get("user"),
            session_data.get("bn", "<missing>"),
        )
        return None
    # Reject sessions from a different deployment (defence-in-depth)
    if not settings.persistent_sessions:
        from app.build_info import BUILD_HASH

        session_av = session_data.get("av", "")
        if session_av and session_av != BUILD_HASH:
            logger.info(
                "session_rejected_build_hash user=%s session_av=%s current_av=%s",
                session_data.get("user"),
                session_av,
                BUILD_HASH,
            )
            return None
    return session_data


# -- Auth helpers --


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


def _validate_bearer_token(token: str, settings: Settings) -> str:
    """Validate a bearer token - shared or per-user.

    Returns 'api_token' for the shared token. For per-user tokens, returns
    'api_token' but the caller should use _validate_bearer_token_with_role
    for role-aware checking.
    """
    if verify_bearer_token(token, settings.teacher_api_token):
        return "api_token"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API token",
    )


async def _validate_per_user_token(token: str, db_session: Any) -> dict[str, str] | None:
    """Check token against per-user API tokens table.

    Returns {"auth_method": "per_user_token", "role": ..., "user_id": ..., "token_id": ...}
    or None if no match.
    """

    from app.models.user_api_token import UserApiToken, verify_api_token

    # Optimisation: check prefix to narrow candidates.
    # Tokens start with "gp_" so we can filter by prefix match.
    token_prefix = token[:10] if len(token) >= 10 else token
    stmt = select(UserApiToken).where(
        UserApiToken.is_active.is_(True),
        UserApiToken.token_prefix == token_prefix,
    )
    result = await db_session.execute(stmt)
    candidates = list(result.scalars().all())

    for candidate in candidates:
        # Check expiry
        if candidate.expires_at and candidate.expires_at < datetime.now(UTC):
            continue
        # Verify bcrypt hash
        if verify_api_token(token, candidate.token_hash):
            # Update last_used_at (fire-and-forget, don't block auth)
            candidate.last_used_at = datetime.now(UTC)
            await db_session.merge(candidate)
            # Don't commit here - let the request lifecycle handle it
            return {
                "auth_method": "per_user_token",
                "role": candidate.token_role,
                "user_id": str(candidate.user_id),
                "token_id": str(candidate.id),
            }

    return None


def _check_required_roles(
    session_data: dict[str, str],
    *,
    settings: Settings,
    allowed_roles: tuple[str, ...] | None,
    forbidden_detail: str,
) -> None:
    if allowed_roles is None or not settings.feature_rbac:
        return
    user_role = session_data.get("role", "student")
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=forbidden_detail,
        )


async def _require_api_auth_common(
    request: Request,
    settings: Settings,
    *,
    missing_auth_detail: str,
    allowed_roles: tuple[str, ...] | None = None,
    forbidden_detail: str = "Forbidden",
) -> str:
    bearer_token = _extract_bearer_token(request)
    if bearer_token is not None:
        # Try shared teacher API token first (fast, no DB hit)
        try:
            _validate_bearer_token(bearer_token, settings)
        except HTTPException:
            # Shared token didn't match - try per-user tokens
            per_user = None
            try:
                async with async_session_ctx() as db:
                    per_user = await _validate_per_user_token(bearer_token, db)
            except Exception:
                logger.warning("per-user token DB lookup failed", exc_info=True)
            if per_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API token",
                ) from None
            # Per-user token matched - check role
            if (
                allowed_roles is not None
                and settings.feature_rbac
                and per_user["role"] not in allowed_roles
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=forbidden_detail,
                ) from None
            return "per_user_token"

        # Shared bearer token matched - check role
        if allowed_roles is not None and settings.feature_rbac:
            bearer_role = settings.teacher_api_token_role
            if bearer_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=forbidden_detail,
                )
        return "api_token"

    session_data = _validate_session(request, settings)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=missing_auth_detail,
        )

    _check_required_roles(
        session_data,
        settings=settings,
        allowed_roles=allowed_roles,
        forbidden_detail=forbidden_detail,
    )
    return "session"


def _dashboard_login_redirect(request: Request | None = None) -> HTTPException:
    location = "/dashboard/login"
    # Preserve the original URL so user returns to it after login
    if request is not None:
        path = request.url.path
        if path and path != "/dashboard/login" and path != "/dashboard/":
            from urllib.parse import quote

            location = f"/dashboard/login?next={quote(path, safe='/:@!$&()*+,;=-._~')}"
    return HTTPException(
        status_code=status.HTTP_302_FOUND,
        headers={"Location": location},
    )


#: Usernames this process has already attempted the one-shot backfill for.
#: A restart retries them, which is the right amount of retrying for a repair
#: that has nothing to do once it has run.
_BACKFILL_TRIED: set[str] = set()


def _require_dashboard_session(request: Request, settings: Settings) -> dict[str, str]:
    session_data = _validate_session(request, settings)
    if session_data is None:
        raise _dashboard_login_redirect(request)

    # NOTE: Allowlist-based role elevation is handled in _enforce_db_role()
    # which has DB access to check role_locked.  Doing it here caused
    # infinite login loops when an admin-locked role conflicted with
    # the allowlist (the session was re-elevated every request).

    # Backfill gitlab_user_id in DB if session carries the value but DB doesn't.
    #
    # ONCE per user per process. This is a repair for sessions minted before
    # login started writing the id, and it was firing on EVERY dashboard
    # request: each one opened its own session (a second pool connection while
    # the request already held one) and wrote the same row. The dashboard opens
    # five fragments at once - stats, badges, attention items, activity,
    # notifications - so five writes raced for the same row lock, five times per
    # page. Measured on production during one such burst: the UPDATE took
    # 36 417ms, `/dashboard/stats` took 128 965ms, and two other requests spent
    # 107 SECONDS without ever being handed a connection (`db=0ms q=0` in the
    # request log). The pool was full of requests waiting on each other.
    #
    # The mark goes down BEFORE the task is scheduled, so a burst of parallel
    # fragments schedules one task between them rather than one each.
    gitlab_user_id_str = session_data.get("gitlab_user_id", "") or session_data.get("user_id", "")
    gl_user = session_data.get("gitlab_username", "")
    if (
        gitlab_user_id_str
        and gl_user
        and gitlab_user_id_str.isdigit()
        and gl_user not in _BACKFILL_TRIED
    ):
        _BACKFILL_TRIED.add(gl_user)
        # Fire-and-forget DB backfill: create_task is the modern replacement
        # for ensure_future and integrates with the running event loop's
        # task tracking. The done-callback below logs any exception so
        # silent swallowing doesn't mask real errors.
        try:
            _task = asyncio.create_task(_backfill_gitlab_user_id(gl_user, int(gitlab_user_id_str)))
        except RuntimeError:
            # No running loop (rare - e.g. called from sync test fixture);
            # skip the backfill silently.
            return session_data
        _task.add_done_callback(
            lambda t: (
                None
                if t.cancelled()
                else (
                    logger.debug("backfill_gitlab_user_id failed: %s", t.exception())
                    if t.exception()
                    else None
                )
            )
        )

    return session_data


async def _backfill_gitlab_user_id(gitlab_username: str, gitlab_user_id: int) -> None:
    """One-shot DB update: fill gitlab_user_id when it's NULL."""

    from app.models.user import User

    try:
        async with async_session_ctx() as db:
            await db.execute(
                update(User)
                .where(
                    User.gitlab_username == gitlab_username,
                    User.gitlab_user_id.is_(None),
                )
                .values(gitlab_user_id=gitlab_user_id)
            )
    except Exception:
        logger.debug("backfill_gitlab_user_id failed for %s", gitlab_username, exc_info=True)


# -- Auth: Bearer token for API --
async def require_api_auth(
    request: Request,
    settings: SettingsDep,
) -> str:
    """Verify Bearer token or Session cookie for API endpoints."""
    return await _require_api_auth_common(
        request,
        settings,
        missing_auth_detail="Missing or invalid authentication (Bearer token or Session cookie)",
    )


ApiAuth = Annotated[str, Depends(require_api_auth)]


# -- Auth: API with role check (Bearer token or Session with role) --
async def require_api_teacher_auth(
    request: Request,
    settings: SettingsDep,
) -> str:
    """Verify Bearer token OR Session cookie with teacher/admin role."""
    return await _require_api_auth_common(
        request,
        settings,
        missing_auth_detail="Missing or invalid authentication",
        allowed_roles=("admin", "teacher"),
        forbidden_detail="Requires teacher or admin role",
    )


ApiTeacherAuth = Annotated[str, Depends(require_api_teacher_auth)]


async def require_api_admin_auth(
    request: Request,
    settings: SettingsDep,
) -> str:
    """Verify Bearer token OR Session cookie with admin role."""
    return await _require_api_auth_common(
        request,
        settings,
        missing_auth_detail="Missing or invalid authentication",
        allowed_roles=("admin",),
        forbidden_detail="Requires admin role",
    )


ApiAdminAuth = Annotated[str, Depends(require_api_admin_auth)]


# -- Auth: Session for dashboard --


async def _enforce_db_role(
    session_data: dict[str, str],
    db: AsyncSession,
) -> None:
    """Synchronise session role with the DB and handle allowlist interactions.

    Handles four scenarios:
    1. Account deactivated -> force re-login.
    2. role_locked=True (admin explicitly set role) -> enforce DB role
       exactly; no allowlist or CourseMembership elevation.
    3. role_locked=False -> apply allowlist-based elevation (admin/teacher
       lists), then fall back to DB role.
    4. role_locked=False AND role==student -> elevate to teacher if user
       has a CourseMembership with owner/teacher role.
    """
    from app.models.user import User

    username = session_data.get("user")
    if not username:
        return
    result = await db.execute(
        select(
            User.role,
            User.is_active,
            User.role_locked,
            User.theme_preference,
            User.accent_theme,
            User.syntax_theme,
            User.layout_width,
            User.keyboard_shortcuts_enabled,
            User.default_homepage,
            User.preferred_language,
            User.first_day_of_week,
            User.use_relative_times,
            User.time_format,
            User.diff_color_removed,
            User.diff_color_added,
            User.default_page_size,
            User.sidebar_collapsed,
            User.notify_ticket_queue,
            User.default_period,
        ).where(User.username == username)
    )
    row = result.first()
    if row is None:
        return  # user not in DB yet (first login / dev mode)
    (
        db_role,
        db_active,
        role_locked,
        theme_preference,
        accent_theme,
        syntax_theme,
        layout_width,
        keyboard_shortcuts_enabled,
        default_homepage,
        preferred_language,
        first_day_of_week,
        use_relative_times,
        time_format,
        diff_color_removed,
        diff_color_added,
        default_page_size,
        sidebar_collapsed,
        notify_ticket_queue,
        default_period,
    ) = row
    # Every preference is re-validated here rather than trusted from the row.
    # A value that fell out of the allowed set (an older release wrote it, or a
    # DB was edited by hand) must degrade to the default, not reach a template
    # and render a broken class name.
    # The allowed values come from the SAME field table the POST endpoint
    # validates against, not from a second copy of each list kept here. The copy
    # had already drifted, in both directions and silently:
    #   - `syntax_theme` never listed "light" or "dark", so choosing either
    #     saved, then reverted to "default" on the very next request - the
    #     setting looked like it did nothing outside its own page.
    #   - `default_homepage` still listed "courses" and "activity", two names
    #     that are no longer offered, while dropping every real option except
    #     "dashboard" - so pinning Support or Users silently did nothing.
    _allowed = _choice_allowlists()
    # preferred_language is deliberately absent: NULL is a real value there
    # ("follow the browser") and it is handled on its own below.
    for _key, _stored in (
        ("theme_preference", theme_preference),
        ("accent_theme", accent_theme),
        ("syntax_theme", syntax_theme),
        ("layout_width", layout_width),
        ("default_homepage", default_homepage),
        ("first_day_of_week", first_day_of_week),
        ("time_format", time_format),
        ("default_page_size", default_page_size),
        ("default_period", default_period),
    ):
        _values, _fallback = _allowed[_key]
        session_data[_key] = _stored if _stored in _values else _fallback
    # session_data is dict[str, str]; a bool stored here would break that, and
    # "0" is TRUTHY in Jinja, which would silently invert the setting. Stored
    # as "1"/"0" and converted back in _role_context, which returns Any.
    session_data["keyboard_shortcuts_enabled"] = "0" if keyboard_shortcuts_enabled is False else "1"
    # NULL is meaningful: "follow the browser". It stays absent from the
    # session so the locale middleware keeps deciding.
    if preferred_language:
        session_data["preferred_language"] = preferred_language
    session_data["use_relative_times"] = "0" if use_relative_times is False else "1"
    session_data["sidebar_collapsed"] = "1" if sidebar_collapsed else "0"
    session_data["notify_ticket_queue"] = "1" if notify_ticket_queue else "0"
    # Re-validated for the same reason as the rest, and more sharply: these two
    # are interpolated into a style attribute in base.html, so a value that is
    # not exactly "#RRGGBB" must never get past this point.
    for _key, _value in (
        ("diff_color_removed", diff_color_removed),
        ("diff_color_added", diff_color_added),
    ):
        session_data[_key] = (
            _value if isinstance(_value, str) and _HEX_COLOR.fullmatch(_value) else ""
        )
    if not db_active:
        raise _dashboard_login_redirect()

    session_role = session_data.get("role")

    # -- Locked role: DB value is absolute truth --
    if role_locked:
        if db_role and session_role != db_role:
            logger.info(
                "role_locked_mismatch_logout session=%s db=%s user=%s",
                session_role,
                db_role,
                username,
            )
            raise _dashboard_login_redirect()
        # Admin explicitly set this role - honour it unconditionally.
        # No allowlist elevation, no CourseMembership elevation.
        session_data["role"] = db_role or session_role or "student"
        return

    # -- Role NOT locked - apply allowlist elevation --
    settings = get_settings()
    gl_user = session_data.get("gitlab_username", "")
    effective_role = db_role or session_role or "student"

    if gl_user:
        if gl_user in (settings.gitlab_admin_usernames or []):
            effective_role = "admin"
        elif gl_user in (settings.gitlab_teacher_usernames or []) and effective_role == "student":
            effective_role = "teacher"

    if effective_role != session_role:
        logger.info(
            "session_role_corrected session=%s effective=%s user=%s",
            session_role,
            effective_role,
            username,
        )
    session_data["role"] = effective_role

    # -- CourseMembership elevation (only when role is NOT locked) --
    # Course owners / teachers get teacher-level access.  This is a
    # course-granted privilege - it only affects the dashboard session.
    if session_data["role"] == "student":
        from app.models.course_membership import CourseMembership

        cm_result = await db.execute(
            select(CourseMembership.role)
            .join(User, CourseMembership.user_id == User.id)
            .where(
                User.username == username,
                CourseMembership.role.in_(["owner", "teacher"]),
            )
            .limit(1)
        )
        if cm_result.scalar_one_or_none():
            logger.info("course_membership_elevation user=%s", username)
            session_data["role"] = "teacher"


def _apply_account_locale(request: Request, session_data: dict[str, str]) -> None:
    """Let the account's language reach a device that has no locale cookie.

    The Preferences page promises these settings "travel with your account to
    every device you log in from", and every other one does - they are rendered
    onto <html> from the row loaded above. Language was the exception:
    `resolve_locale` consults the query param, then the `gp_lang` cookie, then
    Accept-Language, and never the account at all. Saving a language writes
    that cookie, so it worked on the device you changed it on and nowhere else
    - a new browser rendered Slovak while the Preferences form said English.

    The documented precedence is preserved exactly (see the comment in
    api/dashboard/preferences.py): an explicit switch still outranks the
    account, because this only fills in when NEITHER the query param nor the
    cookie said anything. `LocaleMiddleware` has already run by now, so this
    refines `request.state.locale` rather than racing it.
    """
    account = normalize_locale(session_data.get("preferred_language"))
    if not account:
        return
    if request.query_params.get(LOCALE_QUERY_PARAM) or request.cookies.get(LOCALE_COOKIE_NAME):
        return
    request.state.locale = account
    _current_locale_var.set(account)


def _apply_period_default(request: Request, session_data: dict[str, str]) -> None:
    """Hand the account's Default period to requested_period(), which every
    period-scoped page and its live refreshers already call with the request."""
    request.state.default_period = session_data.get("default_period", "remembered")


async def require_dashboard_auth(
    request: Request,
    settings: SettingsDep,
    db: DbSession,
) -> dict[str, str]:
    """Verify session cookie for dashboard. Returns session data dict."""
    session_data = _require_dashboard_session(request, settings)
    try:
        await _enforce_db_role(session_data, db)
    except HTTPException:
        raise  # re-raise login redirects (302) and role errors (403)
    except Exception:
        method = (request.method or "GET").upper()
        logger.warning(
            "enforce_db_role_failed_blocked user=%s method=%s",
            session_data.get("user"),
            method,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("Authentication backend temporarily unavailable. Please retry shortly."),
        ) from None
    _apply_account_locale(request, session_data)
    _apply_period_default(request, session_data)
    return session_data


DashboardAuth = Annotated[dict[str, str], Depends(require_dashboard_auth)]


# -- RBAC: Role-based dashboard auth --
def require_role(*roles: str) -> Callable[..., Awaitable[dict[str, str]]]:
    """Factory that returns a dependency requiring the session user to have one of the given roles.

    When FEATURE_RBAC is disabled, falls back to standard dashboard auth (any logged-in user).
    """

    async def _check(
        request: Request,
        settings: SettingsDep,
        db: DbSession,
    ) -> dict[str, str]:
        session_data = _require_dashboard_session(request, settings)
        await _enforce_db_role(session_data, db)
        _check_required_roles(
            session_data,
            settings=settings,
            allowed_roles=roles,
            forbidden_detail=f"Requires role: {', '.join(roles)}",
        )
        # The same account settings every other dashboard page applies: a
        # teacher or admin page skipped them, so the account's language did not
        # reach a device with no language cookie there.
        _apply_account_locale(request, session_data)
        _apply_period_default(request, session_data)
        return session_data

    return _check


TeacherAuth = Annotated[dict[str, str], Depends(require_role("admin", "teacher"))]
AdminAuth = Annotated[dict[str, str], Depends(require_role("admin"))]


# -- User dependencies by role --


async def _load_user_from_session(
    session_data: dict[str, str],
    db: AsyncSession,
) -> "User":

    from app.models.user import User

    username = session_data.get("user")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        user_id = session_data.get("user_id")
        gitlab_username = session_data.get("gitlab_username")
        if user_id:
            import uuid

            try:
                u_uuid = uuid.UUID(str(user_id))
                res_id = await db.execute(select(User).where(User.id == u_uuid))
                user = res_id.scalar_one_or_none()
            except (ValueError, TypeError):
                pass
        if user is None and gitlab_username:
            res_gl = await db.execute(select(User).where(User.gitlab_username == gitlab_username))
            user = res_gl.scalar_one_or_none()
        if user is None and username:
            from sqlalchemy import func

            res_ci = await db.execute(
                select(User).where(func.lower(User.username) == username.lower())
            )
            user = res_ci.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated",
        )
    return user


async def get_current_user(
    session_data: DashboardAuth,
    db: DbSession,
) -> "User":
    """Get the current authenticated User object from session."""
    return await _load_user_from_session(session_data, db)


async def get_current_teacher(
    session_data: TeacherAuth,
    db: DbSession,
) -> "User":
    """Get the current authenticated User with teacher or admin role."""
    return await _load_user_from_session(session_data, db)


async def get_current_admin(
    session_data: AdminAuth,
    db: DbSession,
) -> "User":
    """The current authenticated User, admin only.

    The teacher variant above is what every support route uses; clearing data
    is a narrower right than reading or answering it, so the purge asks for
    this one instead.
    """
    return await _load_user_from_session(session_data, db)


# -- CSRF protection --


async def verify_csrf(request: Request, settings: SettingsDep) -> None:
    """Verify CSRF token from form data or JSON body. No-op when feature disabled."""
    if not settings.feature_security_hardening:
        return
    from app.security.csrf import validate_csrf_token

    token = ""
    content_type = request.headers.get("content-type", "")

    # Header takes precedence (used for JSON APIs to avoid polluting strict
    # Pydantic schemas with extra="forbid").  Fallback to body for legacy
    # form posts and any caller that still embeds csrf_token in the payload.
    header_token = request.headers.get("X-CSRF-Token") or request.headers.get("x-csrf-token")
    if header_token:
        token = str(header_token)
    elif "application/json" in content_type:
        try:
            body = await request.json()
            token = str(body.get("csrf_token", ""))
        except (ValueError, TypeError, UnicodeDecodeError):
            pass  # malformed JSON -> token stays empty -> validation rejects
    else:
        form = await request.form()
        token = str(form.get("csrf_token", ""))

    # For authenticated endpoints, use session; for login, use nonce from token itself
    session_data = _validate_session(request, settings)
    if session_data is None:
        # Pre-login: derive a deterministic nonce that is bound to:
        #   1. User-Agent (one browser family)
        #   2. Client IP   (one network endpoint)
        #   3. A per-day server-side salt derived from SECRET_KEY,
        #      which automatically rotates the nonce daily - so a leaked
        #      token has at most ~24 h of usefulness even if UA + IP match.
        # This is still weaker than a true session-bound token, but the
        # combination of three factors makes it materially harder to forge
        # than the previous UA-only nonce.
        import hashlib as _hl
        from datetime import UTC as _UTC
        from datetime import datetime as _dt

        ua = request.headers.get("User-Agent", "unknown")
        ip = request.client.host if request.client else "unknown"
        # Day-grained rotation; secret_key prevents an attacker without
        # the key from precomputing nonces for any browser/IP.
        day = _dt.now(_UTC).strftime("%Y%m%d")
        material = f"{ua}|{ip}|{day}|{settings.secret_key}".encode()
        nonce = _hl.sha256(material).hexdigest()[:32]
        session_data = {"user": f"login_nonce-{nonce}"}
    # NOTE: previously we also accepted login_nonce tokens when the user had
    # a valid session cookie (stale login page).  Removed for security -
    # the user must re-render the login form to get a fresh CSRF token.

    if not validate_csrf_token(token, session_data, settings.secret_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed",
        )


CSRFCheck = Annotated[None, Depends(verify_csrf)]


# -- Rate limiting --


@functools.lru_cache(maxsize=1)
def _get_rate_limit_client(url: str) -> "SyncRedis[str]":
    """The shared Redis client for rate limiting - one per URL, created lazily."""
    return SyncRedis.from_url(
        url,
        decode_responses=True,
        socket_timeout=get_settings().redis_socket_timeout_seconds,
    )


async def check_rate_limit(request: Request, settings: SettingsDep) -> None:
    """Apply per-IP rate limiting. No-op when feature disabled or Redis unavailable."""
    if not settings.feature_security_hardening:
        return
    try:
        from app.security.rate_limit import RateLimiter

        max_rpm = settings.rate_limit_requests_per_minute

        def _check_sync(
            url: str,
            path: str,
            ip: str,
            limit: int,
        ) -> tuple[bool, int]:
            limiter = RateLimiter(_get_rate_limit_client(url), prefix="rl")
            return limiter.is_allowed(key=f"{path}:{ip}", max_requests=limit, window_seconds=60)

        client_ip = request.client.host if request.client else "unknown"
        allowed, _remaining = await asyncio.to_thread(
            _check_sync,
            str(settings.redis_url),
            request.url.path,
            client_ip,
            max_rpm,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception as exc:
        # AUTH-05: fail-closed in ALL environments.  If Redis is
        # unavailable we cannot enforce rate limits and silently letting
        # the request through opens the door to brute-force /
        # credential-stuffing attacks.  Previously dev/test was fail-open
        # which risked accidental exposure if a dev .env leaked to
        # production.  Unified to fail-closed everywhere.
        logger.error("rate_limit_unavailable_blocking", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting backend unavailable, request rejected.",
            headers={"Retry-After": "30"},
        ) from exc


RateLimitDep = Annotated[None, Depends(check_rate_limit)]


# -- Feature Flag Checks --


class FeatureDisabledError(HTTPException):
    """Raised when a feature flag is disabled."""

    def __init__(
        self,
        feature_name: str,
        feature_flag: str,
        expected_availability: str | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "feature_disabled",
                "feature_name": feature_name,
                "feature_flag": feature_flag,
                "message": f"The {feature_name} feature is currently disabled.",
                "expected_availability": expected_availability,
            },
        )
        self.feature_name = feature_name
        self.feature_flag = feature_flag
        self.expected_availability = expected_availability


def require_feature(
    feature_flag: str,
    feature_name: str,
    expected_availability: str | None = None,
) -> Callable[[Settings], None]:
    """Dependency factory to require a specific feature flag to be enabled.

    Usage:
        @router.get("/llm-analysis")
        async def llm_analysis(
            _: None = Depends(
                require_feature(
                    "feature_llm_suggestions", "LLM Suggestions", "Ask your admin"
                )
            ),
        ):
            ...
    """

    def checker(settings: SettingsDep) -> None:
        enabled = (
            settings.llm_analysis_enabled
            if feature_flag == "feature_llm_suggestions"
            else getattr(settings, feature_flag, False)
        )
        if not enabled:
            raise FeatureDisabledError(
                feature_name=feature_name,
                feature_flag=feature_flag.upper(),
                expected_availability=expected_availability,
            )

    return checker


# Pre-built feature dependencies
RequireLLMSuggestions = Annotated[
    None,
    Depends(
        require_feature(
            "feature_llm_suggestions", "LLM Analysis", "Ask your instructor or administrator"
        )
    ),
]

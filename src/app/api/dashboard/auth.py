"""Authentication and session routes."""

import asyncio
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select

from app.api.dashboard._helpers import (
    _csrf_token,
    _resolve_login_role_from_project_context,
    _sync_oauth_user_to_db,
    _templates,
    logger,
    save_oauth_state,
    validate_oauth_state,
)
from app.config import get_settings
from app.dependencies import (
    CSRFCheck,
    DashboardAuth,
    DbSession,
    RateLimitDep,
    _validate_session,
)
from app.i18n import (
    DEFAULT_LOCALE,
    normalize_locale,
    safe_redirect_target,
    set_locale_cookie,
)
from app.security.gitlab_oauth import GitLabOAuth, GitLabOAuthError
from app.security.session_auth import clear_session_cookie, create_session_cookie
from app.utils.constants import NO_LOGIN_HASH

router = APIRouter()
_THEME_PREFERENCES = frozenset({"light", "dark", "system"})


async def _login_error_response(
    request: Request,
    error: str,
    status_code: int = 400,
) -> Response:
    """Redirect to the login page carrying the error in a query parameter.

    Using a 303 redirect instead of rendering the login template inline at
    the callback URL ensures:

    * The browser address bar shows ``/dashboard/login``, so F5 / back+
      forward reloads the login UI cleanly without replaying the callback.
    * The login page handler always generates a *fresh* OAuth state, so the
      user can click "Sign in with GitLab" immediately without seeing
      "session expired" a second time.

    ``status_code`` is logged for diagnostics only - the wire status is
    always 303 to drive the browser through the redirect.
    """
    logger.warning(
        "login_error_redirect",
        error=error,
        original_status=status_code,
        path=str(request.url.path),
    )
    return Response(
        status_code=303,
        headers={"Location": f"/dashboard/login?error={quote_plus(error)}"},
    )


async def _render_login_page(request: Request) -> Response:
    """Render the login page.

    Always returns HTML with a "Sign in with GitLab" button when the
    visitor has no valid session.  We never auto-redirect the browser
    to GitLab without an explicit user click: silent OAuth round-trips
    surprise users, hide failure modes, and can produce intermediate
    "Redirecting..." interstitials on cross-origin hops.  One explicit
    click is the OAuth best practice.

    When the visitor already has a valid session (e.g. opened the
    login URL in a new tab while logged in elsewhere), we perform a
    plain internal 303 redirect to the dashboard or the requested
    ``next`` target.  This is a same-origin server redirect, *not* a
    silent OAuth round-trip - no third-party hop, no interstitial.
    """
    settings = get_settings()
    qp = request.query_params
    next_url = safe_redirect_target(request, qp.get("next", ""), fallback="")

    # Already-authenticated visitors should not see the login form.
    # Skip this shortcut when the URL carries diagnostic markers
    # (?error=, ?logged_out=1, ?lang=) so users can still observe
    # those messages immediately after a state change.
    if not any(k in qp for k in ("error", "logged_out", "lang")):
        existing_session = _validate_session(request, settings)
        if existing_session is not None:
            return Response(
                status_code=303,
                headers={"Location": next_url or "/dashboard/"},
            )

    if settings.gitlab_oauth_enabled and settings.gitlab_oauth_client_id:
        # Generate OAuth URL (wrapped in try/except - Redis may be down).
        # Only expose auth_url when the state was successfully persisted;
        # an unsaved state will always fail validate_oauth_state with
        # "session expired" at the callback.
        auth_url: str | None = None
        try:
            oauth = GitLabOAuth(settings)
            state = oauth.generate_state()
            saved = await save_oauth_state(state, next_url=next_url or "")
            if saved:
                auth_url = oauth.get_authorization_url(state)
            else:
                logger.warning("oauth_state_save_failed_redis_unavailable")
        except Exception:
            logger.warning("oauth_state_generation_failed", exc_info=True)

        # GitLab's auto_sign_in_with_provider: when the flag is on, skip the card
        # and go straight to GitLab OAuth. A visit carrying ?auto_sign_in=false -
        # which logout appends - always shows the card, so a just-signed-out user
        # is never bounced straight back in (GitLab's own re-login-loop guard). A
        # diagnostic marker (error / logged_out) also keeps the card so its
        # message can be read.
        if (
            settings.gitlab_oauth_auto_sign_in
            and auth_url
            and qp.get("auto_sign_in") != "false"
            and not any(k in qp for k in ("error", "logged_out"))
        ):
            return Response(status_code=303, headers={"Location": auth_url})

        ctx: dict[str, Any] = {
            "request": request,
            "oauth_enabled": bool(auth_url),
            "dev_mode": settings.debug,
            "rbac_enabled": settings.feature_rbac,
            "csrf_token": _csrf_token(request=request),
            "error": qp.get("error"),
            "logged_out": qp.get("logged_out") == "1",
            "gitlab_url": settings.gitlab_url,
        }
        if auth_url:
            ctx["oauth_url"] = auth_url
        if not auth_url and not settings.debug:
            ctx["error"] = ctx.get("error") or (
                "Authentication service temporarily unavailable. Please try again."
            )
        return _templates(request).TemplateResponse(
            request,
            "login.html",
            ctx,
            headers={"Cache-Control": "no-store"},
        )

    # Fallback: show manual login page (dev mode)
    return _templates(request).TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "oauth_enabled": False,
            "dev_mode": settings.debug,
            "rbac_enabled": settings.feature_rbac,
            "csrf_token": _csrf_token(request=request),
            "error": qp.get("error"),
            "logged_out": qp.get("logged_out") == "1",
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/login",
    response_class=HTMLResponse,
    name="login_page",
    operation_id="dashboard_login_page",
)
async def login_page(request: Request) -> Response:
    """Render the login page."""
    return await _render_login_page(request)


@router.head(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
    name="login_page_head",
)
async def login_page_head(request: Request) -> Response:
    """Serve HEAD /dashboard/login without creating a duplicate OpenAPI operation."""
    return await _render_login_page(request)


@router.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request, db: DbSession) -> Response:
    """Handle GitLab OAuth callback."""
    settings = get_settings()

    if not settings.gitlab_oauth_enabled:
        return await _login_error_response(
            request,
            "OAuth is not enabled",
            400,
        )

    # Per-IP rate limit (5 req/min) to blunt brute-force / token-replay
    # attempts against the callback.  Mirrors the pattern used for the
    # orphan webhook ingest in ``app/api/webhooks.py``.  Trust only
    # ``request.client.host`` - ProxyHeadersMiddleware has rewritten it
    # to the real client IP for trusted upstream proxies.
    if settings.feature_security_hardening:
        try:
            from app.redis_pool import get_redis as _get_redis
            from app.security.rate_limit import RateLimiter as _RateLimiter

            client_ip = request.client.host if request.client else ""
            if client_ip:
                _rl = _RateLimiter(_get_redis(), prefix="rl:oauth_cb")
                allowed, _ = _rl.is_allowed(key=client_ip, max_requests=5, window_seconds=60)
                if not allowed:
                    logger.warning("gitlab_oauth_callback_rate_limited", client_ip=client_ip)
                    return await _login_error_response(
                        request,
                        "Too many sign-in attempts. Please wait a minute and try again.",
                        429,
                    )
        except Exception:
            logger.warning("oauth_callback_rate_limit_unavailable", exc_info=True)
            if settings.is_production:
                return await _login_error_response(
                    request,
                    "Sign-in protection is temporarily unavailable. Please retry shortly.",
                    503,
                )

    # Validate state parameter (CSRF protection).
    # validate_oauth_state returns False on failure or the stored
    # redirect-URL string (e.g. "/dashboard/courses/123" or "1").
    state = request.query_params.get("state", "")
    state_result = await validate_oauth_state(state)
    if not state_result:
        logger.warning("gitlab_oauth_invalid_state", state=state[:10])
        return await _login_error_response(
            request,
            "Session expired or invalid. Please try signing in again.",
            400,
        )
    # Extract post-login redirect target from the state value
    _stored_next = state_result if isinstance(state_result, str) and state_result != "1" else ""

    # Check for error from GitLab
    error = request.query_params.get("error")
    if error:
        error_description = request.query_params.get("error_description", error)
        logger.warning("gitlab_oauth_error", error=error, description=error_description)
        return await _login_error_response(request, f"GitLab error: {error_description}", 400)

    # Exchange code for token
    code = request.query_params.get("code", "")
    if not code:
        return await _login_error_response(request, "Missing authorization code", 400)

    try:
        async with asyncio.timeout(settings.gitlab_api_timeout_seconds):
            oauth = GitLabOAuth(settings)
            token_resp = await oauth.exchange_code_for_token(code)
            user = await oauth.get_user_info(token_resp.access_token)
            groups = await oauth.get_user_groups(token_resp.access_token)
            role = oauth.determine_role(user, groups)
            effective_role = await _resolve_login_role_from_project_context(
                db,
                gitlab_username=user.username,
                oauth_role=role,
            )

        # Compute token expiry time
        token_expires_at = datetime.now(UTC) + timedelta(seconds=token_resp.expires_in)

        # Sync OAuth user to database for RBAC management (including tokens)
        user_is_active = True
        is_new_user = False
        try:
            user_is_active, is_new_user = await _sync_oauth_user_to_db(
                user,
                effective_role,
                secret_key=settings.secret_key,
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                token_expires_at=token_expires_at,
            )
        except Exception as sync_err:
            logger.warning("oauth_user_sync_failed", error=str(sync_err), username=user.username)
            # Don't fail login if sync fails

        # Block login for admin-deactivated users
        if not user_is_active:
            logger.warning("login_blocked_deactivated", username=user.username)
            return await _login_error_response(
                request, "Your account has been deactivated by an administrator.", 403
            )

        # Send welcome email on first login
        if is_new_user and user.email and user.email != "PRIVATE":
            try:
                from app.services.email_notifications import notify_welcome

                notify_welcome(
                    username=user.username,
                    role=effective_role,
                    to_email=user.email,
                    full_name=user.name,
                )
            except Exception:
                logger.warning("welcome_email_failed", username=user.username, exc_info=True)

        logger.info(
            "gitlab_oauth_login_success",
            username=user.username,
            user_id=user.id,
            role=effective_role,
            has_refresh_token=bool(token_resp.refresh_token),
            token_expires_in=token_resp.expires_in,
        )

        from app.build_info import BUILD_HASH

        # Redirect to the original page the user was trying to visit,
        # or the dashboard home with a welcome indicator.
        if _stored_next and safe_redirect_target(request, _stored_next, fallback=""):
            redirect_url = _stored_next
        elif is_new_user:
            redirect_url = "/dashboard/?login=1"
        else:
            redirect_url = "/dashboard/?welcome_back=1"
        response = Response(status_code=303, headers={"Location": redirect_url})
        create_session_cookie(
            response,
            settings.secret_key,
            user=user.username,
            role=effective_role,
            user_id=str(user.id),
            gitlab_username=user.username,
            gitlab_user_id=user.id,
            email=user.email,
            avatar_url=user.avatar_url,
            full_name=user.name,
            max_age=settings.session_max_age_seconds,
            app_base_url=settings.app_base_url,
            user_agent=request.headers.get("User-Agent", ""),
            build_hash=BUILD_HASH,
            allow_stateless_fallback=not settings.is_production,
        )
        return response

    except TimeoutError:
        logger.error("gitlab_oauth_timeout", msg="OAuth callback exceeded 30s")
        return await _login_error_response(
            request,
            "GitLab took too long to respond. Please try again.",
            504,
        )

    except GitLabOAuthError as e:
        logger.error("gitlab_oauth_login_failed", error=str(e))
        return await _login_error_response(request, f"Authentication failed: {e}", 401)

    except Exception:
        logger.exception("gitlab_oauth_unexpected_error")
        return await _login_error_response(
            request,
            "An unexpected error occurred during sign-in. Please try again.",
            500,
        )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, _rate: RateLimitDep, _csrf: CSRFCheck) -> Response:
    """Legacy login form handler - redirects to OAuth or handles dev login."""
    settings = get_settings()

    # Dev mode: allow login without OAuth (even if OAuth is enabled)
    if settings.debug:
        form = await request.form()
        username = str(form.get("username", "dev_user")).strip()[:100]
        role = form.get("role", "teacher")

        # Validate role
        if role not in ("teacher", "admin", "student"):
            role = "teacher"

        logger.info("dev_mode_login", username=username, role=role)

        # Sync dev user to users table so they appear in User Management
        user_id = "dev-0"
        dev_avatar_url: str | None = None
        dev_full_name = str(username)
        try:
            from app.db.session import async_session_ctx
            from app.models.user import User

            async with async_session_ctx() as db:
                result = await db.execute(select(User).where(User.username == str(username)))
                existing = result.scalar_one_or_none()
                if existing:
                    # Dev mode: always update role to match the requested one
                    existing.role = str(role)
                    existing.is_active = True
                    user_id = str(existing.id)
                    dev_avatar_url = existing.avatar_url
                    # A seeded user carries a real name; the greeting should show it.
                    dev_full_name = existing.full_name or str(username)
                else:
                    new_user = User(
                        username=str(username),
                        full_name=str(username),
                        email=f"{username}@dev.local",
                        password_hash=NO_LOGIN_HASH,
                        role=str(role),
                        is_active=True,
                        gitlab_username=str(username),
                    )
                    db.add(new_user)
                    await db.flush()
                    user_id = str(new_user.id)
        except Exception as sync_err:
            logger.warning("dev_user_sync_failed", error=str(sync_err))

        from app.build_info import BUILD_HASH

        response = Response(status_code=303, headers={"Location": "/dashboard/"})
        create_session_cookie(
            response,
            settings.secret_key,
            user=str(username),
            role=str(role),
            user_id=user_id,
            gitlab_username=str(username),
            email=f"{username}@dev.local",
            full_name=dev_full_name,
            avatar_url=dev_avatar_url,
            max_age=settings.session_max_age_seconds,
            app_base_url=settings.app_base_url,
            user_agent=request.headers.get("User-Agent", ""),
            build_hash=BUILD_HASH,
            allow_stateless_fallback=not settings.is_production,
        )
        return response

    if settings.gitlab_oauth_enabled:
        # Redirect to OAuth flow
        return Response(status_code=303, headers={"Location": "/dashboard/login"})

    # OAuth not enabled and not in debug mode - show error
    return _templates(request).TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "error": "OAuth authentication is required",
            "oauth_enabled": False,
            "csrf_token": _csrf_token(request=request),
        },
        status_code=400,
    )


@router.get("/session-check")
async def session_check(request: Request) -> JSONResponse:
    """Lightweight session validity check for client-side heartbeat.

    Returns 200 ``{"status":"ok","user":"...","v":"<build_hash>"}`` when session is valid.
    Returns 401 ``{"status":"expired"}`` when cookie is missing / invalid.
    No DB queries - only verifies the signed cookie.
    """
    from app.build_info import BUILD_HASH
    from app.security.session_auth import get_boot_nonce, get_current_session

    settings = get_settings()
    session_data = get_current_session(
        request,
        settings.secret_key,
        max_age=settings.session_max_age_seconds,
        app_base_url=settings.app_base_url,
        session_absolute_max_age=settings.session_absolute_max_age_seconds,
    )
    if session_data is None:
        return JSONResponse({"status": "expired"}, status_code=401)
    # Check boot nonce (rejects cookies from previous server process)
    if not settings.persistent_sessions and session_data.get("bn") != get_boot_nonce():
        return JSONResponse({"status": "expired"}, status_code=401)
    # Check build hash (rejects cookies from a different deployment)
    if not settings.persistent_sessions:
        session_av = session_data.get("av", "")
        if session_av and session_av != BUILD_HASH:
            return JSONResponse({"status": "expired"}, status_code=401)
    return JSONResponse(
        {
            "status": "ok",
            "user": session_data.get("user", ""),
            "v": BUILD_HASH,
        }
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout_confirmation(request: Request) -> Response:
    """Render a confirmation page without mutating the current session."""
    settings = get_settings()
    session_data = _validate_session(request, settings)
    return _templates(request).TemplateResponse(
        request,
        "logout.html",
        {
            "request": request,
            "csrf_token": _csrf_token(session_data, request=request),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/logout")
async def logout(request: Request, _csrf: CSRFCheck) -> Response:
    """Revoke the session after an explicit, CSRF-protected confirmation."""
    response = Response(
        status_code=303,
        headers={
            # auto_sign_in=false is GitLab's guard: with auto_sign_in on, it keeps
            # the just-signed-out user on the login card instead of bouncing them
            # straight back into OAuth (a logout -> auto-login loop).
            "Location": "/dashboard/login?logged_out=1&auto_sign_in=false",
            "Clear-Site-Data": '"cache"',
        },
    )
    clear_session_cookie(response, app_base_url=get_settings().app_base_url, request=request)
    return response


@router.get("/language/{locale}")
async def switch_language(
    request: Request,
    locale: str,
    next_url: str | None = Query(default=None, alias="next"),
) -> Response:
    """Switch UI language and redirect user back to current page."""
    normalized = normalize_locale(locale) or DEFAULT_LOCALE
    target = safe_redirect_target(
        request,
        next_url or request.headers.get("referer"),
        fallback="/dashboard/",
    )
    response = RedirectResponse(url=target, status_code=303)
    set_locale_cookie(
        response,
        normalized,
        secure=request.headers.get("X-Forwarded-Proto") == "https",
    )
    return response


# -- Appearance preference persistence ---------------------------------------


@router.post("/api/theme")
async def update_theme_preference(
    request: Request,
    _auth: DashboardAuth,
    db: DbSession,
    _csrf: CSRFCheck,
) -> Response:
    """Persist the current user's light, dark, or system preference."""
    from app.dependencies import get_current_user

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=400)

    preference = payload.get("preference") if isinstance(payload, dict) else None
    if not isinstance(preference, str) or preference not in _THEME_PREFERENCES:
        return Response(status_code=422)

    user = await get_current_user(_auth, db)
    if user.theme_preference != preference:
        user.theme_preference = preference
        await db.commit()

    return Response(status_code=204, headers={"Cache-Control": "no-store"})


# -- Tour seen persistence ----------------------------------------------------


@router.get("/api/tour/seen")
async def tour_seen_get(
    _auth: DashboardAuth,
    db: DbSession,
    _rl: RateLimitDep,
) -> JSONResponse:
    """Return the list of gp_tour_v2 localStorage keys already seen by this user.

    The tour engine calls this once per browser session (guarded by
    sessionStorage) to seed localStorage on new devices so tours completed
    elsewhere are not re-prompted.
    """
    from app.dependencies import get_current_user

    user = await get_current_user(_auth, db)
    try:
        keys: list[str] = json.loads(user.tour_seen) if user.tour_seen else []
    except (ValueError, TypeError):
        keys = []
    return JSONResponse({"keys": keys}, headers={"Cache-Control": "private, no-cache"})


_TOUR_KEY_RE = re.compile(r"^[\w.\-@:=+]{1,200}$")
_TOUR_KEY_MAX = 500


@router.post("/api/tour/seen")
async def tour_seen_post(
    request: Request,
    _auth: DashboardAuth,
    db: DbSession,
    _csrf: CSRFCheck,
) -> Response:
    """Append a single gp_tour_v2 localStorage key to the user's seen list.

    Body: ``{"key": "slug@role:completed:fp=12345678"}``

    Silently ignores duplicate keys and returns 204.
    Invalid / oversized payloads return 400 or 422.
    """
    from app.dependencies import get_current_user

    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    key = body.get("key", "") if isinstance(body, dict) else ""
    if not isinstance(key, str) or not _TOUR_KEY_RE.match(key):
        return Response(status_code=422)

    user = await get_current_user(_auth, db)
    try:
        keys: list[str] = json.loads(user.tour_seen) if user.tour_seen else []
    except (ValueError, TypeError):
        keys = []

    if key not in keys:
        if len(keys) >= _TOUR_KEY_MAX:
            # Drop oldest entries to stay within the cap
            keys = keys[-(_TOUR_KEY_MAX - 1) :]
        keys.append(key)
        user.tour_seen = json.dumps(keys)
        await db.commit()

    return Response(status_code=204)


@router.delete("/api/tour/seen")
async def tour_seen_delete(
    _auth: DashboardAuth,
    _csrf: CSRFCheck,
    db: DbSession,
    slug: str | None = Query(default=None),
) -> Response:
    """Clear server-side tour state for the current user.

    Called by ``GP.tour.reset()`` so a reset on one device propagates to
    others.  If ``?slug=dashboard_student`` is given, only keys that
    contain that slug string are removed; without the parameter all keys
    are cleared.
    """
    from app.dependencies import get_current_user

    if slug is not None and (not isinstance(slug, str) or len(slug) > 200):
        return Response(status_code=422)

    user = await get_current_user(_auth, db)
    if user.tour_seen:
        try:
            keys: list[str] = json.loads(user.tour_seen)
            if isinstance(keys, list):
                keys = [k for k in keys if slug not in k] if slug else []
                user.tour_seen = json.dumps(keys) if keys else None
                await db.commit()
        except (ValueError, TypeError):
            pass
    return Response(status_code=204)

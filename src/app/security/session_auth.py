"""Session-based authentication for the teacher dashboard.

Sessions are stateless signed cookies (itsdangerous). A per-boot nonce is
embedded so that a server restart automatically invalidates every session
unless ``PERSISTENT_SESSIONS=true`` (handy for local development with
``--reload``).

Security hardening:
- ``__Host-`` cookie prefix when Secure (browser-enforced: Secure + Path=/ + no Domain)
- User-Agent fingerprint binding to detect session theft
- HttpOnly + SameSite=Lax + Secure (HTTPS)
- HMAC-signed payload via itsdangerous
"""

import hashlib
import os
import re
import secrets
from datetime import UTC, datetime

import structlog
from fastapi import Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.observability.metrics import SESSION_STORE_FALLBACK_TOTAL
from app.security.session_store import (
    SessionStoreUnavailable,
    get_session_store,
)

logger = structlog.get_logger(__name__)

_SESSION_COOKIE_BASE = "gitpulse_session"
# fallback; callers should always pass settings.session_max_age_seconds
_DEFAULT_MAX_AGE = 30 * 24 * 3600


def _cookie_name(secure: bool) -> str:
    """Return session cookie name with ``__Host-`` prefix when secure.

    ``__Host-`` prefix is browser-enforced to require ``Secure``,
    ``Path=/``, and no ``Domain`` attribute - strongest cookie protection.
    """
    if secure:
        return f"__Host-{_SESSION_COOKIE_BASE}"
    return _SESSION_COOKIE_BASE


def _ua_fingerprint(user_agent: str) -> str:
    """Derive a short hash of the User-Agent *stable* parts for session binding.

    Only the browser family (Chrome / Firefox / Safari / Edge) and OS
    platform are hashed - version numbers are stripped so that routine
    browser auto-updates don't invalidate sessions.
    """
    stable = _extract_stable_ua(user_agent)
    return hashlib.sha256(stable.encode("utf-8", errors="replace")).hexdigest()[:16]


_UA_BROWSER_RE = re.compile(r"(Chrome|Firefox|Safari|Edg|OPR|Opera)[\s/]", re.IGNORECASE)
_UA_PLATFORM_RE = re.compile(r"(Windows|Macintosh|Linux|Android|iPhone|iPad)", re.IGNORECASE)


def _extract_stable_ua(user_agent: str) -> str:
    """Return a normalised ``<platform>|<browser>`` string.

    Returns ``"no_ua|no_ua"`` for empty or whitespace-only input so
    sessions created without a User-Agent header carry a distinct
    fingerprint - preventing a stolen cookie from being replayed
    from a client that omits the header entirely.
    """
    stripped = user_agent.strip() if user_agent else ""
    if not stripped:
        return "no_ua|no_ua"
    browser_match = _UA_BROWSER_RE.search(stripped)
    platform_match = _UA_PLATFORM_RE.search(stripped)
    browser = (browser_match.group(1) if browser_match else "Unknown").lower()
    platform = (platform_match.group(1) if platform_match else "Unknown").lower()
    return f"{platform}|{browser}"


# Cookie name shared by login, logout, middleware and browser clients.
SESSION_COOKIE_NAME = _SESSION_COOKIE_BASE

# -- Boot nonce ----------------------------------------------------------
# Sessions embed this value so that an unwanted boot can invalidate them.
#
# AUTH-07: when running with multiple Uvicorn workers each process would
# previously generate its own random nonce at module-import time, so every
# round-robin load-balanced request hit a worker with a *different* nonce
# and rejected the cookie -> infinite logout/login loop.  Derive the nonce
# from the deploy's ``GIT_SHA`` (set by redeploy.py in ``.env.production``)
# so all workers in the same deploy share it, but a new deploy still
# invalidates old sessions (which is the original intent).  Falls back to
# a per-process random value only when ``GIT_SHA`` is unset (local dev).


def _derive_boot_nonce() -> str:
    sha = os.environ.get("GIT_SHA", "").strip()
    if sha:
        return hashlib.sha256(sha.encode()).hexdigest()[:16]
    return secrets.token_hex(8)


_BOOT_NONCE: str = _derive_boot_nonce()


def get_boot_nonce() -> str:
    """Return the deploy-stable nonce shared across workers."""
    return _BOOT_NONCE


def _get_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key)


def create_session_cookie(
    response: Response,
    secret_key: str,
    user: str,
    role: str = "teacher",
    user_id: str | None = None,
    gitlab_username: str | None = None,
    gitlab_user_id: int | str | None = None,
    email: str | None = None,
    avatar_url: str | None = None,
    full_name: str | None = None,
    max_age: int = _DEFAULT_MAX_AGE,
    app_base_url: str = "http://localhost:8000",
    user_agent: str = "",
    build_hash: str = "",
    allow_stateless_fallback: bool = True,
) -> None:
    """Set a signed, HttpOnly session cookie on the response.

    Security features:
    - ``__Host-`` cookie prefix when HTTPS (browser-enforced constraints)
    - User-Agent fingerprint binding (detects session cookie theft)
    - ``HttpOnly`` (JS cannot access)
    - ``Secure`` when HTTPS
    - ``SameSite=Lax`` (CSRF protection)

    Args:
        response: FastAPI Response object
        secret_key: Secret key for signing
        user: Username to store in session
        role: User role (admin, teacher, student)
        user_id: Optional user ID (GitLab user ID or DB ID)
        gitlab_username: GitLab username for OAuth sessions
        email: User email address
        avatar_url: GitLab avatar URL
        full_name: User's full / display name
        max_age: Cookie max age in seconds
        app_base_url: Base URL to determine secure cookie flag
        user_agent: Browser User-Agent string for fingerprint binding
        build_hash: Deployment fingerprint - sessions with a different hash
            are rejected after redeploy (defence-in-depth alongside boot nonce)
        allow_stateless_fallback: When False, raise if the Redis session store
            is unavailable instead of issuing a stateless cookie.
    """
    serializer = _get_serializer(secret_key)
    data = {
        "user": user,
        "role": role,
        "user_id": user_id or "",
        "gitlab_username": gitlab_username or "",
        "gitlab_user_id": str(gitlab_user_id) if gitlab_user_id else "",
        "email": email or "",
        "avatar_url": avatar_url or "",
        "full_name": full_name or "",
        "ts": datetime.now(UTC).isoformat(),
        "bn": _BOOT_NONCE,  # ties cookie to this server process
        # AUTH-08: always bind UA fingerprint - even when UA is empty, the
        # fingerprint will be "no_ua|no_ua" so session replay from a client
        # that strips headers is still detected.
        "ua": _ua_fingerprint(user_agent),
        "av": build_hash,  # ties cookie to this deploy
    }

    # SEC #6 - Redis-backed sessions.  When the store is configured we
    # save the rich payload server-side and put a tiny opaque signed
    # identifier in the cookie. Production callers disable the stateless
    # fallback so a Redis outage cannot silently downgrade revocation.
    store = get_session_store()
    if store is not None:
        try:
            token = store.create(data, max_age=max_age)
        except SessionStoreUnavailable:
            if not allow_stateless_fallback:
                raise
            SESSION_STORE_FALLBACK_TOTAL.labels(reason="create_unavailable").inc()
            logger.warning(
                "session_store_unavailable_fallback_to_cookie",
                reason="create_unavailable",
            )
            token = serializer.dumps(data)
    else:
        if not allow_stateless_fallback:
            raise SessionStoreUnavailable("session store is not initialised")
        token = serializer.dumps(data)

    use_secure = app_base_url.startswith("https://")
    name = _cookie_name(use_secure)

    response.set_cookie(
        key=name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=use_secure,
        samesite="lax",
        path="/",
    )

    logger.info(
        "session_cookie_created",
        user=user,
        role=role,
        secure=use_secure,
        cookie_name=name,
        ua_bound=bool(user_agent),
    )


def get_current_session(
    request: Request,
    secret_key: str,
    max_age: int = _DEFAULT_MAX_AGE,
    *,
    app_base_url: str = "http://localhost:8000",
    enforce_ua: bool = True,
    session_absolute_max_age: int = 90 * 24 * 3600,
) -> dict[str, str] | None:
    """Validate session cookie and return session data, or ``None``.

    Checks:
    1. Cookie presence (tries ``__Host-`` prefixed name first, then fallback)
    2. HMAC signature validity (itsdangerous)
    3. Max-age expiry (sliding TTL)
    4. Absolute TTL - session ``ts`` claim vs *session_absolute_max_age*
    5. User-Agent fingerprint match (if ``ua`` claim present and *enforce_ua* is True)

    Args:
        enforce_ua: When True (default), reject sessions whose User-Agent
            fingerprint (platform + browser family) does not match the
            fingerprint stored at login time.  Set to False only for
            SSE/streaming endpoints where programmatic clients may omit
            the User-Agent header.
    """
    use_secure = app_base_url.startswith("https://")
    name = _cookie_name(use_secure)
    token = request.cookies.get(name)
    # Transitional fallback: try unprefixed name for cookies created before upgrade
    if not token and use_secure:
        token = request.cookies.get(_SESSION_COOKIE_BASE)
    if not token:
        # Only interesting when the browser HAS cookies but not ours: that means
        # a session was lost, or the cookie is scoped wrong (name/domain/secure
        # prefix). A visitor with no cookies at all is simply anonymous - the
        # normal state for the login page, static assets and health checks - and
        # logging it on every such request drowned real debug output.
        if request.cookies:
            logger.debug("session_cookie_missing", expected=name, present=sorted(request.cookies))
        return None

    # SEC #6 - try Redis-backed lookup first.  The store accepts both
    # legacy stateless tokens (rejects with bad signature -> falls
    # through to the itsdangerous path) and the new opaque signed sid.
    store = get_session_store()
    data: dict[str, str] | None = None
    if store is not None:
        store_data = store.load(token, max_age=max_age)
        if store_data is not None:
            # Coerce values to str - the rest of the auth code expects
            # ``dict[str, str]``; legacy callers stored everything as
            # str already.
            data = {k: str(v) if v is not None else "" for k, v in store_data.items()}
    if data is None:
        serializer = _get_serializer(secret_key)
        try:
            data = serializer.loads(token, max_age=max_age)
        except (BadSignature, SignatureExpired) as e:
            logger.warning("session_cookie_invalid", error=str(e))
            return None

    # Pyright: serializer.loads() returns Any - narrow to dict explicitly.
    if not isinstance(data, dict):
        return None

    # -- AUTH-06: Absolute TTL enforcement for stateless cookies --
    # The sliding ``max_age`` only bounds idle time - a session that is
    # used every 7 hours would renew indefinitely.  The ``ts`` claim
    # (written at login) provides a hard creation timestamp; reject the
    # session once it exceeds ``session_absolute_max_age`` regardless of
    # activity.  This matches the Redis session store's built-in TTL.
    ts_str = data.get("ts", "")
    if ts_str and session_absolute_max_age > 0:
        try:
            created_at = datetime.fromisoformat(ts_str)
            age_seconds = (datetime.now(UTC) - created_at).total_seconds()
            if age_seconds > session_absolute_max_age:
                logger.warning(
                    "session_absolute_ttl_exceeded",
                    user=data.get("user"),
                    age_hours=round(age_seconds / 3600, 1),
                    limit_hours=round(session_absolute_max_age / 3600, 1),
                )
                return None
        except (ValueError, TypeError, OSError):
            # Malformed ts - treat as expired for safety (fail-closed)
            logger.warning("session_ts_malformed", user=data.get("user"), ts=ts_str)
            return None

    # Validate User-Agent fingerprint (if present in session).
    # Only the browser family (Chrome/Firefox/etc.) and OS platform are
    # compared - version numbers are stripped so routine browser updates
    # do not invalidate sessions.
    # Behaviour is controlled by the SESSION_STRICT_UA_FINGERPRINT setting:
    #  * False (default): mismatch is logged but the session is kept, because
    #    SSE/multi-tab/mobile clients legitimately send slightly different UA
    #    strings and rejecting them produces too many false-positive logouts.
    #  * True: mismatch rejects the session (stronger protection against a
    #    leaked session cookie being replayed from a different browser).
    stored_ua = data.get("ua", "")
    if stored_ua and enforce_ua:
        current_ua = request.headers.get("User-Agent", "")
        if current_ua and _ua_fingerprint(current_ua) != stored_ua:
            try:
                from app.config import get_settings as _gs

                _strict = _gs().session_strict_ua_fingerprint
            except Exception:
                _strict = False
            if _strict:
                logger.warning(
                    "session_ua_mismatch_rejected",
                    user=data.get("user"),
                    stored=stored_ua[:8],
                    current=_ua_fingerprint(current_ua)[:8],
                )
                return None
            logger.info(
                "session_ua_mismatch_warning",
                user=data.get("user"),
                stored=stored_ua[:8],
                current=_ua_fingerprint(current_ua)[:8],
            )
    return data


def clear_session_cookie(
    response: Response,
    app_base_url: str = "http://localhost:8000",
    *,
    request: Request | None = None,
) -> None:
    """Remove the session cookie and revoke any server-side session.

    Clears both ``__Host-`` prefixed and unprefixed names to ensure
    logout works during cookie-name migration.  When ``request`` is
    supplied and a Redis-backed session store is configured, the
    server-side record is also deleted so a stolen cookie cannot be
    replayed even before the cookie expires.
    """
    use_secure = app_base_url.startswith("https://")
    name = _cookie_name(use_secure)

    # SEC #6 - best-effort server-side revocation.
    if request is not None:
        store = get_session_store()
        if store is not None:
            token = request.cookies.get(name)
            if not token and use_secure:
                token = request.cookies.get(_SESSION_COOKIE_BASE)
            if token:
                store.revoke(token)

    response.delete_cookie(
        key=name,
        path="/",
        httponly=True,
        secure=use_secure,
        samesite="lax",
    )
    # Also clear the unprefixed name for transitional cookies
    if use_secure:
        response.delete_cookie(
            key=_SESSION_COOKIE_BASE,
            path="/",
            httponly=True,
            secure=use_secure,
            samesite="lax",
        )

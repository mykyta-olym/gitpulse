"""Redis cache for the heavy content of the slow dashboard pages.

Six pages render their content - the aggregations below the page header -
from queries that take up to a few seconds on a populous course:

* **Course detail** (``GET /dashboard/courses/{id}``)
* **Course analytics** (``GET /dashboard/courses/{id}/analytics``)
* **Course activity monitor** (``GET /dashboard/courses/{id}/activity``)
  - teachers/admins only; students fall through to the per-user
  template path because their filtered view is already cheap.
* **Team detail** (``GET /dashboard/teams/{id}``)
* **Project detail** (``GET /dashboard/projects/{id}``)
* **Student-on-team detail** (``GET /dashboard/students/{id}/team/{team_id}``)

That content is the same HTML for every user at the same permission level,
so it is rendered once, cached in Redis (default 60s TTL) and inlined into
each viewer's full page by :func:`render_inline` - the whole page in one
response, as GitLab does.

Pages we intentionally do NOT cache:

* **Dashboard home** - heavily per-user (course filter, recent activity).
* **Admin users / Course teachers** - templates bake the viewer's
  username into "(you)" markers; rewriting that out is more risk than
  the cache saves.
* **Support form / Support tickets** - bodies contain a per-request
  unique token used to neutralise CSRF replay; not safe to share.

Correctness considerations
==========================

* **CSRF token isolation.** Tokens are bound to the requesting user
  (``{user}:{ts}:{hmac}`` - see :mod:`app.security.csrf`). Caching a
  rendered body verbatim would leak one user's token to another and
  break every subsequent POST. We work around this by rendering with
  :data:`CSRF_PLACEHOLDER` instead of the real token; on each cache hit
  :func:`personalize` substitutes the requesting user's fresh
  token.

* **CSP nonce isolation.** ``SecurityHeadersMiddleware`` emits a fresh
  per-response nonce. Cached bodies hold :data:`CSP_NONCE_PLACEHOLDER`
  instead of the real value; :func:`personalize` substitutes
  the per-request nonce so inline scripts validate against the response
  headers.

* **Personal field isolation.** Username, gitlab_username, avatar_url
  and full_name flow through :data:`PERSONAL_PLACEHOLDERS` so the
  topbar / sidebar / chrome that surrounds the cached fragment never
  bakes in another user's identity. Use :func:`cacheable_role_ctx`
  when building the template context.

* **Variant keys.** :func:`make_role_variant` folds locale, role flags
  and any caller-supplied extras (course-membership role, query
  filters, "is own profile") into a stable hash so different views
  cannot collide.

* **Invalidation.** TTL bounds staleness to 60s. For tighter freshness
  the write paths (webhook receive, sync / metrics job completion,
  course-settings save, manual config edits) call :func:`invalidate`
  or :func:`invalidate_cascade` to drop the affected scope eagerly.
  Over-invalidation is preferred to stale reads.

* **Failure mode.** All Redis operations are wrapped in
  ``suppress(Exception)`` - Redis being down or slow MUST NOT block
  the page; the builder runs as a normal fallback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from collections.abc import Iterable
from contextlib import suppress
from typing import Any, cast

from starlette.responses import Response

from app.redis_pool import get_redis

_log = logging.getLogger(__name__)


def _record_lookup(kind: str, hit: bool) -> None:
    """Bump Prometheus hit/miss counter. Never raises."""
    with suppress(Exception):
        from app.observability.metrics import PAGE_CACHE_HITS, PAGE_CACHE_MISSES

        (PAGE_CACHE_HITS if hit else PAGE_CACHE_MISSES).labels(kind=kind).inc()


def _record_invalidation(kind: str, removed: int) -> None:
    """Bump Prometheus invalidation counter by the number of keys removed."""
    if removed <= 0:
        return
    with suppress(Exception):
        from app.observability.metrics import PAGE_CACHE_INVALIDATIONS

        PAGE_CACHE_INVALIDATIONS.labels(kind=kind).inc(removed)


#: Sentinel placeholder substituted into rendered HTML in place of the
#: real per-user CSRF token. Chosen to be a string that will never
#: appear in legitimate content and is safe inside HTML attributes.
CSRF_PLACEHOLDER = "__GP_CSRF_PLACEHOLDER_DO_NOT_USE__"

#: Placeholder for the per-request CSP nonce. ``SecurityHeadersMiddleware``
#: emits a fresh nonce for every response and requires every inline or
#: external ``<script nonce="...">`` to carry that
#: exact nonce. Caching a body with a stale nonce would therefore break
#: every script, so the real nonce is substituted at response time. This
#: keeps cached pages compatible with the enforced script policy.
CSP_NONCE_PLACEHOLDER = "__GP_CSP_NONCE_PLACEHOLDER_DO_NOT_USE__"

#: Per-user role-context fields that may appear in cached partials and
#: therefore MUST be rendered as placeholders, then substituted with
#: the requesting user's real values on each cache hit. Keys match the
#: names returned by ``_role_context`` in the dashboard helpers.
#:
#: Example: ``_analytics_content.html`` renders ``{{ username }}`` in
#: a hidden form field - without this substitution, the cached HTML
#: would show the first viewer's username to every subsequent viewer.
_PERSONAL_FIELDS: tuple[str, ...] = (
    "username",
    "gitlab_username",
    "avatar_url",
    "full_name",
)

#: Mapping of personal-field name -> placeholder string. Built once so
#: callers can ``**`` it into a template context.
PERSONAL_PLACEHOLDERS: dict[str, str] = {
    name: f"__GP_PERSONAL_{name.upper()}_PLACEHOLDER__" for name in _PERSONAL_FIELDS
}

#: Default cache TTL in seconds.
#:
#: Freshness is event-driven, not TTL-driven: every data change invalidates
#: the affected fragments precisely - both GitLab webhooks (see
#: ``event_processor._invalidate_page_cache``) and in-app mutations (course /
#: settings / team / project / member edits all call ``invalidate_cascade`` /
#: ``invalidate_many``). The whole namespace is also busted per-deploy via the
#: GIT_SHA suffix. The TTL is therefore only a safety net for a change that
#: somehow bypasses both paths, so it can be generous: a longer window means
#: far more cache hits (instant loads) when a teacher clicks around, without
#: risking stale data on any real change. 5 minutes balances that against the
#: residual missed-invalidation edge case.
DEFAULT_TTL_SECONDS = 300


#: Key namespace - bumped automatically per-deploy by suffixing the
#: short GIT_SHA so that any code change (template fix, payload shape
#: change, variant-key semantics) invalidates the entire cache without
#: a manual ``FLUSHDB``.  Falls back to the static literal in local
#: dev where ``GIT_SHA`` is unset.  Bump the literal manually only if
#: you change the on-the-wire payload format itself.
def _compute_key_prefix() -> str:
    sha = os.environ.get("GIT_SHA", "").strip()
    base = "gp:page:v3"
    return f"{base}:{sha[:12]}" if sha else base


_KEY_PREFIX = _compute_key_prefix()


ScopeId = str | uuid.UUID | int | None


def _norm_scope(scope_id: ScopeId) -> str:
    """Render a scope id into its canonical string form for cache keys."""
    if scope_id is None:
        return "_"
    if isinstance(scope_id, uuid.UUID):
        return str(scope_id)
    return str(scope_id)


def make_variant(*parts: Any) -> str:
    """Compute a short stable hash of arbitrary variant parts.

    Variant parts disambiguate cache entries that share a kind+scope_id
    but render differently per request - typically ``(locale, role)``
    for shared pages, or ``(locale, role, user_id, query_params)``
    for per-user pages.

    ``None`` values are normalised to the empty string so callers do
    not need to coerce optional inputs.
    """
    normalized = ["" if p is None else str(p) for p in parts]
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=8).hexdigest()


def _build_key(kind: str, scope_id: ScopeId, variant: str) -> str:
    return f"{_KEY_PREFIX}:{kind}:{_norm_scope(scope_id)}:{variant}"


def _scope_pattern(kind: str, scope_id: ScopeId) -> str:
    """Wildcard match all variants for a single (kind, scope_id) pair."""
    return f"{_KEY_PREFIX}:{kind}:{_norm_scope(scope_id)}:*"


def get_cached(kind: str, scope_id: ScopeId, variant: str) -> str | None:
    """Return cached HTML, or ``None`` on miss/error.

    Pass cache hits through :func:`personalize` or :func:`render_inline` to
    substitute the requesting user's values and the current CSP nonce.
    """
    body = _safe_get(_build_key(kind, scope_id, variant))
    _record_lookup(kind, body is not None)
    return body


def set_cached(
    kind: str,
    scope_id: ScopeId,
    variant: str,
    body: str,
    *,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> None:
    """Store ``body`` under the given cache key for ``ttl`` seconds.

    The body MUST contain :data:`CSRF_PLACEHOLDER` instead of the real
    CSRF token - see :func:`personalize`.
    """
    _safe_setex(_build_key(kind, scope_id, variant), ttl, body)


def cacheable_role_ctx(role_ctx: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``role_ctx`` safe to render into a cached body.

    Per-user string fields are replaced with placeholders; role flags
    (``is_admin``, ``is_teacher``, ``is_student``, ``can_edit``,
    ``user_role``) are kept verbatim - they DO need to participate in
    the cache key variant so the rendered HTML matches the viewer's
    permission level.
    """
    out = dict(role_ctx)
    for name, placeholder in PERSONAL_PLACEHOLDERS.items():
        if name in out:
            out[name] = placeholder
    return out


def personalize(
    cached_body: str,
    *,
    csrf_token: str,
    role_ctx: dict[str, Any] | None = None,
    csp_nonce: str | None = None,
) -> str:
    """Substitute every placeholder with the requesting user's values.

    Handles the CSRF placeholder, the CSP nonce placeholder, and every
    entry in :data:`PERSONAL_PLACEHOLDERS`. Missing values are replaced
    with the empty string so the rendered HTML never leaks a raw
    placeholder.
    """
    body = cached_body
    if csrf_token:
        body = body.replace(CSRF_PLACEHOLDER, csrf_token)
    if csp_nonce is not None:
        body = body.replace(CSP_NONCE_PLACEHOLDER, csp_nonce)
    rc = role_ctx or {}
    for name, placeholder in PERSONAL_PLACEHOLDERS.items():
        body = body.replace(placeholder, str(rc.get(name, "") or ""))
    return body


def request_csp_nonce(request: Any) -> str:
    """Return the per-request CSP nonce set by ``SecurityHeadersMiddleware``."""
    try:
        return str(getattr(request.state, "csp_nonce", "") or "")
    except Exception:
        return ""


def make_role_variant(request: Any, role_ctx: dict[str, Any], *extra: Any) -> str:
    """Variant key built from ``(locale, role flags, *extra)``.

    Almost every dashboard partial varies on the viewer's locale and
    permission level - wrapping the boilerplate keeps the call sites
    short and uniform. Callers add page-specific differentiators
    (query params, course-membership role, "is own profile") as
    positional ``extra`` arguments. Order matters for cache key
    stability.
    """
    from app.i18n import resolve_locale

    try:
        locale = resolve_locale(request)
    except Exception:
        # Fall back to "" so a mocked request in tests does not crash
        # - locale-less callers still get a stable hash.
        locale = ""
    return make_variant(
        locale,
        role_ctx.get("user_role", ""),
        int(bool(role_ctx.get("is_teacher"))),
        int(bool(role_ctx.get("is_admin"))),
        int(bool(role_ctx.get("can_edit"))),
        *extra,
    )


def render_inline(
    *,
    request: Any,
    fragment: str,
    csrf_token: str,
    role_ctx: dict[str, Any],
    templates: Any,
    page_template: str,
    page_ctx: dict[str, Any],
) -> Response:
    """GitLab-style single-response page delivery.

    The FULL page with the (cached) content ``fragment`` inlined into
    ``{{ content_html|safe }}`` - the whole page arrives in one server
    response, exactly like GitLab, with no second HTMX round-trip and no
    full-body placeholder swap. The fragment's placeholders (CSRF, CSP nonce,
    per-user fields) are substituted first, so the inlined content and the
    surrounding page share one nonce and never leak another user's token.
    """
    content_html = personalize(
        fragment,
        csrf_token=csrf_token,
        role_ctx=role_ctx,
        csp_nonce=request_csp_nonce(request),
    )
    # Establish the viewer's locale before the shell renders.
    #
    # The cached fragment is already in the right language - the cache key
    # includes the locale - but the PAGE around it is rendered here, and its
    # `t()` calls read a context variable that this path never set. On a cache
    # hit the shell therefore fell back to the source strings: a Slovak session
    # opening course analytics saw the Slovak body under an English heading.
    #
    # This is the same call build_cache_render_ctx() makes for the same reason.
    i18n_ctx: dict[str, Any] = {}
    with suppress(Exception):
        from app.i18n import get_template_i18n_context

        i18n_ctx = get_template_i18n_context(request)

    ctx = {
        **i18n_ctx,
        **page_ctx,
        "request": request,
        "csrf_token": csrf_token,
        "content_html": content_html,
        **role_ctx,
    }
    return cast("Response", templates.TemplateResponse(request, page_template, ctx))


def build_cache_render_ctx(request: Any) -> dict[str, Any]:
    """Build the template context fragment needed for cached rendering.

    Direct ``templates.get_template(...).render(...)`` does NOT execute
    the ``Jinja2Templates`` context processors that ``TemplateResponse``
    runs automatically - so we must pull those values in manually here.
    Includes:

    * The i18n / feature-flag context (locale, supported_locales,
      ``feature_*`` toggles, ``i18n_client_config``) - these are the
      same for every viewer at the same locale and are safely cached
      verbatim.
    * The :data:`CSP_NONCE_PLACEHOLDER` for ``csp_nonce`` - must be
      substituted at response time via :func:`personalize`.
    * The :data:`CSRF_PLACEHOLDER` for ``csrf_token`` - same.
    * The :data:`PERSONAL_PLACEHOLDERS` for session-derived fields.

    Endpoints typically use this as::

        ctx = {**build_cache_render_ctx(request), "request": request, ...}
    """
    from app.i18n import get_template_i18n_context

    ctx: dict[str, Any] = {}
    with suppress(Exception):
        # i18n context unavailable in some tests with mocked requests
        # - leave keys absent; templates use ``|default(...)`` guards
        # where it matters.
        ctx.update(get_template_i18n_context(request))
    ctx["csp_nonce"] = CSP_NONCE_PLACEHOLDER
    ctx["csrf_token"] = CSRF_PLACEHOLDER
    ctx.update(PERSONAL_PLACEHOLDERS)
    return ctx


def invalidate(kind: str, scope_id: ScopeId) -> int:
    """Drop every cached variant for one ``(kind, scope_id)`` pair.

    Returns the number of keys removed (best-effort; 0 on Redis error).
    Safe to call from sync code (workers, request handlers) - uses the
    shared blocking Redis client.
    """
    pattern = _scope_pattern(kind, scope_id)
    removed = _safe_delete_pattern(pattern)
    _record_invalidation(kind, removed)
    return removed


def invalidate_many(pairs: Iterable[tuple[str, ScopeId]]) -> int:
    """Invalidate many ``(kind, scope_id)`` pairs in one call."""
    total = 0
    seen: set[tuple[str, str]] = set()
    for kind, scope_id in pairs:
        marker = (kind, _norm_scope(scope_id))
        if marker in seen:
            continue
        seen.add(marker)
        total += invalidate(kind, scope_id)
    return total


def invalidate_cascade(
    *,
    project_id: ScopeId | None = None,
    team_id: ScopeId | None = None,
    course_id: ScopeId | None = None,
    student_ids: Iterable[ScopeId] | None = None,
) -> int:
    """Invalidate every page-cache scope that could be affected by a data change.

    Mirrors the dashboard parent/child hierarchy:

    * ``project_id`` -> ``("project", project_id)``
    * ``team_id`` -> ``("team", team_id)``
    * ``course_id`` -> ``("course", ...)``, ``("course-analytics", ...)``,
      ``("course-activity", ...)``
    * each ``student_id`` -> ``("student", student_id)``

    Pass only the IDs that are known at the call site; missing IDs
    are skipped. Returns the total number of Redis keys removed.
    """
    pairs: list[tuple[str, ScopeId]] = []
    if project_id is not None:
        pairs.append(("project", project_id))
    if team_id is not None:
        pairs.append(("team", team_id))
    if course_id is not None:
        pairs.append(("course", course_id))
        pairs.append(("course-analytics", course_id))
        pairs.append(("course-activity", course_id))
    if student_ids:
        pairs.extend(("student", sid) for sid in student_ids)
    return invalidate_many(pairs) if pairs else 0


# --------------------------- Redis helpers ---------------------------


def _safe_get(key: str) -> str | None:
    """Return the cached string or ``None`` on miss / Redis failure."""
    try:
        conn = get_redis()
    except Exception:  # pool not initialised in tests
        return None
    try:
        raw: Any = conn.get(key)
    except Exception:  # Redis down / network glitch
        return None
    if raw is None:
        return None
    if isinstance(raw, bytes):
        with suppress(UnicodeDecodeError):
            return raw.decode("utf-8")
        return None
    return str(raw)


def _safe_setex(key: str, ttl: int, value: str) -> None:
    try:
        conn = get_redis()
    except Exception:
        return
    with suppress(Exception):
        conn.set(key, value, ex=ttl)


def _safe_delete_pattern(pattern: str) -> int:
    """Delete every key matching ``pattern``. Uses SCAN (not KEYS)."""
    try:
        conn = get_redis()
    except Exception:
        return 0
    removed = 0
    try:
        # Use cursor-based ``SCAN`` (not ``KEYS *`` which blocks the
        # server). Batched deletes keep round-trip count low for large
        # invalidations - e.g. dropping every team variant in a course
        # after a settings change.
        cursor: int = 0
        batch: list[Any] = []
        while True:
            cursor, keys = conn.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                batch.extend(keys)
            if len(batch) >= 200:
                removed += int(conn.delete(*batch) or 0)
                batch.clear()
            if cursor == 0:
                break
        if batch:
            removed += int(conn.delete(*batch) or 0)
    except Exception:
        return removed
    if removed:
        _log.debug("page_cache.invalidated pattern=%s removed=%d", pattern, removed)
    return removed

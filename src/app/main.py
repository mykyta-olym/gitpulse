"""FastAPI application factory with lifespan management."""

import mimetypes
import pathlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import Response

from app.api.exception_handlers import register_exception_handlers
from app.assets import DIST_DIR, DIST_URL, absolute_static_url, static_url
from app.config import get_settings
from app.db.session import dispose_engine, init_engine
from app.i18n import get_template_i18n_context
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.error_boundary import ErrorBoundaryMiddleware
from app.middleware.locale import LocaleMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.performance import StaticCacheMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.observability.logging import setup_logging
from app.redis_pool import close_redis_pool, init_redis_pool
from app.services.gitlab_import.service import is_bot_user
from app.template_cache import template_environment
from app.template_helpers import identicon, local_time

_TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"

# -- Build hash (deployment fingerprint) --
# Imported from a sibling module so request-handling code
# (dependencies, auth, security middleware) can access BUILD_HASH
# without creating a circular import on ``app.main``.
from app.build_info import BUILD_HASH  # noqa: E402  (kept near the top-level constants)


def _get_template_csp_context(request: Request) -> dict[str, str]:
    """Expose the per-request CSP nonce to Jinja templates.

    SecurityHeadersMiddleware sets ``request.state.csp_nonce`` for every
    HTTP request.  Surface it as ``{{ csp_nonce }}`` so templates can drop
    it onto every ``<script>`` tag with a single token.  Falls back to an
    empty string in degenerate cases (e.g. internal renders during tests
    where the middleware did not run); the strict CSP is still
    Report-Only at this stage so an empty nonce is safe.
    """
    return {"csp_nonce": getattr(request.state, "csp_nonce", "")}


templates = Jinja2Templates(
    env=template_environment(),
    context_processors=[get_template_i18n_context, _get_template_csp_context],
)

# Expose canonical threshold defaults to all templates so that
# ``|default(...)`` guards never use hardcoded magic numbers.
from app.api.dashboard._helpers import (  # noqa: E402
    _DEFAULT_GREEN_THRESHOLD,
    _DEFAULT_SEMESTER_WEEKS,
    _DEFAULT_YELLOW_THRESHOLD,
)
from app.utils.academic_period import (  # noqa: E402
    AcademicPeriod,
    calendar_period,
    calendar_windows,
    dialog_periods,
    in_session,
)
from app.utils.semester import (  # noqa: E402
    SEMESTER_DATE_MAX_OFFSET_DAYS,
    semester_date_min,
)
from app.utils.semester_presets import (  # noqa: E402
    current_semester_start as _current_semester_start,
)

# Settings-independent globals can be registered eagerly so the
# ``templates`` instance is fully usable from any importer (test
# fixtures, exception handlers).  Settings-dependent globals are
# registered inside ``create_app`` to keep module import side-effect
# free.
templates.env.globals["DEFAULT_GREEN_PCT"] = int(_DEFAULT_GREEN_THRESHOLD * 100)
templates.env.globals["DEFAULT_YELLOW_PCT"] = int(_DEFAULT_YELLOW_THRESHOLD * 100)
templates.env.globals["DEFAULT_SEMESTER_WEEKS"] = _DEFAULT_SEMESTER_WEEKS
templates.env.globals["static_url"] = static_url
templates.env.globals["absolute_static_url"] = absolute_static_url
templates.env.globals["build_hash"] = BUILD_HASH
# Callable so every page - including the ones with no course in context - can
# anchor its date pickers to the running semester and show the same week
# numbering. Recomputed per render: a long-running process must not keep the
# semester it booted in.
templates.env.globals["current_semester_start"] = _current_semester_start


# -- The academic period, for every template ------------------------------
# Every period a template shows or pre-fills comes from these, and every one
# of them asks app.utils.academic_period - there is no second rule anywhere.
# All are callables, recomputed per render: the top bar used to show a year
# captured at server boot, and a process started in July kept offering last
# year's courses all autumn.


def _current_period() -> dict[str, object]:
    """The term the calendar is in - or, between two terms, the one about to start.

    For the top bar, which names it, and anything else that says "now".
    ``running`` tells the two apart so the label can say Current or Upcoming,
    the same words the period selector uses for the same term.
    """
    period = calendar_period()
    return {
        "academic_year": period.academic_year,
        "semester": period.semester,
        "key": period.key,
        "running": in_session() == period,
    }


templates.env.globals["current_period"] = _current_period


def _new_course_period() -> dict[str, str]:
    """The year + semester a NEW course should default to.

    One answer for every dialog that creates or moves a course. Import from
    GitLab defaulted the semester to "summer" and Create Course to "winter"
    (its first option), so two dialogs on the same page disagreed; and the
    import's year was a string frozen at server boot. A page on which the
    reader PICKED a term overrides it with that term (see _modals.html).
    """
    period = calendar_period()
    return {"academic_year": period.academic_year, "semester": period.semester}


templates.env.globals["new_course_period"] = _new_course_period


def _next_course_period(academic_year: str, semester: str) -> dict[str, str]:
    """The same term one year on - the default target of "Transfer to New Semester"."""
    try:
        nxt = AcademicPeriod(academic_year, semester).next_year()
    except ValueError:
        return _new_course_period()
    return {"academic_year": nxt.academic_year, "semester": nxt.semester}


templates.env.globals["next_course_period"] = _next_course_period


def _is_current_period(academic_year: str, semester: str) -> bool:
    """Whether a course's term is the one the calendar says is running (or next).

    Drives the highlighted period badge on course, group, student and project
    pages: with the same course running in two terms, "this group is this
    term's" is the first thing a reader needs to know about the page.
    """
    return calendar_period().key == f"{academic_year.replace('/', '-')}-{semester}"


templates.env.globals["is_current_period"] = _is_current_period


def _period_windows() -> list[dict[str, str]]:
    """Every TUKE term with its official dates, for the period-and-dates fields:
    which dates a chosen term has, and which term a typed date falls in."""
    return calendar_windows()


templates.env.globals["period_windows"] = _period_windows


def _period_choices(
    academic_year: str = "", semester: str = "", past_terms: int = 0
) -> list[dict[str, str]]:
    """The terms a course dialog offers (see ``dialog_periods``), with the one
    the field holds added when it is outside the offered span."""
    try:
        include: AcademicPeriod | None = (
            AcademicPeriod(academic_year, semester) if academic_year and semester else None
        )
    except ValueError:
        include = None
    return [
        {
            "key": p.key,
            "academic_year": p.academic_year,
            "semester": p.semester,
            "state": state,
        }
        for p, state in dialog_periods(past_terms=past_terms, include=include)
    ]


templates.env.globals["period_choices"] = _period_choices


def _period_window(academic_year: str, semester: str) -> dict[str, str] | None:
    """The official dates of one term, or None when the calendar does not reach it."""
    return next(
        (
            w
            for w in _period_windows()
            if w["academic_year"] == academic_year and w["semester"] == semester
        ),
        None,
    )


templates.env.globals["period_window"] = _period_window


def _semester_date_bounds() -> dict[str, str]:
    """The range a semester date may be typed in - what the server enforces.

    Was computed three times, in two routes and a helper module, for the same
    two fields; one answer now, next to the fields that use it.
    """
    today = datetime.now(UTC).date()
    return {
        "min": semester_date_min(today).isoformat(),
        "max": (today + timedelta(days=SEMESTER_DATE_MAX_OFFSET_DAYS)).isoformat(),
    }


templates.env.globals["semester_date_bounds"] = _semester_date_bounds
templates.env.globals["is_bot_user"] = is_bot_user
templates.env.globals["local_time"] = local_time
templates.env.globals["identicon"] = identicon

# Compliance check registry - exposed for partials that need category/description
# lookup without the route having to pass them explicitly (e.g. the shared
# Run Compliance Checks modal).
try:
    from app.compliance.check_registry import CATEGORIES as _CHECK_CATEGORIES
    from app.compliance.check_registry import DESCRIPTIONS as _CHECK_DESCRIPTIONS

    templates.env.globals["CHECK_CATEGORIES"] = _CHECK_CATEGORIES
    templates.env.globals["CHECK_DESCRIPTIONS"] = _CHECK_DESCRIPTIONS
except Exception:
    templates.env.globals["CHECK_CATEGORIES"] = {}
    templates.env.globals["CHECK_DESCRIPTIONS"] = {}


def _register_settings_template_globals() -> None:
    """Bind settings-dependent template globals.

    Called from :func:`create_app` so that importing this module (e.g.
    from tests or scripts) does not require all environment variables
    to be set.
    """
    settings = get_settings()
    templates.env.globals["gitlab_url"] = settings.gitlab_url
    templates.env.globals["docs_url"] = settings.docs_url
    # Gates the dev-only login form + Swagger/ReDoc.
    templates.env.globals["dev_mode"] = settings.is_development or settings.debug
    templates.env.globals["contact_email"] = settings.contact_email
    templates.env.globals["survey_urls"] = {
        "student": settings.survey_url_student,
        "teacher": settings.survey_url_teacher,
        "admin": settings.survey_url_admin,
    }
    templates.env.globals["institution_name"] = settings.institution_name
    templates.env.globals["theme_color"] = settings.theme_color
    templates.env.globals["app_base_url"] = settings.app_base_url
    # Auto-reload only in development to avoid stat() overhead in production
    templates.env.auto_reload = settings.is_development


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown logic."""
    settings = get_settings()
    setup_logging(level=settings.log_level, fmt=settings.log_format)

    # Warn if RBAC is disabled in non-development mode
    if not settings.feature_rbac and not settings.is_development:
        structlog.get_logger().warning(
            "rbac_disabled_in_production",
            message="FEATURE_RBAC=false - all role enforcement is bypassed! "
            "TeacherAuth and AdminAuth will accept ANY authenticated user.",
        )

    # Warn about feature flags reserved for future scaling (default=false)
    if settings.feature_backpressure:
        structlog.get_logger().debug(
            "feature_backpressure_active",
            message="FEATURE_BACKPRESSURE=true - queue watermark thresholds "
            "are enforced via scheduler settings.",
        )

    # Initialize OpenTelemetry tracing (no-op if SDK not installed)
    from app.observability.tracing import setup_tracing

    setup_tracing(
        service_name="gitpulse",
        otlp_endpoint=settings.otlp_endpoint,
    )

    # Initialize database engine
    init_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        pool_timeout=settings.db_pool_timeout,
    )

    # Initialize shared Redis connection pool
    init_redis_pool(str(settings.redis_url))

    # SEC #6 - initialise Redis-backed session store when enabled.
    if settings.feature_redis_sessions:
        from typing import cast

        from app.redis_pool import get_redis
        from app.security.session_store import _RedisLike, init_session_store

        try:
            init_session_store(
                cast(_RedisLike, get_redis()),
                settings.secret_key,
                key_prefix=settings.session_redis_key_prefix,
                idle_refresh_seconds=settings.session_redis_idle_refresh_seconds,
                absolute_max_age_seconds=settings.session_absolute_max_age_seconds,
            )
        except Exception as exc:  # pragma: no cover - never block startup
            structlog.get_logger(__name__).error(
                "session_store_init_failed",
                error=str(exc),
            )

    # Load the image's template bytecode and prepare the ORM before Uvicorn
    # accepts requests. Background compilation took 9.4s across four processes
    # after a deploy, competing with the first visitors' requests.
    if not settings.is_development:
        from app.services.warmup import warm_process

        await warm_process(templates.env)

    yield

    # Cleanup
    close_redis_pool()
    await dispose_engine()


def _add_middleware(app: FastAPI, settings: Any) -> None:
    """The middleware stack - order matters: last added = first executed."""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.feature_security_hardening,
        dev_mode=settings.is_development,
    )
    app.add_middleware(StaticCacheMiddleware, dev_mode=settings.is_development)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(LocaleMiddleware)
    # Error boundary outermost - replaces raw JSON errors with HTML for browsers
    app.add_middleware(ErrorBoundaryMiddleware)

    # CORS only in development mode with explicit setting (never in production)
    if settings.is_development and settings.allow_dev_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Trusted host protection (production)
    if settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )

    # Forward proxy headers
    if settings.proxy_headers:
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

        proxy_trusted = settings.proxy_trusted_hosts or ["127.0.0.1", "::1"]
        app.add_middleware(cast(Any, ProxyHeadersMiddleware), trusted_hosts=proxy_trusted)


def _mount_static(app: FastAPI) -> None:
    """The static assets and the built project documentation."""

    @app.get("/static/offline.html", include_in_schema=False)
    async def offline_shell(request: Request) -> Response:
        # A cached offline document keeps its matching CSP header and nonce.
        # Serve it before the static mount so its bootstrap is allowed to run.
        return templates.TemplateResponse(request=request, name="static/offline.html")

    # Register web-font MIME types. Python's mimetypes db does not know woff/woff2,
    # so StaticFiles would serve them as application/octet-stream; combined with the
    # `X-Content-Type-Options: nosniff` header that makes browsers refuse to use the
    # file as a font (self-hosted GitLab Sans/Mono silently fall back to a system
    # font, and the <link rel=preload as=font> is reported as "preloaded but not
    # used"). Declaring the correct types fixes both.
    mimetypes.add_type("font/woff2", ".woff2")
    mimetypes.add_type("font/woff", ".woff")
    # The build outputs first: `/static` would otherwise answer for them too.
    # `check_dir=False`: before a first build there is no dist/ - its files 404
    # and the manifest warning says how to build them.
    app.mount(DIST_URL, StaticFiles(directory=str(DIST_DIR), check_dir=False), name="static-dist")
    static_dir = _TEMPLATES_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # -- Documentation Site --
    docs_dir = pathlib.Path(__file__).parents[2] / "docs-site" / "site"
    if docs_dir.exists():
        app.mount(
            "/project-docs", StaticFiles(directory=str(docs_dir), html=True), name="project-docs"
        )


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    _register_settings_template_globals()

    # Disable API docs in production to avoid exposing endpoints
    docs_enabled = settings.is_development or settings.debug
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    _add_middleware(app, settings)

    # -- Routers --
    from app.api.csp_report import csp_report_router
    from app.api.dashboard import router as dashboard_router
    from app.api.docs_authz import router as docs_authz_router
    from app.api.health import health_router
    from app.api.monitoring_authz import router as monitoring_authz_router
    from app.api.router import api_router
    from app.api.site import site_router

    app.include_router(health_router)
    app.include_router(csp_report_router)
    # Caddy calls this before serving anything under /docs/.
    app.include_router(docs_authz_router)
    # ... and this before /grafana/, /prometheus/, /jaeger/, /alertmanager/.
    app.include_router(monitoring_authz_router)
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

    _mount_static(app)

    # The site's own pages (root, icons, robots, sitemap) after the mounts.
    app.include_router(site_router)

    # -- Error Handlers --
    register_exception_handlers(app, templates)

    return app


# The production server preloads ``app.main:create_app()`` before forking;
# local Uvicorn uses ``--factory app.main:create_app``. We do NOT bind a
# module-level ``app = create_app()`` instance here - doing so caused
# double initialisation (every middleware registered twice, two lifespan
# contexts, duplicate template-global registrations) when uvicorn also
# called the factory.  Tools that want a ready-made ASGI app should call
# ``create_app()`` themselves (see ``tests/integration/conftest.py``) or
# launch uvicorn with ``--factory app.main:create_app``.

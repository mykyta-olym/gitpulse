"""Application configuration via environment variables with Pydantic Settings."""

import logging
import os
import tomllib
from enum import StrEnum
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from urllib.parse import urlparse

from pydantic import (
    AliasChoices,
    Field,
    PostgresDsn,
    RedisDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

_PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _version_from_pyproject() -> str | None:
    """Read a valid project.version from the source checkout, or return None."""
    try:
        data = tomllib.loads(_PYPROJECT_PATH.read_text(encoding="utf-8"))
        version = data.get("project", {}).get("version")
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return version.strip() if isinstance(version, str) and version.strip() else None


def _detect_app_version() -> str:
    """Prefer the source version; editable-install metadata can be stale.

    Use installed metadata for packaged deployments without pyproject.toml, then
    report unknown so health checks expose missing version information."""
    from_pyproject = _version_from_pyproject()
    if from_pyproject:
        return from_pyproject
    try:
        return _pkg_version("gitpulse")
    except PackageNotFoundError:
        return "unknown"


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class LogFormat(StrEnum):
    JSON = "json"
    CONSOLE = "console"


class Settings(BaseSettings):
    """All application settings. Loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- App --
    app_name: str = "GitPulse"
    app_version: str = Field(default_factory=_detect_app_version)
    app_env: AppEnv = AppEnv.PRODUCTION
    debug: bool = False

    # -- Database --
    database_url: PostgresDsn = Field(
        ..., description="PostgreSQL connection URL (required, no default for security)"
    )
    # Per API process. Four of them (the Dockerfile's --workers) and the four
    # workers' pools must fit Postgres' 100 connections with room for a
    # migration and a psql: 25 + 15 promised 220, and the 101st is refused
    # outright instead of waiting for the pool. tests/unit/test_metrics_reach_
    # prometheus.py keeps the sum honest.
    db_pool_size: int = 12
    db_max_overflow: int = 4
    db_pool_recycle: int = Field(
        default=1800, description="Seconds before a connection is recycled"
    )
    db_pool_timeout: int = Field(
        default=5,
        description="Seconds to wait for a connection from the pool before raising TimeoutError",
    )
    db_echo: bool = False

    # -- Redis --
    redis_url: RedisDsn = Field(default=RedisDsn("redis://localhost:6379/0"))
    redis_socket_timeout_seconds: int = Field(
        default=5, description="Default Redis socket timeout in seconds"
    )

    # -- Security --
    secret_key: str = Field(min_length=16)
    teacher_api_token: str = Field(min_length=8)
    teacher_api_token_role: str = Field(
        default="teacher",
        description="Role granted to API-token-authenticated requests (teacher|admin)",
    )
    session_max_age_seconds: int = 30 * 24 * 3600  # 30 days idle TTL
    session_absolute_max_age_seconds: int = Field(
        default=90 * 24 * 3600,  # 90 days
        description=(
            "AUTH-06: hard ceiling on a single session's lifetime regardless "
            "of activity.  Sliding TTL refreshes on each request bump idle "
            "expiry, but a session whose ``created_at`` is older than this "
            "value is rejected and the user must re-authenticate.  Bounds "
            "the blast radius of a stolen long-lived cookie."
        ),
    )
    persistent_sessions: bool = Field(
        default=True,
        description=(
            "When True (default), sessions survive server restarts/deploys. "
            "Other defences keep cookies safe: signed cookie + Redis opaque "
            "sid + Secure/HttpOnly/SameSite=Lax/__Host- prefix + absolute TTL "
            "+ explicit logout invalidation.  Set False to invalidate every "
            "session on each server restart (paranoid mode)."
        ),
    )
    session_strict_ua_fingerprint: bool = Field(
        default=False,
        description=(
            "When True, sessions are rejected if the User-Agent "
            "fingerprint (browser family + OS) does not match the one captured "
            "at login. AUTH-02: in practice modern browsers (Chrome's UA "
            "Reduction, SSE/EventSource, htmx fetch in some configurations) "
            "send slightly different UA strings between page navigation and "
            "JS/SSE fetches, producing false-positive logouts. Defaults to "
            "False (warning-only); other defences (signed cookie + Redis "
            "opaque sid + boot nonce + build hash + absolute TTL + Secure/"
            "HttpOnly/SameSite) still apply. Flip on only where UA stability "
            "is guaranteed."
        ),
    )

    # -- GitLab --
    gitlab_url: str = "https://gitlab.kpi.tuke.sk"
    gitlab_api_token: str = Field(
        default="",
        validation_alias=AliasChoices("GITLAB_API_TOKEN", "GITLAB_TOKEN"),
    )
    gitlab_api_timeout_seconds: int = 30
    gitlab_api_max_retries: int = 3

    # -- GitLab OAuth --
    gitlab_oauth_enabled: bool = Field(
        default=True, description="Enable GitLab OAuth for dashboard authentication"
    )
    gitlab_oauth_client_id: str = Field(default="", description="GitLab OAuth Application ID")
    gitlab_oauth_client_secret: str = Field(
        default="", description="GitLab OAuth Application Secret"
    )
    gitlab_oauth_auto_sign_in: bool = Field(
        default=False,
        description=(
            "GitLab's auto_sign_in_with_provider: when True the login page skips the "
            "card and redirects straight to GitLab OAuth. A visit carrying "
            "?auto_sign_in=false (which logout appends) always shows the card instead, "
            "so a signed-out user is never bounced straight back in. Default False "
            "keeps the 'Sign in with GitLab' button."
        ),
    )
    gitlab_teacher_group_ids: list[int] = Field(
        default_factory=list,
        description="GitLab group IDs that grant teacher role",
    )
    gitlab_teacher_group_paths: list[str] = Field(
        default_factory=list,
        description="GitLab group paths (e.g. 'kpi/teachers') that grant teacher role",
    )
    gitlab_teacher_usernames: list[str] = Field(
        default_factory=list,
        description="GitLab usernames explicitly granted teacher role",
    )
    gitlab_admin_usernames: list[str] = Field(
        default_factory=list,
        description="GitLab usernames explicitly granted admin role",
    )
    excluded_contributor_names: list[str] = Field(
        default_factory=list,
        description=(
            "Full names of non-teacher commit authors to exclude from contributor "
            "counts (e.g. template repository authors)"
        ),
    )

    # -- Arena KPI (external email lookup) --
    arena_email_api_url: str = Field(
        default="https://arena.kpi.fei.tuke.sk/emails",
        description="Base URL for arena email lookup by GitLab username (GET {url}/{username})",
    )
    arena_email_api_enabled: bool = Field(
        default=True,
        description="Enable arena API as fallback for student email lookup",
    )
    arena_email_api_timeout_seconds: int = Field(
        default=10,
        description="HTTP timeout for arena email API calls",
    )
    arena_email_api_token: str = Field(
        default="",
        description="Bearer token for arena email API authentication",
    )

    # -- Logging --
    log_level: str = "info"
    log_format: LogFormat = LogFormat.JSON

    # -- Webhook --
    webhook_max_payload_bytes: int = 1_048_576  # 1 MB

    # -- Worker --
    rq_default_timeout: int = 300  # 5 minutes

    # -- Observability --
    otlp_endpoint: str | None = Field(
        default=None, description="OTLP gRPC endpoint for traces, e.g. http://jaeger:4317"
    )

    # -- SSE --
    sse_poll_interval_seconds: int = Field(
        default=2, description="Seconds between SSE status polls"
    )
    sse_heartbeat_interval_seconds: int = Field(
        default=15, description="Seconds between SSE heartbeat comments"
    )

    # -- Feature Flags - Processes & Communication (PRIORITY for pilot) --
    feature_security_hardening: bool = Field(
        default=True, description="Enable CSRF protection and app-level rate limiting"
    )
    feature_event_pipeline: bool = Field(
        default=True, description="Enable DLQ, replay, and audit log for event pipeline"
    )

    # -- Feature Flags - Multi-tenant (disabled for pilot) --
    feature_rbac: bool = Field(
        default=True, description="Enable role-based access control (User model)"
    )
    feature_multi_tenant: bool = Field(
        default=False, description="Enable multi-semester clone/archive"
    )

    # -- SEC #6: Redis-backed server-side sessions --
    feature_redis_sessions: bool = Field(
        default=True,
        description=(
            "When True, session payloads are stored in Redis and the "
            "cookie carries a tiny opaque signed identifier instead of "
            "the full payload.  Enables instant revocation, force-logout-"
            "all, and shrinks cookie size from ~1 KB to ~80 B.  Requires "
            "Redis to be reachable on REDIS_URL.  Falls back to the "
            "stateless cookie path on Redis errors so authentication "
            "never hard-fails on a transient outage."
        ),
    )
    session_redis_key_prefix: str = Field(
        default="session:",
        description="Redis key namespace for the session store.",
    )
    session_redis_idle_refresh_seconds: int = Field(
        default=300,
        ge=0,
        description=(
            "Sliding-window TTL refresh.  The session TTL is bumped to "
            "session_max_age_seconds only when the elapsed lifetime "
            "exceeds this many seconds - avoids a Redis EXPIRE on every "
            "request.  Set to 0 to refresh on every load."
        ),
    )

    # -- Semester automation --
    semester_auto_archive_enabled: bool = Field(
        default=True,
        description=(
            "When true, the daily sweep auto-sets courses.is_active=False after "
            "semester_end_date + semester_grace_days has passed. Every scheduled "
            "sweep already filters on is_active=True, so a single archive flip "
            "stops all automation for that course."
        ),
    )
    semester_grace_days: int = Field(
        default=14,
        description=(
            "Days of post-semester grace before a course is auto-archived. Gives "
            "teachers time to pull final reports, students time to resolve late MRs, "
            "and buffers against semester_end_date being set too aggressively."
        ),
    )
    semester_default_length_weeks: int = Field(
        default=14,
        description=(
            "Fallback semester length when CourseSettings.semester_end_date is NULL. "
            "Used to derive effective semester end from semester_start_date."
        ),
    )
    exam_period_default_weeks: int = Field(
        default=6,
        description=(
            "Length of the exam period (skuskove obdobie) after teaching ends, used "
            "ONLY when CourseSettings.semester_end_date is NULL. Without it the "
            "fallback end was the last teaching week, so a course with no explicit "
            "end date never entered an exam period at all - no Exam Period card, no "
            "exam week pills. TUKE FEI runs roughly six weeks."
        ),
    )

    # -- Job timeouts --
    job_timeout_sync_seconds: int = Field(
        default=3600, description="RQ job timeout for full team sync (seconds)"
    )
    job_timeout_report_seconds: int = Field(
        default=600, description="RQ job timeout for report generation and checks (seconds)"
    )
    job_timeout_enrich_seconds: int = Field(
        default=180, description="RQ job timeout for GitLab enrichment jobs (seconds)"
    )
    job_timeout_event_seconds: int = Field(
        default=120, description="RQ job timeout for webhook event processing (seconds)"
    )

    gitlab_enrichment_per_item_timeout: int = Field(
        default=12, description="Seconds timeout per user/student during GitLab enrichment"
    )

    # -- LLM / AI Suggestions --
    feature_llm_suggestions: bool = Field(
        default=False, description="Enable LLM-based suggestions for teachers"
    )
    llm_provider: str = Field(
        default="openai",
        description=(
            "LLM provider: openai, gemini, groq, azure, or mock. "
            "Groq offers a free tier with Llama/Mixtral models. "
            "'mock' answers locally without any provider, so LLM-backed "
            "features stay testable when the real account is unreachable or "
            "out of quota - do not use it in production."
        ),
    )
    llm_api_key: str = Field(default="", description="API key for the LLM provider")
    llm_model: str = Field(
        default="gpt-4o-mini",
        description=(
            "Model name. Examples: gpt-4o-mini (openai), gemini-2.0-flash (gemini), "
            "llama-3.3-70b-versatile (groq), mixtral-8x7b-32768 (groq)"
        ),
    )
    llm_api_base_url: str = Field(
        default="",
        description=(
            "Override base URL for LLM API (optional). "
            "Groq: https://api.groq.com/openai/v1 (auto-set when provider=groq)"
        ),
    )
    llm_debug_mode: bool = Field(
        default=False,
        description=(
            "If True, store raw prompts/responses for debugging. "
            "If False, store only structured output."
        ),
    )
    llm_max_tokens: int = Field(
        default=8000,
        description="Max tokens for generation (expanded analysis needs ~4000-6000)",
    )
    llm_max_diff_chars: int = Field(
        default=12000, description="Max characters of diff context sent to LLM per analysis"
    )
    llm_max_retries: int = Field(
        default=2, description="Max LLM API call attempts (including retries on parse failure)"
    )
    llm_response_language: str = Field(
        default="",
        description=(
            "Language for LLM analysis responses (e.g. 'sk', 'en', 'cs'). "
            "Empty string = auto-detect from DEFAULT_LOCALE."
        ),
    )

    # -- Event Pipeline --
    dlq_max_retries: int = Field(
        default=5, description="Max retries before moving event to dead-letter queue"
    )

    # -- Scale Optimizations --
    feature_gitlab_cache: bool = Field(
        default=True, description="Enable GitLab API response caching with ETags"
    )
    feature_backpressure: bool = Field(
        default=True, description="Enable queue backpressure and rate limiting"
    )
    feature_support_forms: bool = Field(
        default=False,
        description="Enable dynamic support-form builder and ticket viewer",
    )
    feature_classroom_assistant: bool = Field(
        default=False,
        description=(
            "Enable the classroom assistant: a bot account that reviews pushes "
            "and merge requests and plants merge conflicts for exercises"
        ),
    )
    support_anonymize_free_text: bool = Field(
        default=True, description="Anonymize free-text support submissions"
    )
    compliance_auto_snapshot: bool = Field(
        default=True, description="Automatically capture weekly compliance snapshots"
    )
    app_base_url: str = Field(
        default="http://localhost:8000",
        description="Canonical public base URL used for callbacks, links, and secure cookies",
    )
    allow_dev_cors: bool = Field(
        default=False, description="Allow wildcard CORS in development mode"
    )

    # -- Email Notifications --
    smtp_host: str = Field(default="", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(
        default="",
        description=(
            "SMTP password. Whitespace is stripped: Google DISPLAYS an app "
            "password as 'abcd efgh ijkl mnop' but the credential is the 16 "
            "characters without the spaces, and pasting it as shown fails "
            "authentication with a bare 535 that names no cause."
        ),
    )
    smtp_use_tls: bool = Field(default=True, description="Use STARTTLS for SMTP")
    smtp_from_email: str = Field(
        default="support@gitpulse.dev",
        description="From address for support email notifications",
    )
    smtp_from_name: str = Field(
        default="GitPulse Support",
        description="Display name for support emails",
    )
    feature_email_notifications: bool = Field(
        default=True,
        description="Enable email notifications (tickets, role changes, courses)",
    )

    # -- Branding / links --
    docs_url: str = Field(
        default="/docs/",
        description="Public documentation site URL (relative or absolute)",
    )
    contact_email: str = Field(
        default="mykyta.olym.work@gmail.com",
        description="Contact email shown in the UI",
    )
    # One diploma thesis survey per role; the dashboard shows each user theirs.
    survey_url_student: str = Field(
        default="https://forms.gle/mNvu5Yv4bLmm4D6L6",
        description="Google Forms survey shown to students",
    )
    survey_url_teacher: str = Field(
        default="https://forms.gle/TaHFrQaFM1a33hG27",
        description="Google Forms survey shown to teachers and course owners",
    )
    survey_url_admin: str = Field(
        default="https://forms.gle/AYkbAJEft1bmHpTq5",
        description="Google Forms survey shown to administrators",
    )
    institution_name: str = Field(
        default="TUKE KPI",
        description="Institution name shown on login and footer",
    )
    theme_color: str = Field(
        default="#28272d",
        description="Browser theme-color meta tag value",
    )

    # Rate limiting settings
    rate_limit_requests_per_minute: int = Field(
        default=60, description="Max requests per project per minute"
    )

    # Backpressure settings
    queue_high_watermark: int = Field(default=1000, description="Queue depth to start throttling")
    queue_critical_watermark: int = Field(
        default=5000, description="Queue depth to stop accepting jobs"
    )

    # -- Worker tuning --
    idempotency_lock_ttl_seconds: int = Field(
        default=600, description="Redis lock TTL for idempotent job dedup (seconds)"
    )
    sync_pipeline_concurrency: int = Field(
        default=5, description="Max concurrent GitLab API calls per sync job"
    )
    llm_analysis_max_mrs: int = Field(
        default=20, description="Max MRs to analyze per LLM analysis job"
    )
    llm_analysis_cache_hours: int = Field(
        default=6, description="Hours to cache LLM analysis results per MR"
    )

    # -- Security --
    allowed_hosts: list[str] = Field(
        default_factory=list, description="Trusted Host header values (empty = allow all)"
    )
    proxy_headers: bool = Field(
        default=True, description="Trust X-Forwarded-* headers from reverse proxy"
    )
    proxy_trusted_hosts: list[str] = Field(
        default_factory=lambda: ["127.0.0.1", "::1"],
        description=(
            "Client IPs allowed to supply X-Forwarded-* headers to Uvicorn. "
            "Use '*' only when the API port is not exposed except through the reverse proxy."
        ),
    )

    # -- Monitoring stack secrets (consumed by docker-compose only - surfaced
    # here so the production validator can refuse to start with insecure defaults)
    monitoring_enabled: bool = Field(
        default=False,
        description=(
            "True when the monitoring stack (Grafana/Prometheus/Jaeger) is "
            "deployed in front of Caddy.  Gates the strict validator below."
        ),
    )
    grafana_admin_password: str = Field(
        default="", description="Grafana admin password (must be set in production)"
    )
    prometheus_url: str = Field(
        default="",
        description=(
            "Base URL of Prometheus's HTTP API as the app reaches it inside the stack "
            "(http://prometheus:9090). Empty turns the in-app observability views off."
        ),
    )

    @field_validator("smtp_password", mode="before")
    @classmethod
    def _strip_smtp_password_whitespace(cls, value: object) -> object:
        """Drop whitespace from the SMTP password.

        Google shows an app password as four groups of four ("abcd efgh ijkl
        mnop"), and pasting it exactly as shown is the obvious thing to do -
        but the credential is the 16 characters without the spaces. Gmail
        answers the spaced form with a bare ``535 Username and Password not
        accepted`` that names no cause, so this fails in a way nobody can
        diagnose from the error. No real SMTP password relies on surrounding
        or embedded whitespace.
        """
        if isinstance(value, str):
            return "".join(value.split())
        return value

    @model_validator(mode="after")
    def _warn_localhost_defaults(self) -> "Settings":
        """Log warnings when production uses insecure or localhost defaults."""
        if self.app_env == AppEnv.PRODUCTION:
            _log = logging.getLogger(__name__)
            if "localhost" in str(self.redis_url):
                _log.warning(
                    "REDIS_URL points to localhost in PRODUCTION - "
                    "set REDIS_URL to a production Redis instance"
                )
            if "localhost" in self.app_base_url:
                raise ValueError(
                    "APP_BASE_URL points to localhost in PRODUCTION. "
                    "Set APP_BASE_URL=https://<public-domain>."
                )
            parsed_base = urlparse(self.app_base_url)
            if parsed_base.scheme != "https":
                raise ValueError(
                    "APP_BASE_URL must use https:// in PRODUCTION so OAuth callbacks, "
                    "absolute links, Secure cookies, and __Host- cookie prefix are correct."
                )
            base_host = (parsed_base.hostname or "").lower()
            local_hosts = {"localhost", "127.0.0.1", "::1"}
            if base_host in local_hosts or base_host.endswith(".localhost"):
                raise ValueError(
                    "APP_BASE_URL must point to the real public host in PRODUCTION, not localhost."
                )
            if not self.allowed_hosts:
                raise ValueError(
                    "ALLOWED_HOSTS must be set in PRODUCTION as a JSON array containing "
                    "the public APP_BASE_URL host."
                )
            if "*" not in self.allowed_hosts and base_host not in {
                host.lower() for host in self.allowed_hosts
            }:
                raise ValueError(
                    f"ALLOWED_HOSTS must include the APP_BASE_URL host in PRODUCTION ({base_host})."
                )
            # AUTH-04: RBAC must be enabled in production. Refuse to start
            # rather than silently fail-open on every role-checked route.
            if not self.feature_rbac:
                raise ValueError(
                    "FEATURE_RBAC is DISABLED in PRODUCTION (AUTH-04) - "
                    "all role-based access checks would be bypassed. "
                    "Set FEATURE_RBAC=true and restart."
                )
            # §7b: Debug mode must be off in production. Hard-fail because
            # debug mode exposes stack traces and may auto-create admin users.
            if self.debug:
                raise ValueError(
                    "DEBUG is ENABLED in PRODUCTION - this exposes detailed "
                    "errors and may auto-create admin users. Set DEBUG=false "
                    "and restart."
                )
            # §7b: Secret key strength check
            if len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY is shorter than 32 characters in PRODUCTION - "
                    "use a strong random key (e.g. `python -c 'import secrets; "
                    "print(secrets.token_hex(32))'`)"
                )
            if not self.feature_redis_sessions:
                raise ValueError(
                    "FEATURE_REDIS_SESSIONS must be true in PRODUCTION so dashboard "
                    "sessions are server-side revocable."
                )
            # Monitoring stack secrets - refuse to start with a default Grafana
            # password when monitoring is actually deployed. The tools are
            # opened by a GitPulse admin session (Caddy asks
            # api/monitoring_authz.py), but Grafana's local `admin` still
            # answers at 127.0.0.1:3000. When ``monitoring_enabled`` is False
            # (default) the check is skipped.
            if self.monitoring_enabled and (
                not self.grafana_admin_password or self.grafana_admin_password.lower() == "admin"
            ):
                raise ValueError(
                    "Insecure monitoring configuration in PRODUCTION:\n - "
                    "GRAFANA_ADMIN_PASSWORD is unset or equal to 'admin' - "
                    "set a strong password before exposing Grafana."
                )
            # SEC-03/SEC-04: Redis must require a password in production.
            # Even though Redis sits on a private docker network, defence-in-
            # depth demands authentication for sessions, rate-limit state, RQ
            # job payloads, and GitLab API caches. Refuse to start without it
            # so a misconfigured deploy cannot silently leak session cookies
            # or RQ job arguments to anyone on the docker network.
            url = str(self.redis_url)
            if urlparse(url).password is None:
                raise ValueError(
                    "REDIS_URL has no password component in PRODUCTION "
                    "(SEC-03/SEC-04). Set REDIS_PASSWORD in .env so the URL "
                    "becomes redis://:PASSWORD@redis:6379/0 (defence-in-depth "
                    "on internal docker networks)."
                )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnv.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        return self.app_env == AppEnv.TEST

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def llm_analysis_enabled(self) -> bool:
        """Runtime gate for LLM analysis surfaces.

        The raw feature flag may stay configured for development/test, but
        production must not expose or execute AI analysis until it is explicitly
        re-approved for that environment.
        """
        return self.feature_llm_suggestions and not self.is_production


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    # Soft-deprecation: GITLAB_TOKEN is kept as a fallback alias for
    # GITLAB_API_TOKEN so legacy .env files keep working, but new
    # deployments should use GITLAB_API_TOKEN.  Warn loudly when only
    # the legacy variable is set.
    if os.environ.get("GITLAB_TOKEN") and not os.environ.get("GITLAB_API_TOKEN"):
        logging.getLogger(__name__).warning(
            "config_gitlab_token_deprecated_alias",
            extra={
                "details": (
                    "GITLAB_TOKEN is deprecated; rename the variable to "
                    "GITLAB_API_TOKEN. Support for the legacy name will be "
                    "removed in a future release."
                ),
            },
        )
    # BaseSettings fills required fields from process env / .env at runtime;
    # mypy only sees the generated __init__ signature.
    return Settings()  # type: ignore[call-arg]

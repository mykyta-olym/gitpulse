"""Central GitLab API-token health flag.

One place the whole app consults to know whether the configured
``GITLAB_API_TOKEN`` is currently accepted by GitLab. It is:

* **poisoned** to ``unauthorized`` the instant *any* GitLab call returns
  401/403 (``GitLabClient`` calls :func:`mark_unauthorized`), so a single
  failure makes every entrypoint and background job refuse to start doomed
  work instead of each one independently hammering GitLab and spawning retry
  storms;
* **cleared** to ``ok`` on any successful call (:func:`mark_ok`), so recovery
  after a token rotation is automatic - no restart required;
* **probeable** on demand (:func:`probe`) with a short shared cache
  (:func:`status`) so we do not hammer GitLab on every request.

State is mirrored in Redis so the API and every (forked) worker process share
one view. The Redis key carries a TTL so a stale ``unauthorized`` self-expires
and work is re-attempted even if nothing explicitly clears it.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

import structlog

from app.config import get_settings
from app.redis_pool import get_redis as _pool_get_redis

logger = structlog.get_logger(__name__)

Status = Literal["ok", "unauthorized", "unreachable", "unknown"]

_REDIS_KEY = "gitlab:token_health"
# How long a poisoned/known status is trusted before a fresh probe is allowed.
# Short enough that a fixed token recovers within a couple of minutes without a
# restart; long enough that we are not probing GitLab constantly.
_STATUS_TTL_S = 120
_DECISIVE = {"ok", "unauthorized"}


@dataclass
class _LocalMirror:
    """In-process mirror so the hot path (GitLabClient success) avoids a Redis
    round-trip on every call - Redis is only written when the status *changes*.

    ``written_ts`` is when this process last wrote the shared key, so a status
    that stays the same still keeps that key alive (see :func:`_set`).
    """

    status: Status = "unknown"
    ts: float = 0.0
    written_ts: float = 0.0

    def reset(self) -> None:
        self.status, self.ts, self.written_ts = "unknown", 0.0, 0.0


_local = _LocalMirror()


def _now() -> float:
    return time.monotonic()


def _wall() -> float:
    return time.time()


def _write_redis(status: Status) -> None:
    try:
        conn = _pool_get_redis()
        conn.set(_REDIS_KEY, f"{status}:{_wall():.0f}", ex=_STATUS_TTL_S)
    except Exception:  # pragma: no cover - Redis is best-effort here
        logger.debug("gitlab_token_health redis write failed", exc_info=True)


def _read_redis() -> tuple[Status, float] | None:
    try:
        conn = _pool_get_redis()
        raw = conn.get(_REDIS_KEY)
    except Exception:  # pragma: no cover - Redis is best-effort here
        return None
    if not raw:
        return None
    try:
        text = raw.decode() if isinstance(raw, bytes) else str(raw)
        status_str, ts_str = text.rsplit(":", 1)
        if status_str not in ("ok", "unauthorized", "unreachable", "unknown"):
            return None
        return status_str, float(ts_str)  # type: ignore[return-value]
    except (ValueError, AttributeError):
        return None


def _set(status: Status) -> None:
    """Record a new status in-process + Redis.

    Writing only on change was not enough: the shared key carries a TTL, and a
    condition that persists - a revoked token, say - never changes the status,
    so the key expired and was never rewritten. The cross-process flag then
    silently disappeared and every process fell back to probing GitLab on its
    own, which is the storm this module exists to prevent.

    So refresh the key once it is halfway through its TTL as well. The hot path
    (``mark_ok`` on every successful GitLab call) still skips Redis almost
    always, because a refresh happens at most once per half-TTL.
    """
    changed = status != _local.status
    _local.status = status
    _local.ts = _now()
    stale = (_now() - _local.written_ts) >= (_STATUS_TTL_S / 2)
    if changed or stale:
        _write_redis(status)
        _local.written_ts = _now()


def mark_unauthorized() -> None:
    """Flag the token as rejected (401/403). Called by GitLabClient + guards."""
    if _local.status != "unauthorized":
        logger.warning("gitlab_token_marked_unauthorized")
    _set("unauthorized")


def mark_ok() -> None:
    """Flag the token as accepted. Called by GitLabClient on any success."""
    if _local.status != "ok":
        logger.info("gitlab_token_marked_ok")
    _set("ok")


def cached_status() -> Status:
    """Best-effort current status WITHOUT any network probe.

    Prefers the shared Redis value (so a worker's poison is visible to the API
    and vice-versa), falling back to the in-process mirror. Returns
    ``"unknown"`` when nothing is cached (or the poison TTL expired) so callers
    let the work proceed and re-learn the truth.
    """
    shared = _read_redis()
    if shared is not None:
        return shared[0]
    if _local.status != "unknown" and (_now() - _local.ts) < _STATUS_TTL_S:
        return _local.status
    return "unknown"


async def probe() -> Status:
    """Hit GitLab ``/api/v4/version`` with the configured token.

    Returns ``ok`` (accepted), ``unauthorized`` (401/403 - token dead) or
    ``unreachable`` (network/5xx). Retries once on a transient network error so
    a single slow response does not look like an outage. Result is cached.
    """
    import httpx

    settings = get_settings()
    url = str(settings.gitlab_url).rstrip("/") + "/api/v4/version"
    headers = {"PRIVATE-TOKEN": settings.gitlab_api_token}
    last_error: str | None = None
    result: Status = "unreachable"
    async with httpx.AsyncClient(timeout=5.0) as client:
        for attempt in range(2):
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code in (401, 403):
                    result = "unauthorized"
                else:
                    result = "ok" if resp.status_code < 500 else "unreachable"
                break
            except (httpx.RequestError, TimeoutError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt == 0:
                    import asyncio

                    await asyncio.sleep(0.4)
    if result == "unreachable" and last_error:
        logger.warning("gitlab_token_probe_unreachable", error=last_error)
    _set(result)
    return result


async def status(*, max_age_s: int = _STATUS_TTL_S) -> Status:
    """Return a decisive status, probing only when the cache is stale.

    Fresh ``ok``/``unauthorized`` values are returned without a network call;
    otherwise a live :func:`probe` runs and its result is cached. This is the
    call user-facing entrypoints use to decide whether to allow GitLab work.
    """
    shared = _read_redis()
    if shared is not None:
        cur_status, cur_ts = shared
        if cur_status in _DECISIVE and (_wall() - cur_ts) < max_age_s:
            return cur_status
    return await probe()


def gitlab_token_guarded(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap an RQ job that calls GitLab so a dead token can't cause a storm.

    * **Early skip**: if the token is already known-bad (cached ``unauthorized``,
      no network call), the job is a no-op - it returns without raising, so RQ
      records it finished and does NOT retry. This stops one dead token from
      spawning a flood of doomed jobs each hammering GitLab.
    * **Fail fast on auth error**: if a fresh 401/403 surfaces inside the job,
      poison the shared flag and zero RQ's ``retries_left`` so the job fails
      once with a clear cause instead of looping through its retry budget.

    Apply ABOVE ``@idempotent_job`` so the skip happens before the dedup lock.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if cached_status() == "unauthorized":
            logger.warning("gitlab_job_skipped_token_invalid", job=getattr(fn, "__qualname__", fn))
            return None
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            from app.services.gitlab.client_types import is_gitlab_auth_error

            if is_gitlab_auth_error(exc):
                mark_unauthorized()
                try:
                    from rq import get_current_job

                    job = get_current_job()
                    if job is not None:
                        job.retries_left = 0
                except Exception:  # pragma: no cover - RQ context optional
                    logger.debug("could not zero retries_left on auth error", exc_info=True)
            raise

    return wrapper

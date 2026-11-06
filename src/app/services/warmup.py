"""Load image-built templates and prepare the ORM before accepting requests.

Template bytecode is compiled during the Docker build. Loading it here avoids
four processes compiling the same sources while serving the first requests.
Source check failures still fall back to normal Jinja compilation. This only
prepares the process; it does not cache rendered pages or user data.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import text
from sqlalchemy.orm import configure_mappers

if TYPE_CHECKING:  # pragma: no cover - typing only
    from jinja2 import Environment

_log = structlog.get_logger(__name__)
_ORM_WARMUP_TIMEOUT_S = 5.0

#: Warmed first, in this order - the templates behind the pages a session opens
#: before any other. Everything else follows in a stable alphabetical order.
_FIRST: tuple[str, ...] = (
    "login.html",
    "base.html",
    "dashboard.html",
    "partials/dashboard/_content.html",
    "course_detail.html",
    "partials/course/_detail_content.html",
    "team_detail.html",
    "partials/team/_detail_content.html",
    "student_detail.html",
    "partials/student/_detail_content.html",
)


def _ordered(env: Environment) -> list[str]:
    """Every HTML template, most-opened pages first."""
    known = set(env.list_templates(extensions=["html"]))
    head = [name for name in _FIRST if name in known]
    return head + sorted(known - set(head))


async def warm_template_cache(env: Environment) -> int:
    """Compile every template into ``env``'s cache. Returns how many succeeded.

    A template that fails to compile is logged and skipped: a warm-up must never
    be the reason the application does not start. The page that uses it raises
    the same error when it is rendered, which is where it belongs.
    """
    warmed = 0
    for name in _ordered(env):
        try:
            env.get_template(name)
            warmed += 1
        except Exception as exc:  # pragma: no cover - a broken template is a bug elsewhere
            _log.warning("template_warmup_failed", template=name, error=str(exc))
        # Allow startup probes and shutdown cancellation between templates.
        await asyncio.sleep(0)
    return warmed


async def warm_orm() -> None:
    """Resolve the ORM's mapper configuration and open one pooled connection.

    ``configure_mappers()`` is triggered by the first ORM query in the process
    and ``asyncpg`` connects on first use, so without this the first request
    pays 83ms + 162ms of setup before its own query runs.
    """

    from app.db.session import async_session_ctx

    configure_mappers()
    async with async_session_ctx() as db:
        await db.execute(text("SELECT 1"))


async def warm_process(env: Environment) -> int:
    """Run every warm-up step. Never raises - a cold process still serves."""
    started = time.perf_counter()
    try:
        await asyncio.wait_for(warm_orm(), timeout=_ORM_WARMUP_TIMEOUT_S)
    except Exception as exc:
        # A database that is not up yet is not a reason to fail: the pages that
        # need it report it, and the pool reconnects on its own.
        _log.warning("orm_warmup_failed", error=str(exc))
    templates = await warm_template_cache(env)
    _log.info(
        "process_warmed",
        templates=templates,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 1),
    )
    return templates

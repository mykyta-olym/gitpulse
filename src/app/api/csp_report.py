"""CSP violation reporting endpoint (SEC-03).

Browsers POST violations of the enforced CSP to ``/csp/report`` via the
policy's ``report-uri`` / ``report-to`` directives.
We log them as structured events so an operator can grep
``violated_directive=script-src`` etc. before promoting the strict
policy from report-only to enforce.

The endpoint accepts both report formats:

* Legacy ``Content-Type: application/csp-report`` (Firefox, Safari ≤ 15) -
  payload shape: ``{"csp-report": {...}}``.
* Modern ``Content-Type: application/reports+json`` (Chromium ≥ 96) -
  payload shape: a JSON array of report objects.

A small in-process de-duplication cache suppresses the same violation
fingerprint within a short window so a single broken page does not
flood the log stream.

Defence-in-depth notes:

* Body size is capped at ``_MAX_BODY_BYTES`` to bound memory usage.
* Malformed JSON returns ``204 No Content`` (browsers retry on errors,
  so we deliberately swallow parse failures with a debug log instead
  of a 4xx that would amplify bad clients).
* No authentication is required - by design, browsers cannot send
  credentials with CSP reports.
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from threading import Lock
from typing import Any

import structlog
from fastapi import APIRouter, Request, Response, status

logger = structlog.get_logger(__name__)
csp_report_router = APIRouter()


# Maximum acceptable CSP report payload (browsers send a few hundred bytes).
_MAX_BODY_BYTES = 16 * 1024

# Suppress repeats of the same violation fingerprint within this many seconds.
_DEDUPE_WINDOW_SECONDS = 60.0

# Maximum number of distinct fingerprints tracked at once (LRU eviction).
_DEDUPE_MAX_KEYS = 1024


class _DedupeCache:
    """Tiny LRU + TTL cache used to suppress noisy duplicate reports."""

    def __init__(self, max_keys: int, ttl_seconds: float) -> None:
        self._entries: OrderedDict[str, float] = OrderedDict()
        self._max_keys = max_keys
        self._ttl = ttl_seconds
        self._lock = Lock()

    def should_log(self, fingerprint: str) -> bool:
        now = time.monotonic()
        with self._lock:
            last = self._entries.get(fingerprint)
            if last is not None and now - last < self._ttl:
                # Already logged recently - refresh recency, drop.
                self._entries.move_to_end(fingerprint)
                return False
            self._entries[fingerprint] = now
            self._entries.move_to_end(fingerprint)
            while len(self._entries) > self._max_keys:
                self._entries.popitem(last=False)
            return True


_dedupe = _DedupeCache(_DEDUPE_MAX_KEYS, _DEDUPE_WINDOW_SECONDS)


def _normalise(report: dict[str, Any]) -> dict[str, Any]:
    """Normalise legacy ``csp-report`` and modern ``reports+json`` shapes."""
    body = report.get("body") if "body" in report else report
    if not isinstance(body, dict):
        return {}
    # Convert the modern dashed keys (``blocked-uri``) to underscores so
    # structured loggers don't require quoting them.
    return {
        "document_uri": body.get("documentURL") or body.get("document-uri"),
        "violated_directive": body.get("effectiveDirective") or body.get("violated-directive"),
        "blocked_uri": body.get("blockedURL") or body.get("blocked-uri"),
        "source_file": body.get("sourceFile") or body.get("source-file"),
        "line_number": body.get("lineNumber") or body.get("line-number"),
        "column_number": body.get("columnNumber") or body.get("column-number"),
        "disposition": body.get("disposition"),
        "sample": (body.get("sample") or "")[:200] or None,
    }


def _fingerprint(record: dict[str, Any]) -> str:
    """Stable key for de-duplication - directive + blocked + source + line."""
    return "|".join(
        str(record.get(field) or "")
        for field in ("violated_directive", "blocked_uri", "source_file", "line_number")
    )


@csp_report_router.post(
    "/csp/report",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def csp_report(request: Request) -> Response:
    """Receive CSP violation reports from browsers.

    Always returns ``204 No Content`` regardless of payload validity.
    """
    body = await request.body()
    if len(body) > _MAX_BODY_BYTES:
        logger.warning(
            "csp_report.oversized",
            extra={"size_bytes": len(body)},
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if not body:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.debug("csp_report.malformed_json")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Normalise both shapes to a uniform list of report dicts.
    reports: list[dict[str, Any]]
    if isinstance(payload, dict) and "csp-report" in payload:
        reports = [payload["csp-report"]]
    elif isinstance(payload, list):
        reports = [r for r in payload if isinstance(r, dict)]
    else:
        reports = []

    user_agent = request.headers.get("user-agent", "")[:200]

    for raw in reports:
        record = _normalise(raw)
        if not record.get("violated_directive"):
            continue
        if not _dedupe.should_log(_fingerprint(record)):
            continue
        logger.warning(
            "csp_violation",
            user_agent=user_agent,
            **{k: v for k, v in record.items() if v is not None},
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

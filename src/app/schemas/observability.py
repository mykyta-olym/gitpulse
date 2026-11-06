"""Observability response schemas (api/observability.py)."""

from typing import Literal

from pydantic import BaseModel


class ServiceNotice(BaseModel):
    """What a reader is told while an alert that affects them fires."""

    key: str
    text: str
    action_href: str | None = None
    action_label: str | None = None


class ObservabilityStatusResponse(BaseModel):
    """The monitoring stack's state, as far as the reader's role should see it.

    `unknown` when Prometheus is not configured or does not answer - never
    reported as all clear.
    """

    state: Literal["ok", "degraded", "unknown"]
    notices: list[ServiceNotice]

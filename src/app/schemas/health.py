"""Health check response schemas - production-grade."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ComponentStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class OverallStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class ComponentHealth(BaseModel):
    """Health status of an individual infrastructure component."""

    status: ComponentStatus = ComponentStatus.OK
    latency_ms: float | None = None
    error: str | None = None
    details: dict[str, str | int | float | bool | None] | None = None


class HealthResponse(BaseModel):
    """Full health check response with per-component breakdown."""

    status: OverallStatus
    version: str
    environment: str = "production"
    uptime_seconds: float
    uptime_human: str = ""
    components: dict[str, ComponentHealth]
    timestamp: datetime
    checks_duration_ms: float = Field(
        default=0.0, description="Total wall-clock time for all checks"
    )


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: str  # "ready" | "not_ready"
    reason: str | None = None
    components: dict[str, str] | None = None

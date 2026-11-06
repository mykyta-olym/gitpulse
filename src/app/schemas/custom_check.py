"""Custom-check CRUD schemas.

These Pydantic models validate request/response payloads for the
custom-check management endpoints in the course dashboard.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, StrictBool, field_validator, model_validator

from app.utils.constants import DEFAULT_CUSTOM_CHECK_WEIGHT

# -- Shared constants ------------------------------------------------
ALLOWED_RULE_TYPES = frozenset({"count", "field_check", "ratio", "word_count", "avg_word_count"})


def validate_rule_type(v: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate that evaluation_rule type is a supported custom check type."""
    if v:
        rt = v.get("type", "")
        if rt and rt not in ALLOWED_RULE_TYPES:
            valid = ", ".join(sorted(ALLOWED_RULE_TYPES))
            msg = f"Invalid rule type '{rt}'. Must be one of: {valid}"
            raise ValueError(msg)
    return v


# -- Request schemas -------------------------------------------------


class CustomCheckCreate(BaseModel):
    """Payload for creating a new custom check."""

    check_code: str = Field(
        default="",
        max_length=10,
        description="Unique code within the course (e.g. C01). Auto-generated if empty.",
    )
    name: str = Field(
        default="Custom Check",
        max_length=200,
        description="Short human-readable name.",
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="What this check verifies.",
    )
    # pydantic Field() default vs Literal - validated by the mypy pydantic plugin
    # pyrefly: ignore[bad-assignment]
    category: Literal["issue", "mr", "review", "ci", "commit", "custom"] = Field(
        default="custom",
        description="Engine category for score aggregation.",
    )
    evaluation_rule: dict[str, Any] = Field(
        default_factory=dict,
        description="JSONB evaluation rule (type, entity, threshold, ...).",
    )
    weight: float = Field(
        default=DEFAULT_CUSTOM_CHECK_WEIGHT,
        ge=0.0,
        le=1.0,
        description="Weight factor for weighted_score (0-1).",
    )
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0, ge=0, le=10000)
    created_by: str = Field(default="manual", max_length=100)

    @field_validator("evaluation_rule")
    @classmethod
    def _validate_rule_type(cls, v: dict[str, Any]) -> dict[str, Any]:
        validate_rule_type(v)
        return v


class CustomCheckUpdate(BaseModel):
    """Payload for updating an existing custom check (partial)."""

    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: Literal["issue", "mr", "review", "ci", "commit", "custom"] | None = None
    evaluation_rule: dict[str, Any] | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)

    @field_validator("evaluation_rule")
    @classmethod
    def _validate_rule_type(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_rule_type(v)


class CheckUpdate(CustomCheckUpdate):
    """A staged built-in or custom check edit; omitted fields stay unchanged."""

    is_active: StrictBool | None = None
    check_config: dict[str, Any] | None = None
    expected_updated_at: datetime | None = None

    @model_validator(mode="after")
    def _non_null_edits(self) -> "CheckUpdate":
        for field in self.model_fields_set - {"expected_updated_at"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


# -- Response schemas ------------------------------------------------

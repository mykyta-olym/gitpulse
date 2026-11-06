"""CustomCheck model - teacher-defined dynamic compliance checks.

Each CustomCheck defines a rule that the compliance engine evaluates at runtime.
Rules are stored as JSONB and interpreted by the dynamic evaluator
(:mod:`app.compliance.dynamic_checks`).

Evaluation rule schema
----------------------
**count** - count entities matching a filter, compare to threshold::

    {
        "type": "count",
        "entity": "merge_request",        # issue | merge_request | pipeline | review | response
        "filter": {"state": "merged"},     # field == value conditions (AND)
        "operator": ">=",                  # >= | <= | == | > | <
        "threshold": 2,
        "partial_scoring": true            # score = weight * (count / threshold) if partial
    }

**field_check** - at least one (or all) entities satisfy a boolean field::

    {
        "type": "field_check",
        "entity": "merge_request",
        "field": "has_test_changes",       # any boolean/truthy field on the entity
        "expected": true,
        "match_mode": "any"                # "any" | "all"
    }

**ratio** - ratio of filtered entities to total, compared to threshold::

    {
        "type": "ratio",
        "entity": "merge_request",
        "numerator_filter": {"has_issue_link": true},
        "denominator_filter": {},
        "operator": ">=",
        "threshold": 0.8,
        "partial_scoring": true
    }

**word_count** - check that notes/reviews have a minimum average word count::

    {
        "type": "word_count",
        "entity": "note",                  # note | review
        "min_avg_words": 30
    }
"""

import uuid
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.utils.constants import DEFAULT_CUSTOM_CHECK_WEIGHT


class CustomCheck(Base, UUIDMixin, TimestampMixin):
    """A teacher-defined dynamic compliance check for a course."""

    __tablename__ = "custom_checks"
    __table_args__ = (
        UniqueConstraint("course_id", "check_code", name="uq_custom_checks_course_code"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unique code within course, e.g. C01, C02",
    )

    @validates("check_code")
    def _validate_check_code(self, _key: str, code: str) -> str:
        """Ensure custom check codes don't collide with built-in R01-R13.

        Was previously a plain ``@staticmethod`` that nothing ever called, so the
        rule it documents was never enforced: the create endpoint passes the
        client's ``check_code`` through verbatim, which allowed a custom check to
        be created as e.g. ``R05`` and shadow a built-in. Wired as a SQLAlchemy
        validator so it now fires on every assignment. The import path already
        generates ``C{nn}`` codes, so it is unaffected.
        """
        if code and not code.upper().startswith("C"):
            raise ValueError(
                f"Custom check codes must start with 'C' prefix (got '{code}'). "
                "Built-in codes R01-R13 are reserved."
            )
        return code

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="custom",
        comment="issue | mr | review | ci | commit | custom",
    )

    evaluation_rule: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Rule evaluated by dynamic_checks engine (see module docstring)",
    )

    weight: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_CUSTOM_CHECK_WEIGHT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        comment="manual | import | llm",
    )

"""Course membership model - per-course role assignments.

Enables the same user to hold different roles in different courses:
e.g. *owner* of Course A, *student* of Course B.

Role hierarchy (higher includes lower permissions):
    owner > teacher > student

System admins (User.role == 'admin') bypass course-level checks
and do NOT need a CourseMembership row.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.user import User

# Ordered from least to most privileged
COURSE_ROLES = ("student", "teacher", "owner")

COURSE_ROLE_WEIGHT: dict[str, int] = {r: i for i, r in enumerate(COURSE_ROLES)}


class CourseMembership(Base, UUIDMixin, TimestampMixin):
    """Per-course role assignment linking a User to a Course."""

    __tablename__ = "course_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_course_membership_user_course"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
        comment="owner | teacher | student",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", lazy="selectin")

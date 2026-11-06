"""Student model."""

from typing import Any

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Student(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "students"

    gitlab_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    gitlab_username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))

    # Compliance history
    compliance_snapshots: Mapped[list[Any]] = relationship(
        "StudentComplianceSnapshot", back_populates="student", lazy="noload"
    )

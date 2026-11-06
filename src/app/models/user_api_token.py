"""Per-user API token model for individual token management.

Replaces the single shared TEACHER_API_TOKEN for users who need API access.
The shared token is still supported as a fallback via settings.teacher_api_token.
"""

import secrets
import uuid
from datetime import datetime

import bcrypt
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


def _generate_api_token() -> str:
    """Generate a secure API token with a recognisable prefix."""
    return f"gp_{secrets.token_hex(32)}"


def _hash_token(token: str) -> str:
    """Hash an API token for storage (bcrypt)."""
    return bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_api_token(token: str, stored_hash: str) -> bool:
    """Verify a token against its bcrypt hash (constant-time)."""
    try:
        return bcrypt.checkpw(token.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


class UserApiToken(Base, UUIDMixin, TimestampMixin):
    """Per-user API token for programmatic access.

    Tokens are bcrypt-hashed.  The plaintext is shown once on creation
    and cannot be retrieved later.  Each user can have multiple tokens
    (e.g. "CI bot", "personal script") and revoke them individually.
    """

    __tablename__ = "user_api_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable label (e.g. "CI/CD integration", "personal dev")
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Bcrypt hash of the token - plaintext never stored
    token_hash: Mapped[str] = mapped_column(String(200), nullable=False)

    # First 8 chars of token for identification (e.g. "gp_a1b2c3...")
    token_prefix: Mapped[str] = mapped_column(String(12), nullable=False)

    # Permissions / role this token grants
    token_role: Mapped[str] = mapped_column(String(20), nullable=False, default="teacher")

    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @classmethod
    def create_token(
        cls,
        user_id: uuid.UUID,
        name: str,
        role: str = "teacher",
        expires_at: datetime | None = None,
    ) -> tuple["UserApiToken", str]:
        """Create a new token instance and return (model, plaintext_token).

        The plaintext token must be shown to the user once and cannot be
        retrieved later.
        """
        plaintext = _generate_api_token()
        instance = cls(
            user_id=user_id,
            name=name,
            token_hash=_hash_token(plaintext),
            token_prefix=plaintext[:10],
            token_role=role,
            expires_at=expires_at,
        )
        return instance, plaintext

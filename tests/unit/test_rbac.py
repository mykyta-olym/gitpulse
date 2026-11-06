"""Unit tests for RBAC feature: schemas, feature flags, user model structure.

Note: OAuth-only mode - UserCreate and UserLogin schemas removed.
Users are synced from GitLab OAuth, not created locally.
"""

import pytest
from pydantic import ValidationError


class TestUserSchemas:
    """Test user schemas for OAuth-only mode."""

    def test_user_update_partial(self) -> None:
        """Test partial update with role only."""
        from app.schemas.users import UserUpdate

        u = UserUpdate(role="teacher")
        dump = u.model_dump(exclude_unset=True)
        assert dump == {"role": "teacher"}

    def test_user_update_is_active(self) -> None:
        """Test update with is_active flag."""
        from app.schemas.users import UserUpdate

        u = UserUpdate(is_active=False)
        dump = u.model_dump(exclude_unset=True)
        assert dump == {"is_active": False}

    def test_user_update_empty(self) -> None:
        """Test empty update."""
        from app.schemas.users import UserUpdate

        u = UserUpdate()
        dump = u.model_dump(exclude_unset=True)
        assert dump == {}

    def test_user_read_fields(self) -> None:
        """Test UserRead has all required fields."""
        from app.schemas.users import UserRead

        fields = UserRead.model_fields
        assert "id" in fields
        assert "username" in fields
        assert "role" in fields
        assert "is_active" in fields
        assert "email" in fields

    def test_user_update_invalid_role(self) -> None:
        """Test that invalid role raises ValidationError."""
        from app.schemas.users import UserUpdate

        with pytest.raises(ValidationError, match="role"):
            UserUpdate(role="superadmin")

    def test_user_update_valid_roles(self) -> None:
        """Test all valid roles are accepted."""
        from app.schemas.users import UserUpdate

        for role in ["student", "teacher", "admin"]:
            u = UserUpdate(role=role)
            assert u.role == role

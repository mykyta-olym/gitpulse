"""Data classes for membership sync service."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class MemberSyncResult:
    """Summary of a membership sync operation."""

    team_id: UUID
    team_name: str
    members_added: int = 0
    members_removed: int = 0
    members_reactivated: int = 0
    roles_changed: int = 0
    members_unchanged: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (
            self.members_added
            + self.members_removed
            + self.members_reactivated
            + self.roles_changed
        )


@dataclass
class _GitLabMemberInfo:
    """Parsed GitLab member info."""

    gitlab_user_id: int
    username: str
    full_name: str | None
    email: str | None
    access_level: int
    access_role: str
    source: str  # "direct" or "inherited"

"""Unit tests for member_sync_types and gitlab.cache_types dataclasses."""

from __future__ import annotations

import uuid


class TestMemberSyncResult:
    def test_defaults(self):
        from app.services.member_sync_types import MemberSyncResult

        r = MemberSyncResult(team_id=uuid.uuid4(), team_name="T1")
        assert r.members_added == 0
        assert r.members_removed == 0
        assert r.members_reactivated == 0
        assert r.roles_changed == 0
        assert r.members_unchanged == 0
        assert r.errors == []
        assert r.total_changes == 0

    def test_total_changes(self):
        from app.services.member_sync_types import MemberSyncResult

        r = MemberSyncResult(
            team_id=uuid.uuid4(),
            team_name="T1",
            members_added=2,
            members_removed=1,
            members_reactivated=3,
            roles_changed=4,
        )
        assert r.total_changes == 10

    def test_errors_list(self):
        from app.services.member_sync_types import MemberSyncResult

        r = MemberSyncResult(team_id=uuid.uuid4(), team_name="T1", errors=["e1"])
        assert r.errors == ["e1"]


class TestGitLabMemberInfo:
    def test_creation(self):
        from app.services.member_sync_types import _GitLabMemberInfo

        m = _GitLabMemberInfo(
            gitlab_user_id=1,
            username="john",
            full_name="John",
            email="j@x.com",
            access_level=30,
            access_role="Developer",
            source="direct",
        )
        assert m.username == "john"
        assert m.access_level == 30


class TestCacheConfig:
    def test_defaults(self):
        from app.services.gitlab.cache_types import CacheConfig

        c = CacheConfig()
        assert c.default_ttl == 300
        assert c.list_ttl == 120
        assert c.user_ttl == 900
        assert c.compress_threshold == 1024
        assert c.enabled is True

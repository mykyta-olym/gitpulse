"""Unit tests for the multi-scope webhook configuration service.

These tests validate the pieces of the service that can be exercised
without a real Postgres connection: scope-payload validation, the
``WebhookConfiguration.matches_payload`` boundary semantics, the
plaintext format, the rotate / revoke bookkeeping and the
``record_last_used`` rate-limit.

End-to-end auth flow against the real receiver is covered in
``tests/integration``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.webhook_configuration import WebhookConfiguration
from app.services import webhook_configs as wc

# -- Scope matching semantics ----------------------------------------


def _cfg(**overrides) -> WebhookConfiguration:
    """Build a transient (un-attached) WebhookConfiguration row."""
    cfg = WebhookConfiguration()
    cfg.id = uuid4()
    cfg.course_id = uuid4()
    cfg.name = overrides.pop("name", "Test")
    cfg.description = overrides.pop("description", None)
    cfg.scope_type = overrides.pop("scope_type", "course")
    cfg.gitlab_group_id = overrides.pop("gitlab_group_id", None)
    cfg.gitlab_group_path = overrides.pop("gitlab_group_path", None)
    cfg.gitlab_project_ids = overrides.pop("gitlab_project_ids", [])
    cfg.secret_hash = overrides.pop("secret_hash", "")
    cfg.secret_lookup = overrides.pop("secret_lookup", "")
    cfg.secret_hash_previous = overrides.pop("secret_hash_previous", None)
    cfg.secret_lookup_previous = overrides.pop("secret_lookup_previous", None)
    cfg.previous_expires_at = overrides.pop("previous_expires_at", None)
    cfg.is_active = overrides.pop("is_active", True)
    cfg.created_at = overrides.pop("created_at", datetime.now(UTC))
    cfg.rotated_at = overrides.pop("rotated_at", None)
    cfg.last_used_at = overrides.pop("last_used_at", None)
    cfg.created_by = overrides.pop("created_by", None)
    assert not overrides, f"Unused overrides: {overrides}"
    return cfg


class TestScopeMatching:
    def test_course_scope_matches_anything(self):
        cfg = _cfg(scope_type="course")
        assert cfg.matches_payload(project_id=42, path_with_namespace="x/y") is True
        assert cfg.matches_payload(project_id=None, path_with_namespace=None) is True

    def test_projects_scope_requires_id_in_list(self):
        cfg = _cfg(scope_type="projects", gitlab_project_ids=[10, 20, 30])
        assert cfg.matches_payload(project_id=20, path_with_namespace="x/y") is True
        assert cfg.matches_payload(project_id=99, path_with_namespace="x/y") is False
        assert cfg.matches_payload(project_id=None, path_with_namespace="x/y") is False

    def test_group_scope_matches_exact_path(self):
        cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi-2026")
        assert cfg.matches_payload(project_id=1, path_with_namespace="teaching/zsi-2026") is True

    def test_group_scope_matches_descendants(self):
        cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi-2026")
        assert (
            cfg.matches_payload(project_id=1, path_with_namespace="teaching/zsi-2026/team-alpha")
            is True
        )
        assert (
            cfg.matches_payload(
                project_id=1,
                path_with_namespace="teaching/zsi-2026/sub-group/team-beta",
            )
            is True
        )

    def test_group_scope_path_boundary_protects_against_prefix_collision(self):
        """``teaching/zsi`` must NOT match ``teaching/zsi-2026``."""
        cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi")
        assert (
            cfg.matches_payload(project_id=1, path_with_namespace="teaching/zsi-2026/team-alpha")
            is False
        )

    def test_group_scope_case_insensitive(self):
        cfg = _cfg(scope_type="group", gitlab_group_path="Teaching/ZSI-2026")
        assert (
            cfg.matches_payload(project_id=1, path_with_namespace="TEACHING/zsi-2026/team-alpha")
            is True
        )

    def test_group_scope_rejects_outside_path(self):
        cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi-2026")
        assert cfg.matches_payload(project_id=1, path_with_namespace="other/group/team") is False

    def test_subgroup_scope_uses_same_path_logic(self):
        cfg = _cfg(scope_type="subgroup", gitlab_group_path="teaching/zsi-2026/sub")
        assert (
            cfg.matches_payload(project_id=1, path_with_namespace="teaching/zsi-2026/sub/team")
            is True
        )
        assert (
            cfg.matches_payload(project_id=1, path_with_namespace="teaching/zsi-2026/other/team")
            is False
        )

    def test_group_scope_requires_path(self):
        cfg = _cfg(scope_type="group", gitlab_group_path="x")
        assert cfg.matches_payload(project_id=1, path_with_namespace=None) is False

    def test_unknown_scope_returns_false(self):
        cfg = _cfg()
        cfg.scope_type = "made_up"
        assert cfg.matches_payload(project_id=1, path_with_namespace="x/y") is False


# -- Plaintext / format ----------------------------------------------


def test_plaintext_secret_format():
    s1 = wc._new_plaintext()
    s2 = wc._new_plaintext()
    assert s1.startswith("whsec_")
    assert s2.startswith("whsec_")
    assert s1 != s2  # 192 bits of entropy - collision must be vanishingly rare
    assert len(s1) == len("whsec_") + 48  # 24 bytes -> 48 hex chars


# -- Scope payload validation ----------------------------------------


class TestValidateScopePayload:
    def test_projects_requires_non_empty_list(self):
        with pytest.raises(ValueError, match="at least one"):
            wc._validate_scope_payload(
                scope_type="projects", gitlab_group_path=None, gitlab_project_ids=[]
            )

    def test_projects_rejects_zero_or_negative(self):
        with pytest.raises(ValueError, match="positive integers"):
            wc._validate_scope_payload(
                scope_type="projects", gitlab_group_path=None, gitlab_project_ids=[0]
            )
        with pytest.raises(ValueError, match="positive integers"):
            wc._validate_scope_payload(
                scope_type="projects",
                gitlab_group_path=None,
                gitlab_project_ids=[-5, 1],
            )

    def test_projects_rejects_duplicates(self):
        with pytest.raises(ValueError, match="unique"):
            wc._validate_scope_payload(
                scope_type="projects",
                gitlab_group_path=None,
                gitlab_project_ids=[1, 2, 2],
            )

    def test_group_requires_path(self):
        with pytest.raises(ValueError, match="gitlab_group_path"):
            wc._validate_scope_payload(
                scope_type="group", gitlab_group_path=None, gitlab_project_ids=None
            )

    def test_subgroup_requires_path(self):
        with pytest.raises(ValueError, match="gitlab_group_path"):
            wc._validate_scope_payload(
                scope_type="subgroup",
                gitlab_group_path=None,
                gitlab_project_ids=None,
            )

    def test_unknown_scope_rejected(self):
        with pytest.raises(ValueError, match="Unknown scope_type"):
            wc._validate_scope_payload(
                scope_type="root", gitlab_group_path=None, gitlab_project_ids=None
            )

    def test_course_scope_no_extra_required(self):
        # Should not raise.
        wc._validate_scope_payload(
            scope_type="course", gitlab_group_path=None, gitlab_project_ids=None
        )


# -- Rotation logic (with mocked DB / audit) -------------------------


@pytest.mark.asyncio
async def test_rotate_first_time_does_not_set_previous():
    cfg = _cfg(scope_type="course")
    cfg.secret_hash = ""  # first-time
    cfg.secret_lookup = ""

    db = AsyncMock()
    db.refresh = AsyncMock()
    with patch.object(wc, "write_audit", AsyncMock()):
        result = await wc.rotate_configuration(db, cfg)

    assert result.plaintext.startswith("whsec_")
    assert cfg.secret_hash != ""
    assert cfg.secret_lookup != ""
    assert cfg.secret_hash_previous is None
    assert cfg.previous_expires_at is None
    assert cfg.rotated_at is not None


@pytest.mark.asyncio
async def test_rotate_subsequent_demotes_current_to_previous():
    cfg = _cfg(scope_type="course")
    cfg.secret_hash = "old-hash"
    cfg.secret_lookup = "old-lookup"

    db = AsyncMock()
    db.refresh = AsyncMock()
    with patch.object(wc, "write_audit", AsyncMock()):
        result = await wc.rotate_configuration(db, cfg)

    assert cfg.secret_hash != "old-hash"  # new
    assert cfg.secret_hash_previous == "old-hash"
    assert cfg.secret_lookup_previous == "old-lookup"
    assert cfg.previous_expires_at is not None
    assert result.previous_expires_at is not None
    grace = (cfg.previous_expires_at - datetime.now(UTC)).total_seconds()
    assert 23 * 3600 < grace <= 24 * 3600


@pytest.mark.asyncio
async def test_rotate_audit_never_contains_plaintext():
    cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi-2026")
    cfg.secret_hash = "old"
    cfg.secret_lookup = "lk"

    audit_spy = AsyncMock()
    db = AsyncMock()
    db.refresh = AsyncMock()
    with patch.object(wc, "write_audit", audit_spy):
        result = await wc.rotate_configuration(db, cfg, actor_label="alice")

    audit_spy.assert_awaited_once()
    assert audit_spy.await_args is not None
    call_kwargs = audit_spy.await_args.kwargs
    detail_blob = repr(call_kwargs.get("detail"))
    assert result.plaintext not in detail_blob
    assert "whsec_" not in detail_blob


@pytest.mark.asyncio
async def test_revoke_clears_all_secret_material_and_deactivates():
    cfg = _cfg(scope_type="course")
    cfg.secret_hash = "h"
    cfg.secret_lookup = "lk"
    cfg.secret_hash_previous = "old"
    cfg.secret_lookup_previous = "lk_old"
    cfg.previous_expires_at = datetime.now(UTC) + timedelta(hours=1)
    cfg.is_active = True

    db = AsyncMock()
    with patch.object(wc, "write_audit", AsyncMock()):
        await wc.revoke_configuration(db, cfg)

    assert cfg.secret_hash == ""
    assert cfg.secret_lookup == ""
    assert cfg.secret_hash_previous is None
    assert cfg.secret_lookup_previous is None
    assert cfg.previous_expires_at is None
    assert cfg.is_active is False


@pytest.mark.asyncio
async def test_revoke_with_delete_calls_db_delete():
    cfg = _cfg(scope_type="course")
    cfg.secret_hash = "h"
    cfg.secret_lookup = "lk"

    db = AsyncMock()
    with patch.object(wc, "write_audit", AsyncMock()):
        await wc.revoke_configuration(db, cfg, delete=True)

    db.delete.assert_awaited_once_with(cfg)


# -- record_last_used ------------------------------------------------


@pytest.mark.asyncio
async def test_record_last_used_skips_when_recent():
    cfg = _cfg(scope_type="course")
    cfg.last_used_at = datetime.now(UTC) - timedelta(seconds=10)
    original = cfg.last_used_at

    db = AsyncMock()
    db.get = AsyncMock(return_value=cfg)
    await wc.record_last_used(db, config_id=cfg.id)

    assert cfg.last_used_at == original
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_record_last_used_updates_when_stale():
    cfg = _cfg(scope_type="course")
    cfg.last_used_at = datetime.now(UTC) - timedelta(minutes=5)

    db = AsyncMock()
    db.get = AsyncMock(return_value=cfg)
    await wc.record_last_used(db, config_id=cfg.id)

    assert cfg.last_used_at is not None
    assert (datetime.now(UTC) - cfg.last_used_at).total_seconds() < 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_last_used_swallows_errors():
    db = AsyncMock()
    db.get = AsyncMock(side_effect=RuntimeError("boom"))
    db.rollback = AsyncMock()
    # Must not raise.
    await wc.record_last_used(db, config_id=uuid4())


@pytest.mark.asyncio
async def test_record_last_used_handles_missing_row():
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    # Must be a no-op, not a crash.
    await wc.record_last_used(db, config_id=uuid4())
    db.commit.assert_not_called()


# -- authenticate() pool query + scope check -------------------------


@pytest.mark.asyncio
async def test_authenticate_returns_none_for_empty_token():
    db = AsyncMock()
    result = await wc.authenticate(db, token="", project_gitlab_id=1, path_with_namespace="x/y")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_skips_configs_with_non_matching_scope():
    """An attacker with a leaked group secret cannot use it for a
    project outside that group."""
    cfg = _cfg(scope_type="group", gitlab_group_path="teaching/zsi-2026")
    cfg.secret_hash = "doesnt-matter"
    cfg.secret_lookup = "lookup"
    cfg.is_active = True

    # Mock DB returning this config from the lookup query.
    fake_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [cfg]))
    db = AsyncMock()
    db.execute = AsyncMock(return_value=fake_result)

    # Payload from a project OUTSIDE the group -> must be rejected even
    # though the lookup digest matches.
    result = await wc.authenticate(
        db,
        token="any-token",
        project_gitlab_id=99,
        path_with_namespace="other/group/team",
    )
    assert result is None

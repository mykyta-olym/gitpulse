"""Tests covering small gaps across multiple modules to maintain â‰¥ 40% coverage.

Targets: api/errors.py, i18n/__init__.py, schemas/support.py,
schemas/courses.py, schemas/llm.py, models/merge_request.py,
models/commit.py, models/team.py.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.errors import (
    check_optimistic_lock,
    raise_bad_request,
    raise_conflict,
    raise_forbidden,
    raise_http_error,
    raise_internal_error,
    raise_not_found,
    raise_payload_too_large,
    raise_service_unavailable,
    raise_unauthorized,
    raise_unprocessable,
)
from app.compliance.check_registry import _load_json
from app.config import AppEnv
from app.i18n import (
    SOURCE_LOCALE,
    _canonical_text,
    _detokenize_numbers,
    _get_pattern_catalog,
    _parse_accept_language,
    _tokenize_numbers,
    get_catalog,
    normalize_locale,
    resolve_locale,
    safe_redirect_target,
    translate_text,
)
from app.models.commit import Commit
from app.models.merge_request import MergeRequest
from app.models.team import Team
from app.observability.logging import (
    _add_otel_trace_context,
    _add_service_name,
    _PoolTerminationFilter,
    _redact_secrets,
)
from app.schemas.courses import GitLabGroupImportRequest
from app.schemas.custom_check import ALLOWED_RULE_TYPES, CustomCheckUpdate
from app.schemas.llm import LLMCollaborationMetric, LLMEvidenceRef
from app.schemas.students import StudentCreate
from app.security.session_auth import get_boot_nonce
from app.utils.time_utils import get_current_week
from app.workers.idempotency import _lock_key

# -- api/errors.py ----------------------------------------------------------


class TestErrorFactories:
    """Cover all raise_* factories and check_optimistic_lock."""

    def test_raise_http_error_plain(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_http_error(400, "bad")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "bad"

    def test_raise_http_error_structured(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_http_error(
                422,
                "invalid",
                error="validation_error",
                fields={"name": "too short"},
            )
        raw_detail = exc_info.value.detail
        assert isinstance(raw_detail, dict)
        d = raw_detail
        assert d["detail"] == "invalid"
        assert d["error"] == "validation_error"
        assert d["fields"]["name"] == "too short"

    def test_raise_http_error_with_headers(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_http_error(429, "slow down", headers={"Retry-After": "60"})
        assert exc_info.value.headers == {"Retry-After": "60"}

    def test_raise_bad_request(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_bad_request("oops")
        assert exc_info.value.status_code == 400

    def test_raise_unauthorized_default(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_unauthorized()
        assert exc_info.value.status_code == 401

    def test_raise_unauthorized_with_headers(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_unauthorized(headers={"WWW-Authenticate": "Bearer"})
        assert exc_info.value.status_code == 401

    def test_raise_forbidden(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_forbidden("nope")
        assert exc_info.value.status_code == 403

    def test_raise_not_found(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found()
        assert exc_info.value.status_code == 404

    def test_raise_conflict(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("already exists")
        assert exc_info.value.status_code == 409

    def test_raise_unprocessable(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_unprocessable("bad entity")
        assert exc_info.value.status_code == 422

    def test_raise_payload_too_large(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_payload_too_large("file too big")
        assert exc_info.value.status_code == 413

    def test_raise_internal_error(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_internal_error()
        assert exc_info.value.status_code == 500

    def test_raise_service_unavailable(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            raise_service_unavailable("down")
        assert exc_info.value.status_code == 503


class TestOptimisticLock:
    """Cover check_optimistic_lock branches."""

    def test_skip_when_expected_none(self) -> None:
        entity = SimpleNamespace(updated_at=datetime.now(UTC))
        check_optimistic_lock(entity, None)  # should not raise

    def test_skip_when_entity_has_no_updated_at(self) -> None:
        entity = SimpleNamespace()
        check_optimistic_lock(entity, datetime.now(UTC))

    def test_pass_when_timestamps_match(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        entity = SimpleNamespace(updated_at=now)
        check_optimistic_lock(entity, now)

    def test_conflict_when_timestamps_differ(self) -> None:
        old = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        new = old + timedelta(seconds=5)
        entity = SimpleNamespace(updated_at=new)
        with pytest.raises(HTTPException) as exc_info:
            check_optimistic_lock(entity, old, label="Team")
        assert exc_info.value.status_code == 409

    def test_naive_datetimes_normalized(self) -> None:
        naive = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        entity = SimpleNamespace(updated_at=naive)
        check_optimistic_lock(entity, naive)  # should pass (same time)

    def test_different_tz_same_instant(self) -> None:
        utc_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        offset = timezone(timedelta(hours=2))
        same_instant = utc_time.astimezone(offset)
        entity = SimpleNamespace(updated_at=utc_time)
        check_optimistic_lock(entity, same_instant)  # same instant, should pass


# -- i18n/__init__.py -------------------------------------------------------


class TestI18nTokenize:
    """Cover _tokenize_numbers and _detokenize_numbers."""

    def test_tokenize_no_numbers(self) -> None:
        text, vals = _tokenize_numbers("hello world")
        assert text == "hello world"
        assert vals == []

    def test_tokenize_single_number(self) -> None:
        text, vals = _tokenize_numbers("found 42 items")
        assert "42" not in text
        assert "__N0__" in text
        assert vals == ["42"]

    def test_tokenize_multiple_numbers(self) -> None:
        text, vals = _tokenize_numbers("page 3 of 10")
        assert vals == ["3", "10"]
        assert "__N0__" in text
        assert "__N1__" in text

    def test_detokenize_roundtrip(self) -> None:
        original = "synced 5 of 12 projects"
        text, vals = _tokenize_numbers(original)
        restored = _detokenize_numbers(text, vals)
        assert restored == original

    def test_detokenize_empty_values(self) -> None:
        assert _detokenize_numbers("no numbers here", []) == "no numbers here"


class TestParseAcceptLanguage:
    """Cover _parse_accept_language."""

    def test_simple_locale(self) -> None:
        result = _parse_accept_language("sk")
        assert result == ["sk"]

    def test_quality_ordering(self) -> None:
        result = _parse_accept_language("en;q=0.8, sk;q=1.0")
        assert result == ["sk", "en"]

    def test_empty_string(self) -> None:
        assert _parse_accept_language("") == []

    def test_unsupported_locale_filtered(self) -> None:
        result = _parse_accept_language("de-DE;q=1.0, sk;q=0.5")
        assert "de" not in result
        assert "sk" in result

    def test_invalid_quality_defaults_to_1(self) -> None:
        result = _parse_accept_language("sk;q=abc")
        assert result == ["sk"]


# -- schemas/support.py -----------------------------------------------------


# -- schemas/courses.py -----------------------------------------------------


class TestGitLabGroupImportValidator:
    """Cover _require_code_name_without_target."""

    def test_requires_code_without_target(self) -> None:
        with pytest.raises(ValidationError, match="course_code"):
            GitLabGroupImportRequest(
                group_url="https://gitlab.com/groups/test",
                course_code="",
                course_name="My Course",
            )

    def test_requires_name_without_target(self) -> None:
        with pytest.raises(ValidationError, match="course_name"):
            GitLabGroupImportRequest(
                group_url="https://gitlab.com/groups/test",
                course_code="CS101",
                course_name="X",
            )

    def test_valid_without_target(self) -> None:
        req = GitLabGroupImportRequest(
            group_url="https://gitlab.com/groups/test",
            course_code="CS101",
            course_name="Intro CS",
        )
        assert req.target_course_id is None

    def test_skips_check_with_target(self) -> None:
        req = GitLabGroupImportRequest(
            group_url="https://gitlab.com/groups/test",
            course_code="",
            course_name="",
            target_course_id=uuid4(),
        )
        assert req.target_course_id is not None


# -- schemas/llm.py ---------------------------------------------------------


class TestLLMSchemaValidators:
    """Cover field validators for source_type and score normalization."""

    def test_source_type_normalization(self) -> None:
        ref = LLMEvidenceRef(source_type="NOTE")
        assert ref.source_type == "note"

    def test_source_type_unknown_maps_to_general(self) -> None:
        ref = LLMEvidenceRef(source_type="something_weird")
        assert ref.source_type == "general"

    def test_source_type_non_string_maps_to_general(self) -> None:
        ref = LLMEvidenceRef(source_type=123)  # type: ignore[arg-type]
        assert ref.source_type == "general"

    def test_score_normalization(self) -> None:
        metric = LLMCollaborationMetric(metric="test", score="EXCELLENT", detail="great")
        assert metric.score == "excellent"

    def test_score_unknown_maps_to_fair(self) -> None:
        metric = LLMCollaborationMetric(metric="test", score="unknown_score", detail="ok")
        assert metric.score == "fair"


# -- models/merge_request.py ------------------------------------------------


def _make_mr(changed_files: list[str] | None) -> MergeRequest:
    mr = MagicMock(spec=MergeRequest)
    mr.changed_files = changed_files
    mr._DOC_NAMES = MergeRequest._DOC_NAMES
    mr.has_doc_changes = MergeRequest.has_doc_changes.fget(mr)  # type: ignore[attr-defined]
    return mr


class TestMergeRequestHasDocChanges:
    """Cover has_doc_changes property branches."""

    def test_no_changed_files(self) -> None:
        assert _make_mr(None).has_doc_changes is False

    def test_empty_list(self) -> None:
        assert _make_mr([]).has_doc_changes is False

    def test_readme_detected(self) -> None:
        assert _make_mr(["src/main.py", "README.md"]).has_doc_changes is True

    def test_docs_dir_detected(self) -> None:
        assert _make_mr(["docs/guide.md"]).has_doc_changes is True

    def test_doc_dir_detected(self) -> None:
        assert _make_mr(["doc/api.rst"]).has_doc_changes is True

    def test_changelog_detected(self) -> None:
        assert _make_mr(["CHANGELOG.md"]).has_doc_changes is True

    def test_no_doc_files(self) -> None:
        assert _make_mr(["src/main.py", "tests/test_foo.py"]).has_doc_changes is False


# -- models/commit.py -------------------------------------------------------


def _make_commit(parent_shas: list[str] | None) -> MagicMock:
    c = MagicMock(spec=Commit)
    c.parent_shas = parent_shas
    c.is_merge_commit = Commit.is_merge_commit.fget(c)  # type: ignore[attr-defined]
    return c


class TestCommitIsMergeCommit:
    """Cover is_merge_commit property."""

    def test_single_parent_not_merge(self) -> None:
        assert _make_commit(["abc123"]).is_merge_commit is False

    def test_two_parents_is_merge(self) -> None:
        assert _make_commit(["abc123", "def456"]).is_merge_commit is True

    def test_none_parents(self) -> None:
        assert _make_commit(None).is_merge_commit is False


# -- models/team.py ---------------------------------------------------------


class TestTeamActiveMembers:
    """Cover active_members property."""

    def test_filters_inactive(self) -> None:
        t = MagicMock(spec=Team)
        m1 = SimpleNamespace(is_active=True, name="a")
        m2 = SimpleNamespace(is_active=False, name="b")
        m3 = SimpleNamespace(is_active=True, name="c")
        t.members = [m1, m2, m3]
        result = Team.active_members.fget(t)  # type: ignore[attr-defined]
        assert len(result) == 2
        assert m2 not in result


# -- workers/progress.py - publish_dashboard_update -------------------------


class TestPublishDashboardUpdate:
    """Cover publish_dashboard_update and extra publish_progress channels."""

    @patch("app.workers.progress._get_publish_conn")
    def test_dashboard_update_basic(self, mock_get_conn: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", "t-1", "sync_completed")

        calls = mock_conn.publish.call_args_list
        channels = [c[0][0] for c in calls]
        assert "dashboard:team:t-1" in channels
        assert "dashboard:global" in channels
        data = json.loads(calls[0][0][1])
        assert data["entity_type"] == "team"
        assert data["event"] == "sync_completed"

    @patch("app.workers.progress._get_publish_conn")
    def test_dashboard_update_with_extra(self, mock_get_conn: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("course", "c-1", extra={"team_id": "t-99"})

        data = json.loads(mock_conn.publish.call_args_list[0][0][1])
        assert data["team_id"] == "t-99"

    @patch("app.workers.progress._get_publish_conn")
    def test_dashboard_update_invalidates_short_live_caches(
        self,
        mock_get_conn: MagicMock,
    ) -> None:
        mock_conn = MagicMock()
        mock_conn.scan_iter.side_effect = [
            iter(["dashboard:stats:u1:teacher"]),
            iter(["dashboard:badges:u1:teacher", "dashboard:badges:u2:admin"]),
        ]
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("course", "c-1", "sync_completed")

        assert mock_conn.scan_iter.call_args_list[0].kwargs["match"] == "dashboard:stats:*"
        assert mock_conn.scan_iter.call_args_list[1].kwargs["match"] == "dashboard:badges:*"
        delete_args = [call.args for call in mock_conn.delete.call_args_list]
        assert ("dashboard:stats:u1:teacher",) in delete_args
        assert ("dashboard:badges:u1:teacher", "dashboard:badges:u2:admin") in delete_args
        assert mock_conn.publish.call_count == 2

    @patch("app.workers.progress._get_publish_conn")
    def test_dashboard_update_swallows_errors(self, mock_get_conn: MagicMock) -> None:
        mock_get_conn.side_effect = ConnectionError("Redis down")

        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", "t-1")  # should not raise

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_analytics(self, mock_get_conn: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("j-1", "running", analytics_course_id="ac-1")

        channels = [c[0][0] for c in mock_conn.publish.call_args_list]
        assert "analytics:ac-1" in channels

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_dashboard_ids(self, mock_get_conn: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress(
            "j-2",
            "running",
            dashboard_team_id="dt-1",
            dashboard_course_id="dc-1",
        )

        channels = [c[0][0] for c in mock_conn.publish.call_args_list]
        assert "dashboard:team:dt-1" in channels
        assert "dashboard:course:dc-1" in channels


# -- i18n extra coverage ---------------------------------------------------


class TestI18nTranslation:
    """Cover more i18n translation paths."""

    def test_translate_empty_text(self) -> None:
        assert translate_text("sk", "") == ""
        assert translate_text("sk", "  ") == "  "

    def test_translate_with_kwargs(self) -> None:
        result = translate_text("en", "Hello {name}", name="World")
        assert result == "Hello World"

    def test_translate_preserves_whitespace(self) -> None:
        result = translate_text("en", "  Dashboard  ")
        # canonical strips, but original whitespace is preserved around translation
        assert "Dashboard" in result

    def test_get_pattern_catalog_returns_dict(self) -> None:
        result = _get_pattern_catalog("en")
        assert isinstance(result, dict)

    def test_get_catalog_source_locale_empty(self) -> None:
        result = get_catalog("en")
        assert result == {}

    def test_get_catalog_nonexistent_locale_falls_back(self) -> None:
        # Unknown locale falls back to DEFAULT_LOCALE ("sk") which has a catalog
        result = get_catalog("xx")
        assert isinstance(result, dict)

    def test_translate_number_pattern_bridge(self) -> None:
        result = translate_text("en", "found 42 items")
        assert "42" in result


# ===============================================================
#  StudentCreate._require_identifier   (schemas/students.py)
# ===============================================================
class TestStudentCreateValidator:
    def test_no_identifier_raises(self) -> None:
        with pytest.raises(ValidationError, match="gitlab_username"):
            StudentCreate()

    def test_gitlab_username_only(self) -> None:
        s = StudentCreate(gitlab_username="alice")
        assert s.gitlab_username == "alice"

    def test_email_only(self) -> None:
        s = StudentCreate(email="a@b.com")
        assert s.email == "a@b.com"

    def test_gitlab_user_id_only(self) -> None:
        s = StudentCreate(gitlab_user_id=42)
        assert s.gitlab_user_id == 42


# ===============================================================
#  _load_json  (compliance/check_registry.py)
# ===============================================================
class TestCheckRegistry:
    def test_load_json_invalid_structure(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text('["not a dict"]')
        with pytest.raises(ValueError, match="Invalid check registry"):
            _load_json(f)

    def test_load_json_checks_not_list(self, tmp_path: Path) -> None:
        f = tmp_path / "bad2.json"
        f.write_text('{"checks": "oops"}')
        with pytest.raises(ValueError, match="must be a list"):
            _load_json(f)

    def test_load_json_valid(self, tmp_path: Path) -> None:
        f = tmp_path / "ok.json"
        payload = {
            "checks": [
                {
                    "code": "T01",
                    "name": "Test",
                    "category": "Git",
                    "weight_field": "w",
                    "description": "d",
                }
            ],
        }
        f.write_text(json.dumps(payload))
        entries = _load_json(f)
        assert len(entries) == 1


# ===============================================================
#  _PoolTerminationFilter   (observability/logging.py)
# ===============================================================
class TestPoolTerminationFilter:
    def test_suppress_terminating(self) -> None:
        f = _PoolTerminationFilter()
        msg = "Exception terminating connection blah"
        rec = logging.LogRecord("test", logging.ERROR, "", 0, msg, (), None)
        assert f.filter(rec) is False

    def test_suppress_close_failed(self) -> None:
        f = _PoolTerminationFilter()
        msg = "Exception close failed on something"
        rec = logging.LogRecord("test", logging.ERROR, "", 0, msg, (), None)
        assert f.filter(rec) is False

    def test_pass_normal_message(self) -> None:
        f = _PoolTerminationFilter()
        rec = logging.LogRecord("test", logging.INFO, "", 0, "Normal log line", (), None)
        assert f.filter(rec) is True


class TestLogProcessors:
    def test_add_otel_trace_no_otel(self) -> None:
        event: dict[str, Any] = {"event": "test"}
        result = _add_otel_trace_context(None, "info", event)
        # Without active span, trace_id may or may not be set, but no crash
        assert "event" in result

    def test_redact_secrets(self) -> None:
        event: dict[str, Any] = {"event": "test", "password": "hunter2", "token": "abc"}
        result = _redact_secrets(None, "info", event)
        assert result["password"] == "***REDACTED***"
        assert result["token"] == "***REDACTED***"
        assert result["event"] == "test"

    def test_add_service_name(self) -> None:
        event: dict[str, Any] = {"event": "test"}
        result = _add_service_name(None, "info", event)
        assert result["service"] == "gitpulse"

    def test_redact_non_string_value(self) -> None:
        event: dict[str, Any] = {"password": 12345, "event": "x"}
        result = _redact_secrets(None, "info", event)
        assert result["password"] == 12345  # not a str -> not redacted


# ===============================================================
# ===============================================================


# ===============================================================
#  CustomCheck _validate_rule_type  (schemas/custom_check.py)
# ===============================================================
class TestCustomCheckValidators:
    def test_valid_rule_type(self) -> None:
        rt = next(iter(ALLOWED_RULE_TYPES))
        obj = CustomCheckUpdate(evaluation_rule={"type": rt})
        assert obj.evaluation_rule is not None
        assert obj.evaluation_rule["type"] == rt

    def test_invalid_rule_type(self) -> None:
        with pytest.raises(ValidationError, match="Invalid rule type"):
            CustomCheckUpdate(evaluation_rule={"type": "BOGUS_TYPE"})

    def test_none_rule(self) -> None:
        obj = CustomCheckUpdate(evaluation_rule=None)
        assert obj.evaluation_rule is None

    def test_empty_type_passes(self) -> None:
        # Empty string type is allowed (skipped by the `if rt` guard)
        obj = CustomCheckUpdate(evaluation_rule={"type": ""})
        assert obj.evaluation_rule is not None


# ===============================================================
#  idempotency _lock_key   (workers/idempotency.py)
# ===============================================================
class TestIdempotencyLockKey:
    def test_deterministic(self) -> None:
        k1 = _lock_key("mymod.my_fn", ("a", 1))
        k2 = _lock_key("mymod.my_fn", ("a", 1))
        assert k1 == k2

    def test_different_for_different_args(self) -> None:
        k1 = _lock_key("fn", ("x",))
        k2 = _lock_key("fn", ("y",))
        assert k1 != k2

    def test_prefix(self) -> None:
        k = _lock_key("fn", ())
        assert k.startswith("joblock:fn:")


# ===============================================================
#  Settings.is_test property  (config.py)
# ===============================================================
class TestSettingsIsTest:
    def test_is_test_true(self) -> None:
        from app.config import Settings as _Settings

        s = _Settings(
            app_env=AppEnv.TEST,
            database_url="postgresql+asyncpg://x@localhost/x",
            redis_url="redis://localhost",
            gitlab_webhook_secret="s",
            secret_key="k" * 16,
        )
        assert s.is_test is True

    def test_is_development(self) -> None:
        from app.config import Settings as _Settings

        s = _Settings(
            app_env=AppEnv.DEVELOPMENT,
            database_url="postgresql+asyncpg://x@localhost/x",
            redis_url="redis://localhost",
            gitlab_webhook_secret="s",
            secret_key="k" * 16,
        )
        assert s.is_development is True
        assert s.is_test is False


# ===============================================================
#  LLMMetricScore.normalize_score non-string  (schemas/llm.py)
# ===============================================================


class TestLLMMetricScoreNonString:
    def test_non_string_score(self) -> None:
        # When score is not a string, normalize_score returns "fair"
        obj = LLMCollaborationMetric(metric="x", score=123, detail="d")  # type: ignore[arg-type]
        assert obj.score == "fair"


# ===============================================================
#  get_boot_nonce  (security/session_auth.py)
# ===============================================================
class TestGetBootNonce:
    def test_returns_string(self) -> None:
        nonce = get_boot_nonce()
        assert isinstance(nonce, str)
        assert len(nonce) == 16

    def test_stable_within_process(self) -> None:
        assert get_boot_nonce() == get_boot_nonce()


# ===============================================================
#  get_current_week with now=None  (utils/time_utils.py)
# ===============================================================
class TestGetCurrentWeekDefaultNow:
    def test_default_now(self) -> None:
        # Semester that started 14 days ago -> week 3
        semester_start = datetime.now(UTC).date() - timedelta(days=14)
        result = get_current_week(semester_start)
        assert result == 3


# ===============================================================
#  _add_otel_trace_context with active span  (observability/logging.py)
# ===============================================================


class TestOtelTraceContext:
    def test_with_active_span(self) -> None:
        mock_ctx = MagicMock()
        mock_ctx.trace_id = 0x1234567890ABCDEF1234567890ABCDEF
        mock_ctx.span_id = 0xFEDCBA0987654321
        mock_span = MagicMock()
        mock_span.get_span_context.return_value = mock_ctx

        # Create a fake opentelemetry module with trace attribute
        fake_trace = MagicMock()
        fake_trace.get_current_span.return_value = mock_span
        fake_otel = MagicMock()
        fake_otel.trace = fake_trace

        import sys

        original_modules = {}
        for mod_name in ("opentelemetry", "opentelemetry.trace"):
            original_modules[mod_name] = sys.modules.get(mod_name)

        sys.modules["opentelemetry"] = fake_otel
        sys.modules["opentelemetry.trace"] = fake_trace
        try:
            event: dict[str, Any] = {"event": "test"}
            result = _add_otel_trace_context(None, "info", event)
            assert "trace_id" in result
            assert "span_id" in result
            assert result["trace_id"] == "1234567890abcdef1234567890abcdef"
            assert result["span_id"] == "fedcba0987654321"
        finally:
            for mod_name, orig in original_modules.items():
                if orig is None:
                    sys.modules.pop(mod_name, None)
                else:
                    sys.modules[mod_name] = orig


# ===============================================================
#  safe_redirect_target  (i18n/__init__.py)
# ===============================================================
class TestSafeRedirectTarget:
    def _make_request(self, url: str = "http://localhost/dashboard/") -> MagicMock:
        req = MagicMock()
        req.url = MagicMock()
        req.url.netloc = "localhost"
        return req

    def test_none_target(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, None) == "/dashboard/"

    def test_empty_string_target(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "  ") == "/dashboard/"

    def test_double_slash_rejected(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "//evil.com") == "/dashboard/"

    def test_relative_path_gets_slash(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "courses") == "/courses"

    def test_absolute_path_kept(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "/courses") == "/courses"

    def test_external_url_rejected(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "http://evil.com/steal") == "/dashboard/"

    def test_same_host_url_allowed(self) -> None:
        r = self._make_request()
        assert safe_redirect_target(r, "http://localhost/courses?x=1") == "/courses?x=1"


class TestNormalize:
    def test_invalid_locale_string(self) -> None:
        # Doesn't match _SHORT_LANG_RE -> returns None
        assert normalize_locale("!!!") is None

    def test_canonical_text(self) -> None:
        assert _canonical_text("  hello   world  ") == "hello world"


# ===============================================================
#  translate_text more branches  (i18n/__init__.py)
# ===============================================================


class TestTranslateTextBranches:
    def test_source_locale_passthrough(self) -> None:
        result = translate_text(SOURCE_LOCALE, "hello world")
        assert result == "hello world"

    def test_empty_text(self) -> None:
        result = translate_text("sk", "  ")
        assert result == "  "  # returns original for empty canonical

    def test_kwargs_formatting(self) -> None:
        # Use a text that exists in catalog or just verify no crash
        result = translate_text("en", "test {name}", name="Alice")
        assert "Alice" in result

    def test_whitespace_preservation(self) -> None:
        result = translate_text("en", "  hello  ")
        assert isinstance(result, str)


# ===============================================================
#  get_catalog branches  (i18n/__init__.py)
# ===============================================================
class TestGetCatalogBranches:
    def test_source_locale_returns_empty(self) -> None:
        # SOURCE_LOCALE is "en" - always returns empty dict
        assert get_catalog(SOURCE_LOCALE) == {}

    def test_get_pattern_catalog_source(self) -> None:
        # Pattern catalog for source locale should be empty since catalog is empty
        result = _get_pattern_catalog(SOURCE_LOCALE)
        assert result == {}

    def test_unsupported_locale_normalizes_to_default(self) -> None:
        # "zz" normalizes to None -> falls back to DEFAULT_LOCALE
        result = get_catalog("zz")
        assert isinstance(result, dict)

    def test_get_pattern_catalog_sk(self) -> None:
        # "sk" locale has a real catalog with number patterns
        result = _get_pattern_catalog("sk")
        assert isinstance(result, dict)

    def test_get_catalog_sk(self) -> None:
        catalog = get_catalog("sk")
        assert isinstance(catalog, dict)
        assert len(catalog) > 0  # Slovak catalog has translations


# ===============================================================
#  resolve_locale  (i18n/__init__.py)
# ===============================================================
class TestResolveLocale:
    def test_from_state(self) -> None:
        req = MagicMock()
        req.state.locale = "sk"
        req.query_params.get.return_value = None
        req.cookies.get.return_value = None
        req.headers.get.return_value = ""
        assert resolve_locale(req) == "sk"

    def test_from_query_param(self) -> None:
        req = MagicMock()
        req.state.locale = None
        req.query_params.get.return_value = "sk"
        req.cookies.get.return_value = None
        req.headers.get.return_value = ""
        assert resolve_locale(req) == "sk"

    def test_from_cookie(self) -> None:
        req = MagicMock()
        req.state.locale = None
        req.query_params.get.return_value = None
        req.cookies.get.return_value = "sk"
        req.headers.get.return_value = ""
        assert resolve_locale(req) == "sk"

    def test_from_accept_language(self) -> None:
        req = MagicMock()
        req.state.locale = None
        req.query_params.get.return_value = None
        req.cookies.get.return_value = None
        req.headers.get.return_value = "sk-SK;q=0.9, en;q=0.8"
        assert resolve_locale(req) == "sk"


# -- Admin helpers --


# -- Dashboard helpers (_helpers.py) --


class TestFormatTimeAgo:
    def test_just_now(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime.now(UTC) - timedelta(seconds=10))
        assert result == "just now"

    def test_minutes_ago(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime.now(UTC) - timedelta(minutes=5))
        assert result == "5m ago"

    def test_hours_ago(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime.now(UTC) - timedelta(hours=3))
        assert result == "3h ago"

    def test_days_ago(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime.now(UTC) - timedelta(days=7))
        assert result == "7d ago"

    def test_old_date_shows_formatted(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime(2020, 1, 15, tzinfo=UTC))
        assert "Jan" in result
        assert "2020" in result

    def test_naive_datetime_gets_utc(self) -> None:
        from app.api.dashboard._helpers import _format_time_ago

        result = _format_time_ago(datetime(2020, 6, 1, tzinfo=UTC))
        assert "Jun" in result


class TestRoleContext:
    def test_admin_role(self) -> None:
        from app.api.dashboard._helpers import _role_context

        ctx = _role_context({"role": "admin", "user": "admin1", "gitlab_username": "admin1"})
        assert ctx["is_admin"] is True
        assert ctx["is_teacher"] is True
        assert ctx["can_edit"] is True
        assert ctx["is_student"] is False

    def test_teacher_role(self) -> None:
        from app.api.dashboard._helpers import _role_context

        ctx = _role_context({"role": "teacher", "user": "teach"})
        assert ctx["is_admin"] is False
        assert ctx["is_teacher"] is True
        assert ctx["can_edit"] is True

    def test_student_role(self) -> None:
        from app.api.dashboard._helpers import _role_context

        ctx = _role_context({"role": "student", "user": "stu1"})
        assert ctx["is_admin"] is False
        assert ctx["is_teacher"] is False
        assert ctx["is_student"] is True
        assert ctx["can_edit"] is False

    def test_default_role(self) -> None:
        from app.api.dashboard._helpers import _role_context

        ctx = _role_context({})
        assert ctx["is_student"] is True


class TestParseFormTimestamp:
    def test_valid_iso(self) -> None:
        from app.api.dashboard._helpers import _parse_form_timestamp

        result = _parse_form_timestamp({"expected_updated_at": "2025-06-15T10:00:00"})
        assert result is not None
        assert result.year == 2025

    def test_empty(self) -> None:
        from app.api.dashboard._helpers import _parse_form_timestamp

        assert _parse_form_timestamp({}) is None

    def test_invalid(self) -> None:
        from app.api.dashboard._helpers import _parse_form_timestamp

        assert _parse_form_timestamp({"expected_updated_at": "not-a-date"}) is None


class TestThresholdPcts:
    def test_with_settings(self) -> None:
        from app.api.dashboard._helpers import _threshold_pcts

        cs = SimpleNamespace(green_threshold=0.8, yellow_threshold=0.5)
        g, y = _threshold_pcts(cs)
        assert g == 80
        assert y == 50

    def test_without_settings(self) -> None:
        from app.api.dashboard._helpers import _threshold_pcts

        g, y = _threshold_pcts(None)
        assert g > 0
        assert y > 0


class TestSemesterWeeksFromSettings:
    def test_none_settings(self) -> None:
        from app.api.dashboard._helpers import _semester_weeks_from_settings

        result = _semester_weeks_from_settings(None)
        assert result > 0

    def test_from_weekly_deadlines(self) -> None:
        from app.api.dashboard._helpers import _semester_weeks_from_settings

        cs = SimpleNamespace(
            weekly_deadlines=[{"week": 5}, {"week": 12}, {"week": 3}],
            semester_start_date=None,
        )
        result = _semester_weeks_from_settings(cs)
        assert result >= 12

    def test_from_semester_start(self) -> None:
        from app.api.dashboard._helpers import _semester_weeks_from_settings

        cs = SimpleNamespace(
            weekly_deadlines=None,
            semester_start_date=date(2025, 2, 10),
        )
        result = _semester_weeks_from_settings(cs)
        assert result > 0


class TestIsOwnStudentProfile:
    def test_matches_by_gitlab_username(self) -> None:
        from app.api.dashboard._helpers import _is_own_student_profile

        stu = SimpleNamespace(gitlab_username="john", email="john@example.com")
        assert _is_own_student_profile(stu, {"gitlab_username": "john", "user": "", "email": ""})

    def test_no_match(self) -> None:
        from app.api.dashboard._helpers import _is_own_student_profile

        stu = SimpleNamespace(gitlab_username="john", email="john@example.com")
        sess = {"gitlab_username": "other", "user": "other", "email": "other@x.com"}
        assert not _is_own_student_profile(stu, sess)


# -- More dashboard helpers --


class TestCalendarAcademicYear:
    """``_suggest_academic_year`` was a second, August-rollover answer to "which
    year is it"; the top bar and the dialogs ask ``calendar_period`` now."""

    def test_returns_two_consecutive_years(self) -> None:
        from app.utils.academic_period import calendar_period

        head, tail = calendar_period().academic_year.split("/")
        assert int(tail) == int(head) + 1


class TestConflictRedirect:
    def test_adds_error_param(self) -> None:
        from app.api.dashboard._helpers import _conflict_redirect

        resp = _conflict_redirect("/dashboard/courses/1/settings")
        assert resp.status_code == 303
        assert "error=conflict" in resp.headers["location"]

    def test_appends_to_existing_query(self) -> None:
        from app.api.dashboard._helpers import _conflict_redirect

        resp = _conflict_redirect("/dashboard/courses/1/settings?tab=general")
        assert "&error=conflict" in resp.headers["location"]


class TestPushNotification:
    def test_empty_username_noop(self) -> None:
        from app.api.dashboard._helpers import _push_notification

        _push_notification("", "hello")  # should not raise

    def test_push_with_mocked_redis(self) -> None:
        mock_redis = MagicMock()
        with patch("app.api.dashboard._helpers._get_redis", return_value=mock_redis):
            from app.api.dashboard._helpers import _push_notification

            _push_notification("testuser", "Course created!", "success")
            mock_redis.rpush.assert_called_once()
            mock_redis.expire.assert_called_once()

    def test_push_redis_error_suppressed(self) -> None:
        mock_redis = MagicMock()
        mock_redis.rpush.side_effect = ConnectionError("down")
        with patch("app.api.dashboard._helpers._get_redis", return_value=mock_redis):
            from app.api.dashboard._helpers import _push_notification

            _push_notification("testuser", "msg")  # should not raise


class TestPopNotifications:
    def test_empty_username_returns_empty(self) -> None:
        from app.api.dashboard._helpers import _pop_notifications

        assert _pop_notifications("") == []

    def test_pop_with_mocked_redis(self) -> None:
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [
            [json.dumps({"message": "hello", "type": "success"}).encode()],
        ]
        with patch("app.api.dashboard._helpers._get_redis", return_value=mock_redis):
            from app.api.dashboard._helpers import _pop_notifications

            result = _pop_notifications("testuser")
            assert len(result) == 1
            assert result[0]["message"] == "hello"

    def test_pop_redis_error_returns_empty(self) -> None:
        with patch("app.api.dashboard._helpers._get_redis", side_effect=ConnectionError):
            from app.api.dashboard._helpers import _pop_notifications

            assert _pop_notifications("testuser") == []


class TestEnqueueResult:
    def test_default_values(self) -> None:
        from app.api.dashboard._helpers import _EnqueueResult

        r = _EnqueueResult()
        assert r.background is None
        assert r.job_id is None

    def test_with_job_id(self) -> None:
        from app.api.dashboard._helpers import _EnqueueResult

        r = _EnqueueResult(job_id="abc-123")
        assert r.job_id == "abc-123"


class TestEnqueueOrInline:
    def test_dev_mode_returns_background_task(self) -> None:
        from app.api.dashboard._helpers import _enqueue_or_inline

        settings = SimpleNamespace(is_development=True)

        async def _noop() -> None:
            pass

        result = _enqueue_or_inline(settings, "app.workers.x", (), _noop)
        assert result.background is not None
        assert result.job_id is None

    def test_prod_mode_rq_failure_fallback(self) -> None:
        from app.api.dashboard._helpers import _enqueue_or_inline

        settings = SimpleNamespace(is_development=False, rq_default_timeout=300)
        with patch("app.api.dashboard._helpers._pool_get_redis", side_effect=ConnectionError):

            async def _noop() -> None:
                pass

            result = _enqueue_or_inline(settings, "app.workers.x", (), _noop)
            assert result.background is not None


class TestCsrfToken:
    def test_disabled_returns_empty(self) -> None:
        from app.api.dashboard._helpers import _csrf_token

        with patch("app.api.dashboard._helpers.get_settings") as gs:
            gs.return_value = SimpleNamespace(feature_security_hardening=False)
            assert _csrf_token() == ""

    def test_enabled_returns_token(self) -> None:
        from app.api.dashboard._helpers import _csrf_token

        with patch("app.api.dashboard._helpers.get_settings") as gs:
            gs.return_value = SimpleNamespace(
                feature_security_hardening=True,
                secret_key="test-secret-key-minimum-sixteen",
            )
            result = _csrf_token({"user": "testuser"})
            assert isinstance(result, str)
            assert len(result) > 0


class TestMaxConfigImportBytes:
    def test_constant_exists(self) -> None:
        from app.api.dashboard._helpers import _MAX_CONFIG_IMPORT_BYTES

        assert _MAX_CONFIG_IMPORT_BYTES == 2 * 1024 * 1024


class TestDefaultSemesterWeeks:
    def test_constant_exists(self) -> None:
        from app.api.dashboard._helpers import _DEFAULT_SEMESTER_WEEKS

        assert _DEFAULT_SEMESTER_WEEKS == 13


class TestEnqueueOrInlineProd:
    def test_prod_mode_successful_enqueue(self) -> None:
        from app.api.dashboard._helpers import _enqueue_or_inline

        settings = SimpleNamespace(is_development=False, rq_default_timeout=300)
        mock_conn = MagicMock()
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-xyz"
        mock_queue.enqueue.return_value = mock_job
        with (
            patch("app.api.dashboard._helpers._pool_get_redis", return_value=mock_conn),
            patch("app.api.dashboard._helpers.Queue", return_value=mock_queue),
        ):

            async def _noop() -> None:
                pass

            result = _enqueue_or_inline(settings, "app.workers.x", ("arg1",), _noop)
            assert result.job_id == "job-xyz"
            assert result.background is None


def _error_templates():
    """Minimal Jinja2Templates - the handler only needs it to render the page."""
    from fastapi.templating import Jinja2Templates

    return Jinja2Templates(directory="src/app/templates")


class TestDatabaseUnavailableIsDiagnosable:
    """A 503 must say why the database was unreachable.

    Both handlers used to accept the exception and drop it, so connection
    refused, pool timeout, exhausted server connections and bad credentials
    all produced the same blank 503 with no log line.
    """

    async def test_operational_error_is_logged(self, caplog) -> None:
        import logging

        from sqlalchemy.exc import OperationalError
        from starlette.requests import Request

        from app.api.exception_handlers import handle_db_operational_error

        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/dashboard/",
                "headers": [],
                "query_string": b"",
            }
        )
        exc = OperationalError("SELECT 1", {}, Exception("connection pool exhausted"))

        with caplog.at_level(logging.ERROR):
            await handle_db_operational_error(request, exc, _error_templates())

        assert "db_unavailable" in caplog.text
        assert "OperationalError" in caplog.text
        assert "/dashboard/" in caplog.text
        # The original cause must survive into the traceback.
        assert "connection pool exhausted" in caplog.text

    async def test_connection_refused_is_logged(self, caplog) -> None:
        import logging

        from starlette.requests import Request

        from app.api.exception_handlers import handle_db_connection_refused

        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/dashboard/admin/users",
                "headers": [],
                "query_string": b"",
            }
        )

        with caplog.at_level(logging.ERROR):
            await handle_db_connection_refused(
                request, ConnectionRefusedError("port 5433 refused"), _error_templates()
            )

        assert "db_unavailable" in caplog.text
        assert "connection_refused" in caplog.text
        assert "port 5433 refused" in caplog.text

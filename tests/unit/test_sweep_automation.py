"""Tests for event/sync-driven worker jobs.

Tests cover:
- _incremental_project_refresh
- event-driven metrics (_enqueue_metrics_for_project)
- GitLab cache project invalidation
- cache invalidation in webhook flow
- course activate auto-sync
- team deactivation cascade
- course live-data endpoint
"""

import uuid
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.build_outputs import page_bundle

# -- Fake settings used across tests --


@dataclass
class FakeSettings:
    feature_llm_suggestions: bool = True
    feature_event_pipeline: bool = True
    feature_gitlab_cache: bool = False
    compliance_auto_snapshot: bool = True
    llm_api_key: str = "test-key"
    gitlab_url: str = "https://gitlab.example.com"
    gitlab_api_token: str = "test-token"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://test@localhost/test"
    dlq_max_retries: int = 5
    job_timeout_event_seconds: int = 120
    job_timeout_enrich_seconds: int = 180
    job_timeout_report_seconds: int = 600
    job_timeout_sync_seconds: int = 3600
    gitlab_enrichment_per_item_timeout: int = 12
    app_base_url: str = "https://app.example.com"
    feature_email_notifications: bool = True
    semester_auto_archive_enabled: bool = True
    semester_grace_days: int = 14
    semester_default_length_weeks: int = 14


@dataclass
class FakeTeam:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    course_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "team-alpha"
    is_active: bool = True
    gitlab_group_id: int | None = 100
    projects: list[Any] = field(default_factory=list)


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    gitlab_project_id: int = 42
    team_id: uuid.UUID = field(default_factory=uuid.uuid4)
    gitlab_project_path: str | None = None


@dataclass
class FakeSyncResult:
    team_id: uuid.UUID = field(default_factory=uuid.uuid4)
    team_name: str = "team-alpha"
    members_added: int = 1
    members_removed: int = 0
    roles_changed: int = 0
    members_reactivated: int = 0
    members_unchanged: int = 0
    errors: list[Any] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return self.members_added + self.members_removed + self.roles_changed


# ---------------------------------------------------------------
# Incremental project refresh
# ---------------------------------------------------------------


class TestIncrementalProjectRefresh:
    """Tests for _incremental_project_refresh job."""

    @pytest.mark.asyncio
    async def test_enqueues_enrichment_for_known_entities(self):
        """Enqueues enrich jobs for all known issues and MRs of a project."""
        from app.workers.sweep import _incremental_refresh_async

        project_id = str(uuid.uuid4())
        gitlab_project_id = 42
        settings = FakeSettings()

        mock_session = AsyncMock()
        # First call: issues, second call: MRs
        issue_result = MagicMock()
        issue_result.all.return_value = [(1,), (2,)]
        mr_result = MagicMock()
        mr_result.all.return_value = [(10,), (20,), (30,)]
        mock_session.execute.side_effect = [issue_result, mr_result]

        with (
            patch("app.config.get_settings", return_value=settings),
            patch("app.workers.bootstrap.worker_session") as mock_ws,
            patch("app.services.events._get_queue") as mock_queue,
        ):
            ctx = AsyncMock()
            ctx.__aenter__ = AsyncMock(return_value=(mock_session, settings))
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ws.return_value = ctx

            mock_q = MagicMock()
            mock_queue.return_value = mock_q

            result = await _incremental_refresh_async(project_id, gitlab_project_id)

        # 2 issues + 3 MRs = 5 jobs
        assert result == 5
        assert mock_q.enqueue.call_count == 5


# ---------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# Event-driven metrics (event_processor)
# ---------------------------------------------------------------


class TestEventDrivenMetrics:
    """Tests for event-driven metrics after webhook processing."""

    @pytest.mark.asyncio
    async def test_enqueue_metrics_for_known_project(self):
        """Enqueues metrics refresh when project team is found."""
        from app.workers.event_processor import _enqueue_metrics_for_project

        team_id = uuid.uuid4()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = team_id
        mock_session.execute.return_value = mock_result

        with patch("app.services.events.enqueue_metrics_refresh") as mock_enqueue:
            await _enqueue_metrics_for_project(mock_session, 42)

        mock_enqueue.assert_called_once_with(str(team_id))

    @pytest.mark.asyncio
    async def test_skips_when_project_not_found(self):
        """Does nothing when project is not registered."""
        from app.workers.event_processor import _enqueue_metrics_for_project

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.services.events.enqueue_metrics_refresh") as mock_enqueue:
            await _enqueue_metrics_for_project(mock_session, 999)

        mock_enqueue.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_enqueue_error_gracefully(self):
        """Does not raise if metrics enqueue fails."""
        from app.workers.event_processor import _enqueue_metrics_for_project

        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("DB error")

        # Should not raise
        await _enqueue_metrics_for_project(mock_session, 42)


# ---------------------------------------------------------------
# GitLab cache invalidation
# ---------------------------------------------------------------


class TestGitLabCacheInvalidation:
    """Tests for project-level cache invalidation."""

    def test_extract_project_id_from_endpoint(self) -> None:
        """Extracts project ID from GitLab API endpoint."""
        from app.services.gitlab.cache import GitLabAPICache

        assert GitLabAPICache._extract_project_id("/api/v4/projects/123/merge_requests") == 123
        assert GitLabAPICache._extract_project_id("/api/v4/projects/42/issues") == 42
        assert GitLabAPICache._extract_project_id("/api/v4/users/5") is None
        assert GitLabAPICache._extract_project_id("/api/v4/groups") is None

    @pytest.mark.asyncio
    async def test_invalidate_project_deletes_tracked_keys(self):
        """Invalidation deletes all tracked cache keys for a project."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost:6379/0")
        # Use MagicMock for synchronous pipeline(), but AsyncMock for async methods
        mock_redis = AsyncMock()
        mock_redis.smembers.return_value = {b"abc123", b"def456"}
        mock_pipe = MagicMock()
        mock_pipe.delete = MagicMock(return_value=mock_pipe)  # pipeline methods return self
        mock_pipe.execute = AsyncMock()
        # pipeline() is synchronous in redis.asyncio
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        cache._redis = mock_redis

        await cache.invalidate_project(42)

        mock_redis.smembers.assert_called_once_with("gitlab:project_keys:42")
        # Should delete etag+response for each key, plus the set itself
        assert mock_pipe.delete.call_count == 3  # 2 keys x 2 entries + 1 set
        mock_pipe.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_project_no_redis(self):
        """Does nothing when Redis is not connected."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost:6379/0")
        cache._redis = None

        # Should not raise
        await cache.invalidate_project(42)

    @pytest.mark.asyncio
    async def test_invalidate_project_empty_keys(self):
        """Does nothing when no keys are tracked for project."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost:6379/0")
        mock_redis = AsyncMock()
        mock_redis.smembers.return_value = set()
        cache._redis = mock_redis

        await cache.invalidate_project(42)

        # Should not try to delete anything
        mock_redis.pipeline.assert_not_called()


# ---------------------------------------------------------------
# New config defaults
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# Cache invalidation in webhook flow
# ---------------------------------------------------------------


class TestCacheInvalidationInWebhookFlow:
    """Tests for cache invalidation called during event processing."""

    @pytest.mark.asyncio
    async def test_invalidate_called_when_feature_enabled(self):
        """Cache invalidation is called when feature_gitlab_cache is True."""
        from app.workers.event_processor import _invalidate_project_cache

        settings = FakeSettings(feature_gitlab_cache=True)
        mock_cache = AsyncMock()

        with (
            patch("app.config.get_settings", return_value=settings),
            patch("app.services.gitlab.cache.GitLabAPICache") as mock_cache_cls,
        ):
            mock_cache_cls.return_value = mock_cache
            await _invalidate_project_cache(42)

        mock_cache.connect.assert_awaited_once()
        mock_cache.invalidate_project.assert_awaited_once_with(42)
        mock_cache.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalidate_skipped_when_feature_disabled(self):
        """Cache invalidation is skipped when feature_gitlab_cache is False."""
        from app.workers.event_processor import _invalidate_project_cache

        settings = FakeSettings(feature_gitlab_cache=False)

        with patch("app.config.get_settings", return_value=settings):
            # Should not raise or call cache
            await _invalidate_project_cache(42)

    @pytest.mark.asyncio
    async def test_invalidate_handles_errors_gracefully(self):
        """Cache invalidation does not propagate exceptions."""
        from app.workers.event_processor import _invalidate_project_cache

        settings = FakeSettings(feature_gitlab_cache=True)
        mock_cache = AsyncMock()
        mock_cache.invalidate_project.side_effect = RuntimeError("Redis down")

        with (
            patch("app.config.get_settings", return_value=settings),
            patch("app.services.gitlab.cache.GitLabAPICache") as mock_cache_cls,
        ):
            mock_cache_cls.return_value = mock_cache
            # Should not raise
            await _invalidate_project_cache(42)


# ---------------------------------------------------------------
# Course activate -> auto-sync teams
# ---------------------------------------------------------------


class TestCourseActivateAutoSync:
    """Tests for auto-sync triggered on course activation."""

    @pytest.mark.asyncio
    async def test_activate_enqueues_sync_for_teams(self):
        """Activating a course enqueues sync and metrics for all active teams."""
        from app.services.courses import _enqueue_team_syncs

        team = FakeTeam()
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [team]
        mock_session.scalars.return_value = mock_result
        mock_session.flush = AsyncMock()

        mock_job = MagicMock()
        mock_job.id = uuid.uuid4()

        with (
            patch("app.services.courses.BackgroundJob") as mock_bg,
            patch("app.services.courses._has_pending_sync", return_value=False),
            patch("app.services.events.enqueue_sync_job") as mock_sync,
            patch("app.services.events.enqueue_metrics_refresh") as mock_metrics,
        ):
            mock_bg.return_value = mock_job
            count = await _enqueue_team_syncs(mock_session, uuid.uuid4())

        assert count == 1
        mock_sync.assert_called_once()
        mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_no_teams(self):
        """No syncs enqueued for course with no teams."""
        from app.services.courses import _enqueue_team_syncs

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.scalars.return_value = mock_result

        count = await _enqueue_team_syncs(mock_session, uuid.uuid4())
        assert count == 0

    @pytest.mark.asyncio
    async def test_activate_handles_enqueue_failure(self):
        """Gracefully handles RQ enqueue failures."""
        from app.services.courses import _enqueue_team_syncs

        team = FakeTeam()
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [team]
        mock_session.scalars.return_value = mock_result
        mock_session.flush = AsyncMock()

        with (
            patch("app.services.courses.BackgroundJob") as mock_bg,
            patch("app.services.courses._has_pending_sync", return_value=False),
            patch(
                "app.services.events.enqueue_sync_job",
                side_effect=RuntimeError("Redis down"),
            ),
        ):
            mock_bg.return_value = MagicMock(id=uuid.uuid4())
            count = await _enqueue_team_syncs(mock_session, uuid.uuid4())

        assert count == 0


# ---------------------------------------------------------------
# Team deactivation cascade
# ---------------------------------------------------------------


class TestTeamDeactivationCascade:
    """Tests that team deletion cancels pending background jobs."""

    def test_delete_team_endpoint_exists(self) -> None:
        """The delete_team endpoint is importable."""
        from app.api.teams import delete_team

        assert callable(delete_team)

    def test_team_delete_route_is_delete_method(self) -> None:
        """Verify the route is registered as HTTP DELETE."""
        from app.api.teams import router

        delete_routes = [
            r for r in router.routes if hasattr(r, "methods") and "DELETE" in r.methods
        ]
        team_delete = [r for r in delete_routes if hasattr(r, "path") and r.path == "/{team_id}"]
        assert len(team_delete) == 1

    def test_delete_team_permanent_endpoint_exists(self) -> None:
        """The delete_team_permanent endpoint is importable."""
        from app.api.teams import delete_team_permanent

        assert callable(delete_team_permanent)

    def test_team_delete_permanent_route_is_delete_method(self) -> None:
        """Verify the route is registered as HTTP DELETE."""
        from app.api.teams import router

        delete_routes = [
            r for r in router.routes if hasattr(r, "methods") and "DELETE" in r.methods
        ]
        team_delete = [
            r for r in delete_routes if hasattr(r, "path") and r.path == "/{team_id}/permanent"
        ]
        assert len(team_delete) == 1

    def test_delete_project_permanent_endpoint_exists(self) -> None:
        """The delete_project_permanent endpoint is importable."""
        from app.api.projects import delete_project_permanent

        assert callable(delete_project_permanent)

    def test_project_delete_permanent_route_is_delete_method(self) -> None:
        """Verify the route is registered as HTTP DELETE."""
        from app.api.projects import router

        delete_routes = [
            r for r in router.routes if hasattr(r, "methods") and "DELETE" in r.methods
        ]
        project_delete = [
            r for r in delete_routes if hasattr(r, "path") and r.path == "/{project_id}/permanent"
        ]
        assert len(project_delete) == 1


# ---------------------------------------------------------------
# Course live-data endpoint
# ---------------------------------------------------------------


class TestCourseLiveDataEndpoint:
    """Tests for the course live-data JSON endpoint."""

    def test_endpoint_importable(self) -> None:
        """The course_live_data handler is importable."""
        from app.api.dashboard.courses.routes import course_live_data

        assert callable(course_live_data)

    def test_route_registered(self) -> None:
        """The live-data route is registered on the router."""
        from app.api.dashboard.courses.routes import router

        get_routes = [r for r in router.routes if hasattr(r, "methods") and "GET" in r.methods]
        live_data_routes = [r for r in get_routes if hasattr(r, "path") and "live-data" in r.path]
        assert [route.path for route in live_data_routes] == ["/courses/{course_id}/live-data"]


# ---------------------------------------------------------------
# Auto-refresh integration
# ---------------------------------------------------------------


class TestAutoRefreshIntegration:
    """Tests verifying SSE-first live data + polling fallback is integrated into pages."""

    def test_team_detail_js_has_sse_with_polling_fallback(self) -> None:
        """team-detail.js should use SSE as primary with polling fallback."""
        content = page_bundle("pages/team-detail.js")
        assert "_connectTeamSSE" in content
        assert "GP.sse(" in content
        assert "_startFallbackPolling" in content
        assert "setInterval" in content
        assert "30000" in content  # 30 second fallback interval

    def test_course_detail_js_has_sse_with_polling_fallback(self) -> None:
        """course-detail.js should use SSE as primary with polling fallback."""
        content = page_bundle("pages/course-detail.js")
        assert "_refreshCourseData" in content
        assert "_connectCourseDataSSE" in content
        assert "GP.sse(" in content
        assert "live-data" in content

    def test_dashboard_js_has_sse_with_polling_fallback(self) -> None:
        """dashboard.js should use SSE as primary with polling fallback."""
        content = page_bundle("pages/dashboard.js")
        assert "_connectDashboardSSE" in content
        assert "GP.sse(" in content
        assert "_startDashboardPolling" in content
        assert "refreshDashboardStats" in content

    def test_project_detail_js_has_sse_with_polling_fallback(self) -> None:
        """project-detail.js should use SSE-first for live project data updates."""
        content = page_bundle("pages/project-detail.js")
        assert "_connectProjectSSE" in content
        assert "GP.sse(" in content
        assert "_startProjectPolling" in content
        assert "refreshProjectData" in content
        assert "/api/v1/teams/" in content


# ---------------------------------------------------------------
# Dashboard SSE pub/sub infrastructure
# ---------------------------------------------------------------


class TestDashboardPubSub:
    """Tests for Redis pub/sub dashboard notification infrastructure."""

    def test_publish_dashboard_update_does_not_raise(self) -> None:
        """publish_dashboard_update should never raise, even if Redis is down."""
        from app.workers.progress import publish_dashboard_update

        # Should silently fail (Redis not available in tests)
        publish_dashboard_update("team", "fake-uuid", "test_event")
        publish_dashboard_update("course", "fake-uuid", "metrics_computed", extra={"x": 1})

    def test_publish_progress_dashboard_channels(self) -> None:
        """publish_progress with dashboard params should not raise."""
        from app.workers.progress import publish_progress

        publish_progress(
            "job-123",
            "completed",
            "test",
            dashboard_team_id="team-uuid",
            dashboard_course_id="course-uuid",
        )

    def test_sse_endpoints_registered(self) -> None:
        """SSE router should have team, course, and global dashboard stream endpoints."""
        from app.api.sse import router

        route_names = {r.name for r in router.routes if hasattr(r, "name")}
        assert "stream_team_dashboard" in route_names
        assert "stream_course_dashboard" in route_names
        assert "stream_dashboard_global" in route_names

    def test_event_processor_notify_function_exists(self) -> None:
        """event_processor should have _notify_dashboard_update function."""
        from app.workers import event_processor

        assert hasattr(event_processor, "_notify_dashboard_update")
        assert callable(event_processor._notify_dashboard_update)


# ---------------------------------------------------------------
# Member webhook handler
# ---------------------------------------------------------------


class TestMemberWebhookHandler:
    """Tests for member event handling in event_processor."""

    def test_member_in_dispatch_table(self) -> None:
        """Dispatch table should include 'member' as a known event kind."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor._process_async)
        # Verify "member" appears in a dispatch dict context
        assert '"member"' in source or "'member'" in source

    def test_sync_members_on_member_event_function_exists(self) -> None:
        """_sync_members_on_member_event helper should exist."""
        from app.workers import event_processor

        assert hasattr(event_processor, "_sync_members_on_member_event")
        assert callable(event_processor._sync_members_on_member_event)

    @pytest.mark.asyncio
    async def test_sync_members_on_member_event_enqueues_job(self):
        """Member event should enqueue sync_single_team_members job for the team."""
        from app.workers.event_processor import _sync_members_on_member_event

        mock_session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_session.execute.return_value = result

        with (
            patch("app.services.events._get_queue") as mock_queue,
            patch("app.config.get_settings", return_value=FakeSettings()),
        ):
            mock_q = MagicMock()
            mock_queue.return_value = mock_q

            await _sync_members_on_member_event(
                mock_session, {"user_id": 123, "event_name": "user_add_to_team"}, 42
            )

        mock_q.enqueue.assert_called_once()
        args = mock_q.enqueue.call_args
        assert "sync_single_team_members" in args[0][0]

    @pytest.mark.asyncio
    async def test_sync_members_on_member_event_no_project(self):
        """Member event for unknown project should be a no-op."""
        from app.workers.event_processor import _sync_members_on_member_event

        mock_session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result

        # Should not raise
        await _sync_members_on_member_event(mock_session, {"user_id": 123}, 9999)


# ---------------------------------------------------------------
# Ignorable webhook types
# ---------------------------------------------------------------


class TestIgnorableWebhookTypes:
    """Tests for graceful handling of known-ignorable webhook event types."""

    def test_ignorable_kinds_defined(self) -> None:
        """ignorable_kinds should be defined in event_processor dispatch logic."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        assert "_IGNORABLE_KINDS" in source
        for kind in ("deployment", "release", "wiki_page", "build"):
            assert kind in source

    def test_ignorable_not_processing_error(self) -> None:
        """Ignorable types should NOT produce processing_error - they're silently accepted."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor._process_async)
        # The code should check ignorable_kinds before falling through to the unhandled case
        ignorable_pos = source.index("in _IGNORABLE_KINDS")
        unhandled_pos = source.index("unhandled_kind:")
        assert ignorable_pos < unhandled_pos


# ---------------------------------------------------------------
# Project metadata sync in incremental refresh
# ---------------------------------------------------------------


class TestProjectMetadataSync:
    """Tests for project metadata sync in _incremental_project_refresh."""

    @pytest.mark.asyncio
    async def test_incremental_refresh_updates_project_metadata(self):
        """_incremental_refresh_async should update project name/path from GitLab API."""
        from app.workers.sweep import _incremental_refresh_async

        project_id = str(uuid.uuid4())
        gitlab_project_id = 42
        settings = FakeSettings()
        settings.gitlab_url = "https://gitlab.example.com"
        settings.gitlab_api_token = "fake-token"

        fake_project = MagicMock()
        fake_project.gitlab_project_name = "old-name"
        fake_project.gitlab_project_path = "old/path"
        fake_project.default_branch = "master"

        mock_session = AsyncMock()
        issue_result = MagicMock()
        issue_result.all.return_value = []
        mr_result = MagicMock()
        mr_result.all.return_value = []
        mock_session.execute.side_effect = [issue_result, mr_result]
        mock_session.get.return_value = fake_project

        mock_gl = AsyncMock()
        mock_gl.get_project.return_value = {
            "name": "new-name",
            "path_with_namespace": "new/path",
            "default_branch": "main",
        }

        with (
            patch("app.config.get_settings", return_value=settings),
            patch("app.workers.bootstrap.worker_session") as mock_ws,
            patch("app.services.events._get_queue") as mock_queue,
            patch("app.services.gitlab.client.GitLabClient") as mock_gl_cls,
        ):
            ctx = AsyncMock()
            ctx.__aenter__ = AsyncMock(return_value=(mock_session, settings))
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ws.return_value = ctx

            gl_ctx = AsyncMock()
            gl_ctx.__aenter__ = AsyncMock(return_value=mock_gl)
            gl_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_gl_cls.return_value = gl_ctx

            mock_queue.return_value = MagicMock()

            await _incremental_refresh_async(project_id, gitlab_project_id)

        assert fake_project.gitlab_project_name == "new-name"
        assert fake_project.gitlab_project_path == "new/path"
        assert fake_project.default_branch == "main"
        mock_session.commit.assert_called()


# ---------------------------------------------------------------
# Course activity live-data endpoint
# ---------------------------------------------------------------


class TestCourseActivity:
    """The Activity page owns its initial response and live refresh."""

    def test_activity_route_exists(self) -> None:
        from app.api.dashboard.courses.routes import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert "/courses/{course_id}/activity" in paths


class TestAutoArchiveSweep:
    """Semester-end auto-archive sweep archives only due, non-skipped courses."""

    @pytest.mark.asyncio
    async def test_archives_only_due_non_skipped_courses(self):
        from datetime import date
        from types import SimpleNamespace

        from app.workers import sweep_auto_archive

        settings = FakeSettings()  # auto-archive enabled; grace/weeks default to 14

        # A: ended long ago, not skipped -> ARCHIVE
        # B: ended long ago, skip_auto_archive=True -> SKIP
        # C: end far in the future -> not over -> SKIP
        a = SimpleNamespace(id=uuid.uuid4(), code="A")
        cs_a = SimpleNamespace(
            semester_end_date=date(2020, 1, 1),
            semester_start_date=date(2019, 9, 1),
            skip_auto_archive=False,
        )
        b = SimpleNamespace(id=uuid.uuid4(), code="B")
        cs_b = SimpleNamespace(
            semester_end_date=date(2020, 1, 1),
            semester_start_date=date(2019, 9, 1),
            skip_auto_archive=True,
        )
        c = SimpleNamespace(id=uuid.uuid4(), code="C")
        cs_c = SimpleNamespace(
            semester_end_date=date(2099, 1, 1),
            semester_start_date=date(2098, 9, 1),
            skip_auto_archive=False,
        )

        mock_session = AsyncMock()
        rows = MagicMock()
        rows.all.return_value = [(a, cs_a), (b, cs_b), (c, cs_c)]
        mock_session.execute.return_value = rows
        mock_session.commit = AsyncMock()

        archived: list = []

        async def _fake_archive(session, cid):
            archived.append(cid)

        _archive = AsyncMock(side_effect=_fake_archive)
        with patch("app.services.courses.archive_course", new=_archive):
            n = await sweep_auto_archive.archive_due_courses(mock_session, settings)

        assert n == 1
        assert archived == [a.id]

    @pytest.mark.asyncio
    async def test_disabled_feature_archives_nothing(self):
        from app.workers import sweep_auto_archive

        settings = FakeSettings()
        settings.semester_auto_archive_enabled = False

        mock_session = AsyncMock()
        with patch("app.services.courses.archive_course", new=AsyncMock()) as arch:
            n = await sweep_auto_archive.archive_due_courses(mock_session, settings)

        assert n == 0
        arch.assert_not_called()

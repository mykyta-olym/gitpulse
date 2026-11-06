"""Tests for the visible bounded-retry + GitLab preflight behaviour.

Covers the pieces that turn a dead token / transient failure from a silent
flapping loop into an explicit, bounded, visible outcome:

* sync jobs enqueue with a bounded retry (``SYNC_MAX_ATTEMPTS`` attempts).
* ``_is_gitlab_auth_error`` flags 401/403 so the worker never retries them.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class TestSyncRetryWiring:
    """Sync jobs opt into a bounded, visible retry (not unlimited, not zero)."""

    def test_sync_max_attempts_is_three(self) -> None:
        from app.services.events import SYNC_MAX_ATTEMPTS

        assert SYNC_MAX_ATTEMPTS == 3

    @patch("app.services.events.get_settings")
    @patch("app.services.events._get_queue")
    def test_enqueue_sync_uses_bounded_retry(self, mock_get_queue, mock_get_settings) -> None:
        from app.services.events import SYNC_MAX_ATTEMPTS, enqueue_sync_job

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = MagicMock(id="job-sync")
        mock_get_queue.return_value = mock_queue
        mock_get_settings.return_value = SimpleNamespace(job_timeout_sync_seconds=3600)

        enqueue_sync_job("team-uuid", "bg-job-123")

        _, kwargs = mock_queue.enqueue.call_args
        retry = kwargs["retry"]
        assert retry is not None, "sync must retry transient failures"
        # 3 total attempts => 2 RQ retries.
        assert retry.max == SYNC_MAX_ATTEMPTS - 1

    @patch("app.services.events.get_settings")
    @patch("app.services.events._get_queue")
    def test_enqueue_project_sync_uses_bounded_retry(
        self, mock_get_queue, mock_get_settings
    ) -> None:
        from app.services.events import SYNC_MAX_ATTEMPTS, enqueue_project_sync_job

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = MagicMock(id="job-proj-sync")
        mock_get_queue.return_value = mock_queue
        mock_get_settings.return_value = SimpleNamespace(job_timeout_sync_seconds=3600)

        enqueue_project_sync_job("proj-uuid", "bg-job-123")

        _, kwargs = mock_queue.enqueue.call_args
        assert kwargs["retry"] is not None
        assert kwargs["retry"].max == SYNC_MAX_ATTEMPTS - 1


class TestIsGitLabAuthError:
    """Auth errors (401/403) are never retried; other failures may be."""

    def test_true_for_401_and_403(self) -> None:
        from app.services.gitlab.client_types import GitLabAPIError, is_gitlab_auth_error

        assert is_gitlab_auth_error(GitLabAPIError(401, "unauthorized"))
        assert is_gitlab_auth_error(GitLabAPIError(403, "forbidden"))

    def test_false_for_other_gitlab_status(self) -> None:
        from app.services.gitlab.client_types import GitLabAPIError, is_gitlab_auth_error

        assert not is_gitlab_auth_error(GitLabAPIError(500, "server error"))
        assert not is_gitlab_auth_error(GitLabAPIError(404, "not found"))

    def test_false_for_non_gitlab_exceptions(self) -> None:
        from app.services.gitlab.client_types import is_gitlab_auth_error

        assert not is_gitlab_auth_error(ValueError("boom"))
        assert not is_gitlab_auth_error(TimeoutError())


class TestTokenHealthFlag:
    """The shared flag poisons on 401 and clears on success (in-process path)."""

    def test_mark_unauthorized_then_ok(self) -> None:
        import app.services.gitlab.token_health as h

        # Force the in-process path (no shared Redis) for a deterministic test.
        with patch.object(h, "_read_redis", return_value=None), patch.object(h, "_write_redis"):
            h.mark_unauthorized()
            assert h.cached_status() == "unauthorized"
            h.mark_ok()
            assert h.cached_status() == "ok"


class TestGitLabTokenGuard:
    """gitlab_token_guarded skips known-bad, runs when ok, poisons on 401."""

    def test_skips_when_token_known_bad(self) -> None:
        import app.services.gitlab.token_health as h

        calls: list[int] = []

        @h.gitlab_token_guarded
        def job() -> str:
            calls.append(1)
            return "ran"

        with patch.object(h, "cached_status", return_value="unauthorized"):
            assert job() is None  # no-op, no exception (so RQ won't retry)
        assert calls == []

    def test_runs_when_token_ok(self) -> None:
        import app.services.gitlab.token_health as h

        @h.gitlab_token_guarded
        def job() -> str:
            return "ran"

        with patch.object(h, "cached_status", return_value="ok"):
            assert job() == "ran"

    def test_poisons_flag_on_auth_error(self) -> None:
        import app.services.gitlab.token_health as h
        from app.services.gitlab.client_types import GitLabAPIError

        @h.gitlab_token_guarded
        def job() -> None:
            raise GitLabAPIError(401, "unauthorized")

        marked: list[int] = []
        with (
            patch.object(h, "cached_status", return_value="ok"),
            patch.object(h, "mark_unauthorized", side_effect=lambda: marked.append(1)),
            pytest.raises(GitLabAPIError),
        ):
            job()
        assert marked == [1]

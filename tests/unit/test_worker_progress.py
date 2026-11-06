"""Tests for workers/progress.py - publish_progress helper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestPublishProgress:
    """Test the Redis pub/sub progress publisher."""

    @patch("app.workers.progress._get_publish_conn")
    def test_basic_publish(self, mock_get_conn: MagicMock) -> None:
        """Publish a simple status update to the job channel."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-123", "running", "Processing...")

        mock_conn.publish.assert_called_once()
        args = mock_conn.publish.call_args
        assert args[0][0] == "job_progress:job-123"

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_course_id(self, mock_get_conn: MagicMock) -> None:
        """Publish with course_id also publishes to course channel."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-456", "done", "Complete", course_id="c-1")

        calls = mock_conn.publish.call_args_list
        channels = [c[0][0] for c in calls]
        assert "job_progress:job-456" in channels
        assert "course_sync:c-1" in channels

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_llm_project_id(self, mock_get_conn: MagicMock) -> None:
        """Publish with llm_project_id also publishes to LLM analysis channel."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-789", "running", "Analyzing", llm_project_id="p-1")

        calls = mock_conn.publish.call_args_list
        channels = [c[0][0] for c in calls]
        assert "llm_analysis:p-1" in channels

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_enrichment(self, mock_get_conn: MagicMock) -> None:
        """Publish with enrichment flag also publishes to enrichment channel."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-000", "running", "Enriching", enrichment=True)

        calls = mock_conn.publish.call_args_list
        channels = [c[0][0] for c in calls]
        assert "enrichment_progress" in channels

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_with_extra_data(self, mock_get_conn: MagicMock) -> None:
        """Extra dict fields are merged into the published payload."""
        import json

        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-x", "running", extra={"pct": 42, "step": "lint"})

        data = json.loads(mock_conn.publish.call_args[0][1])
        assert data["pct"] == 42
        assert data["step"] == "lint"

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_never_raises(self, mock_get_conn: MagicMock) -> None:
        """publish_progress swallows all exceptions (SSE is optional)."""
        mock_get_conn.side_effect = ConnectionError("Redis down")

        from app.workers.progress import publish_progress

        # Should not raise
        publish_progress("job-err", "running", "msg")

    @patch("app.workers.progress._get_publish_conn")
    def test_publish_handles_broken_pipe(self, mock_get_conn: MagicMock) -> None:
        """Broken pipe on publish is swallowed gracefully."""
        mock_conn = MagicMock()
        mock_conn.publish.side_effect = ConnectionError("broken pipe")
        mock_get_conn.return_value = mock_conn

        from app.workers.progress import publish_progress

        publish_progress("job-err2", "running", "msg")

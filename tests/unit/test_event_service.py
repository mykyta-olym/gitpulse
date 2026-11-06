"""Tests for event service module."""

from unittest.mock import MagicMock, patch


class TestGetQueue:
    """Tests for _get_queue function."""

    @patch("app.services.events._queues", {})
    @patch("app.services.events.Queue")
    def test_creates_queue_on_first_call(self, mock_queue_class) -> None:
        from app.services.events import _get_queue

        mock_conn = MagicMock()
        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        with patch("app.redis_pool.get_redis", return_value=mock_conn):
            result = _get_queue("default")

        assert result is mock_queue
        mock_queue_class.assert_called_once_with("default", connection=mock_conn)

    @patch("app.services.events._queues", {"default": MagicMock()})
    def test_returns_cached_queue(self) -> None:
        from app.services.events import _get_queue, _queues

        cached_queue = _queues["default"]
        result = _get_queue("default")

        assert result is cached_queue


class TestRetry:
    """Tests for _retry function."""

    def test_retry_function_exists(self) -> None:
        from app.services.events import _retry

        assert callable(_retry)

    def test_retry_returns_retry_object(self) -> None:
        from rq import Retry

        from app.services.events import _retry

        result = _retry()

        assert isinstance(result, Retry)

    def test_retry_default_max_retries(self) -> None:
        from app.services.events import _retry

        result = _retry()

        assert result.max == 3

    def test_retry_custom_max_retries(self) -> None:
        from app.services.events import _retry

        result = _retry(max_retries=5)

        assert result.max == 5


class TestEnqueueEventProcessing:
    """Tests for enqueue_event_processing function."""

    @patch("app.services.events._get_queue")
    def test_enqueues_to_high_queue(self, mock_get_queue) -> None:
        from app.services.events import enqueue_event_processing

        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue

        result = enqueue_event_processing("event-abc")

        mock_get_queue.assert_called_once_with("high")
        assert result == "job-123"

    @patch("app.services.events._get_queue")
    def test_returns_none_on_exception(self, mock_get_queue) -> None:
        from app.services.events import enqueue_event_processing

        mock_get_queue.side_effect = Exception("Redis down")

        result = enqueue_event_processing("event-abc")

        assert result is None


class TestEnqueueEnrichIssue:
    """Tests for enqueue_enrich_issue function."""

    @patch("app.services.events._get_queue")
    def test_enqueues_to_default_queue(self, mock_get_queue) -> None:
        from app.services.events import enqueue_enrich_issue

        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-456"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue

        result = enqueue_enrich_issue(123, 45)

        mock_get_queue.assert_called_once_with("default")
        assert result == "job-456"

    @patch("app.services.events._get_queue")
    def test_returns_none_on_exception(self, mock_get_queue) -> None:
        from app.services.events import enqueue_enrich_issue

        mock_get_queue.side_effect = Exception("Connection refused")

        result = enqueue_enrich_issue(123, 45)

        assert result is None


class TestEnqueueEnrichMr:
    """Tests for enqueue_enrich_mr function."""

    @patch("app.services.events._get_queue")
    def test_enqueues_to_default_queue(self, mock_get_queue) -> None:
        from app.services.events import enqueue_enrich_mr

        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-789"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue

        result = enqueue_enrich_mr(456, 12)

        mock_get_queue.assert_called_once_with("default")
        assert result == "job-789"

    @patch("app.services.events._get_queue")
    def test_returns_none_on_exception(self, mock_get_queue) -> None:
        from app.services.events import enqueue_enrich_mr

        mock_get_queue.side_effect = Exception("Timeout")

        result = enqueue_enrich_mr(456, 12)

        assert result is None


class TestEnqueueMetricsRefresh:
    """Tests for enqueue_metrics_refresh function."""

    @patch("app.services.events._get_queue")
    def test_enqueues_to_default_queue(self, mock_get_queue) -> None:
        from app.services.events import enqueue_metrics_refresh

        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-metrics"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue

        result = enqueue_metrics_refresh("team-uuid")

        mock_get_queue.assert_called_once_with("default")
        assert result == "job-metrics"

    @patch("app.services.events._get_queue")
    def test_returns_none_on_exception(self, mock_get_queue) -> None:
        from app.services.events import enqueue_metrics_refresh

        mock_get_queue.side_effect = Exception("Queue error")

        result = enqueue_metrics_refresh("team-uuid")

        assert result is None


class TestEnqueueSyncJob:
    """Tests for enqueue_sync_job function."""

    @patch("app.services.events._get_queue")
    def test_enqueues_to_default_queue(self, mock_get_queue) -> None:
        from app.services.events import enqueue_sync_job

        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job-sync"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue

        result = enqueue_sync_job("team-uuid", "bg-job-123")

        mock_get_queue.assert_called_once_with("default")
        assert result == "job-sync"

    @patch("app.services.events._get_queue")
    def test_returns_none_on_exception(self, mock_get_queue) -> None:
        from app.services.events import enqueue_sync_job

        mock_get_queue.side_effect = Exception("Sync failed")

        result = enqueue_sync_job("team-uuid", "bg-job-123")

        assert result is None

"""Tests for backpressure and rate limiting module."""


class TestQueueBackpressure:
    """Tests for QueueBackpressure class."""

    def test_queue_backpressure_exists(self) -> None:
        from app.services.backpressure import QueueBackpressure

        assert QueueBackpressure is not None


class _FakeRedis:
    """Only the commands these classes actually reach for."""

    def __init__(self, depths: dict[str, int] | None = None) -> None:
        self._depths = depths or {}

    def llen(self, key: str) -> int:
        return self._depths.get(key.removeprefix("rq:queue:"), 0)


def _bp(**depths: int):
    from app.services.backpressure import QueueBackpressure

    return QueueBackpressure(_FakeRedis(depths))


class TestQueueDepthBehaviour:
    """The existing tests above assert that names exist; these assert what the
    code does with them."""

    def test_depth_is_read_per_queue(self) -> None:
        assert _bp(high=7).get_queue_depth("high") == 7

    def test_an_unknown_queue_reads_as_empty(self) -> None:
        assert _bp().get_queue_depth("nope") == 0

    def test_a_redis_failure_degrades_to_zero_rather_than_raising(self) -> None:
        """Backpressure must never be the reason a request dies."""
        from app.services.backpressure import QueueBackpressure

        class _Broken:
            def llen(self, key: str) -> int:
                raise ConnectionError("redis down")

        assert QueueBackpressure(_Broken()).get_queue_depth("high") == 0


class TestThrottleFactorBehaviour:
    def test_an_empty_queue_is_not_throttled(self) -> None:
        assert _bp(high=0).calculate_throttle_factor("high") == 1.0

    def test_throttling_never_leaves_the_unit_interval(self) -> None:
        for depth in (0, 10, 500, 100_000):
            factor = _bp(high=depth).calculate_throttle_factor("high")
            assert 0.0 <= factor <= 1.0, f"depth={depth} -> {factor}"

    def test_a_deeper_queue_never_throttles_less(self) -> None:
        """Monotonicity is the contract: more backlog, no more admitted."""
        factors = [_bp(high=d).calculate_throttle_factor("high") for d in (0, 50, 200, 1000)]

        assert factors == sorted(factors, reverse=True)

    def test_disabling_the_feature_removes_all_throttling(self) -> None:
        bp = _bp(high=100_000)
        bp.config.enabled = False

        assert bp.calculate_throttle_factor("high") == 1.0

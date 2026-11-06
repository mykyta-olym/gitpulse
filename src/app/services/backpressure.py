"""Protect the webhook queue from overload using its actual Redis depth."""

import random
from dataclasses import dataclass
from typing import Any, cast

from redis import Redis

rng = random.SystemRandom()


@dataclass
class BackpressureConfig:
    queue_high_watermark: int = 1000
    queue_critical_watermark: int = 5000
    enabled: bool = True


class QueueBackpressure:
    """Monitor queue depth and apply backpressure.

    Implements:
    - Queue depth monitoring
    - Adaptive throttling based on depth
    - Shedding strategy for overload
    """

    def __init__(
        self,
        redis_conn: "Redis[Any]",
        config: BackpressureConfig | None = None,
    ) -> None:
        self._redis = redis_conn
        self.config = config or BackpressureConfig()

    def get_queue_depth(self, queue_name: str) -> int:
        """Get current depth of an RQ queue."""
        try:
            depth = self._redis.llen(f"rq:queue:{queue_name}")
            return int(cast(Any, depth))
        except Exception:
            return 0

    def calculate_throttle_factor(self, queue_name: str = "high") -> float:
        """Calculate throttle factor based on queue depth.

        Returns:
            Factor between 0.0 (full throttle) and 1.0 (no throttle)
        """
        if not self.config.enabled:
            return 1.0

        depth = self.get_queue_depth(queue_name)
        high = self.config.queue_high_watermark
        critical = self.config.queue_critical_watermark

        if depth < high:
            return 1.0

        if depth >= critical:
            return 0.0  # Full stop

        # Linear interpolation between high and critical
        return 1.0 - ((depth - high) / (critical - high))

    def should_accept_job(self, queue_name: str = "high", priority: int = 5) -> bool:
        """Determine if a new job should be accepted.

        Args:
            queue_name: Target queue
            priority: Job priority (1=highest, 10=lowest)

        Returns:
            True if job should be accepted
        """
        throttle = self.calculate_throttle_factor(queue_name)

        if throttle >= 1.0:
            return True

        if throttle <= 0.0:
            return priority <= 1  # Only accept highest priority

        # Probabilistic shedding based on priority
        threshold = throttle * (11 - priority) / 10
        return rng.random() < threshold

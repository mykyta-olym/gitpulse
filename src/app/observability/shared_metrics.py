"""Metrics the RQ workers record, kept in Redis so the API can export them.

Prometheus scrapes the API alone. A job runs in a work-horse that RQ forks for
it and that exits when the job ends, in one of four worker containers, so a
prometheus_client counter incremented there is gone before anything reads it.
That is why the webhook, enrichment, metrics-compute and GitLab API panels
stayed empty on production and the alerts over them could never fire. These
metrics add each observation to a Redis hash instead - the workers already
share Redis for the queue - and ``SharedMetricsCollector`` turns the hashes
into samples on every scrape of ``/metrics``. The totals outlive any process,
as a counter's should.

The calling code is the same as for prometheus_client:
``WEBHOOK_PROCESSED.labels(event_type="push", status="ok").inc()``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Sequence
from typing import Any

from prometheus_client.metrics_core import CounterMetricFamily, HistogramMetricFamily, Metric
from prometheus_client.utils import floatToGoString

logger = logging.getLogger(__name__)

_KEY_PREFIX = "gitpulse:metrics:"
# Separates the label values (a JSON list, which escapes tabs) from the
# histogram part a field holds: "sum" or a bucket bound.
_SEP = "\t"

_METRICS: list[_SharedMetric] = []


def _redis() -> Any:
    from app.redis_pool import get_redis

    return get_redis()


class _SharedMetric:
    def __init__(self, name: str, documentation: str, labelnames: Sequence[str]) -> None:
        self._name = name
        self._documentation = documentation
        self._labelnames = tuple(labelnames)
        self._key = _KEY_PREFIX + name
        _METRICS.append(self)

    def _labels_field(self, labels: dict[str, str]) -> str:
        if set(labels) != set(self._labelnames):
            raise ValueError(f"{self._name} takes labels {self._labelnames}, got {sorted(labels)}")
        return json.dumps([str(labels[n]) for n in self._labelnames])

    def _add(self, increments: dict[str, float]) -> None:
        # A metric must never fail the job that records it.
        try:
            pipe = _redis().pipeline(transaction=False)
            for field, amount in increments.items():
                pipe.hincrbyfloat(self._key, field, amount)
            pipe.execute()
        except Exception:
            logger.debug("shared metric %s not recorded", self._name, exc_info=True)

    def family(self, data: dict[str, float]) -> Metric:
        raise NotImplementedError


class _CounterChild:
    def __init__(self, metric: SharedCounter, field: str) -> None:
        self._metric = metric
        self._field = field

    def inc(self, amount: float = 1.0) -> None:
        self._metric._add({self._field: amount})


class SharedCounter(_SharedMetric):
    def __init__(self, name: str, documentation: str, labelnames: Sequence[str] = ()) -> None:
        super().__init__(name, documentation, labelnames)

    def labels(self, **labels: str) -> _CounterChild:
        return _CounterChild(self, self._labels_field(labels))

    def inc(self, amount: float = 1.0) -> None:
        self.labels().inc(amount)

    def family(self, data: dict[str, float]) -> Metric:
        family = CounterMetricFamily(self._name, self._documentation, labels=self._labelnames)
        for field, value in sorted(data.items()):
            family.add_metric(json.loads(field), value)
        return family


class _HistogramChild:
    def __init__(self, metric: SharedHistogram, field: str) -> None:
        self._metric = metric
        self._field = field

    def observe(self, amount: float) -> None:
        increments = {self._field + _SEP + "sum": amount}
        # Stored cumulative, as Prometheus reads them: every bucket the value
        # fits in. The +Inf bucket is the count.
        for bound in self._metric._bounds:
            if amount <= bound:
                increments[self._field + _SEP + _le(bound)] = 1.0
        self._metric._add(increments)


class SharedHistogram(_SharedMetric):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        *,
        buckets: Sequence[float],
    ) -> None:
        super().__init__(name, documentation, labelnames)
        self._bounds = (*sorted(float(b) for b in buckets), float("inf"))

    def labels(self, **labels: str) -> _HistogramChild:
        return _HistogramChild(self, self._labels_field(labels))

    def observe(self, amount: float) -> None:
        self.labels().observe(amount)

    def family(self, data: dict[str, float]) -> Metric:
        family = HistogramMetricFamily(self._name, self._documentation, labels=self._labelnames)
        series: dict[str, dict[str, float]] = {}
        for field, value in data.items():
            labels, part = field.rsplit(_SEP, 1)
            series.setdefault(labels, {})[part] = value
        for labels, parts in sorted(series.items()):
            buckets = [(_le(b), parts.get(_le(b), 0.0)) for b in self._bounds]
            family.add_metric(json.loads(labels), buckets, parts.get("sum", 0.0))
        return family


class SharedMetricsCollector:
    """Exports every shared metric from Redis, one round trip per scrape."""

    def describe(self) -> Iterator[Metric]:
        # Names only, so registering the collector does not reach for Redis.
        for metric in _METRICS:
            yield metric.family({})

    def collect(self) -> Iterator[Metric]:
        try:
            pipe = _redis().pipeline(transaction=False)
            for metric in _METRICS:
                pipe.hgetall(metric._key)
            stored = pipe.execute()
        except Exception:
            logger.debug("shared metrics not collected", exc_info=True)
            return
        for metric, raw in zip(_METRICS, stored, strict=True):
            data = {_text(k): float(v) for k, v in raw.items()}
            yield metric.family(data)


def _text(value: bytes | str) -> str:
    return value.decode() if isinstance(value, bytes) else value


def _le(bound: float) -> str:
    """A bucket bound as prometheus_client writes it ("0.5", "+Inf")."""
    return str(floatToGoString(bound))  # type: ignore[no-untyped-call]

"""OpenTelemetry is an optional extra, so every tracing entry point must be a
no-op when the SDK is absent.

The whole module is written as `try: import ... except ImportError: return`.
That degrades quietly by design - which is exactly why it needs testing: if a
regression let an exception escape, it would take down request handling in
every deployment that does not install the `otel` extra, and nothing else in
the suite touches these functions.
"""

from __future__ import annotations

import builtins
from typing import Any

import pytest

from app.observability import tracing


@pytest.fixture
def without_otel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every `opentelemetry` import raise, as on a base install."""
    real_import = builtins.__import__

    def _blocked(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("opentelemetry"):
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)


class TestWithoutTheSdk:
    def test_setup_is_a_silent_no_op(self, without_otel: None) -> None:
        tracing.setup_tracing("gitpulse", otlp_endpoint="http://collector:4317")

    def test_get_tracer_returns_none_rather_than_raising(self, without_otel: None) -> None:
        assert tracing.get_tracer() is None

    def test_setting_a_correlation_id_is_a_no_op(self, without_otel: None) -> None:
        tracing.set_correlation_attribute("abc-123")

    @pytest.mark.parametrize(
        "instrument",
        ["_instrument_fastapi", "_instrument_sqlalchemy", "_instrument_httpx", "_instrument_redis"],
    )
    def test_every_instrumentor_degrades_quietly(self, without_otel: None, instrument: str) -> None:
        getattr(tracing, instrument)()


class TestWithWhateverIsInstalled:
    """These run against the real environment, whichever way it is set up."""

    def test_setup_without_an_endpoint_does_not_raise(self) -> None:
        tracing.setup_tracing("gitpulse-test")

    def test_get_tracer_returns_none_or_a_tracer(self) -> None:
        tracer = tracing.get_tracer("gitpulse-test")

        assert tracer is None or hasattr(tracer, "start_as_current_span")

    def test_correlation_attribute_is_safe_outside_a_span(self) -> None:
        """Called from middleware on every request, span or not."""
        tracing.set_correlation_attribute("no-active-span")

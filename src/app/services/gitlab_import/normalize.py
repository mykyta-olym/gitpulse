"""Normalization helpers for GitLab group import (text + numeric coercion)."""

from typing import Any


def _normalize_nonempty(value: Any, *, fallback: str | None = None) -> str:
    normalized = _normalize_optional(value)
    if normalized:
        return normalized
    if fallback:
        return fallback
    raise ValueError("Expected non-empty string value")


def _normalize_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_positive_int(value: Any, label: str) -> int:
    parsed = _to_int(value)
    if parsed <= 0:
        raise ValueError(f"Invalid {label}")
    return parsed

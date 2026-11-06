"""Resolution of the convention patterns used by R02, R03 and R05.

These three values - the branch-naming regex, the test-file globs and the MR
template headings - used to be top-level ``course_settings`` columns edited in
a separate "Patterns" card, disconnected from the checks that read them. They
now live in ``course_settings.check_configs`` next to the rest of each check's
configuration, so a check's behaviour is described in exactly one place.

The legacy columns are still read as a fallback: migration ``009`` backfills
``check_configs`` from them, but a course whose row predates that migration (or
was restored from an older dump) must keep scoring the way it did before rather
than silently falling back to "no conventions configured".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.course_settings import CourseSettings

__all__ = ["ResolvedPatterns", "resolve_patterns"]


@dataclass(frozen=True)
class ResolvedPatterns:
    """Effective pattern configuration for one course."""

    branch_pattern: str = ""
    test_file_patterns: list[str] = field(default_factory=list)
    required_sections: list[str] = field(default_factory=list)


def _as_list(value: Any) -> list[str] | None:
    """Coerce a stored param to a list of non-empty strings.

    Accepts both shapes the value can arrive in: a real JSON list (what the
    API stores) and a comma-separated string (what the text input posts).
    Returns ``None`` when nothing was configured, so the caller can tell
    "not set" apart from "deliberately empty".
    """
    if value is None:
        return None
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple)):
        items = [str(part).strip() for part in value]
    else:
        return None
    cleaned = [item for item in items if item]
    return cleaned or None


def resolve_patterns(settings: CourseSettings | None) -> ResolvedPatterns:
    """Return the patterns in force for ``settings``.

    ``check_configs`` wins; the legacy columns fill any key it does not carry.
    """
    if settings is None:
        return ResolvedPatterns()

    configs = settings.check_configs or {}

    def _cfg(code: str, key: str) -> Any:
        entry = configs.get(code)
        return entry.get(key) if isinstance(entry, dict) else None

    branch = _cfg("R02", "branch_pattern")
    if not isinstance(branch, str) or not branch.strip():
        branch = settings.branch_pattern or ""

    tests = _as_list(_cfg("R03", "test_file_patterns"))
    if tests is None:
        tests = list(settings.test_file_patterns or [])

    sections = _as_list(_cfg("R05", "required_sections"))
    if sections is None:
        sections = list(settings.mr_template_required_sections or [])

    return ResolvedPatterns(
        branch_pattern=branch.strip(),
        test_file_patterns=tests,
        required_sections=sections,
    )

"""Every course-creation path must seed the SAME default course settings.

The CourseSettings columns default to an empty list, so the literals at the call
sites are the real defaults. They were copy-pasted into all three paths (the
courses API, the full-config import, and the GitLab group import), so editing a
pattern in one place silently drifted from the others. They now come from
app.utils.constants; this test fails if a copy is reintroduced.
"""

import pathlib
import re

from app.utils.constants import DEFAULT_MR_TEMPLATE_SECTIONS, DEFAULT_TEST_FILE_PATTERNS

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "app"
_CREATION_PATHS = (
    _SRC / "api" / "courses.py",
    _SRC / "api" / "dashboard" / "courses" / "settings_config.py",
    _SRC / "services" / "gitlab_import" / "persistence.py",
)


class TestDefaultCourseSettings:
    def test_defaults_are_immutable_tuples(self) -> None:
        # A shared mutable list could be mutated in place via one course's settings.
        assert isinstance(DEFAULT_TEST_FILE_PATTERNS, tuple)
        assert isinstance(DEFAULT_MR_TEMPLATE_SECTIONS, tuple)

    def test_defaults_are_non_empty_and_unique(self) -> None:
        assert len(DEFAULT_TEST_FILE_PATTERNS) == len(set(DEFAULT_TEST_FILE_PATTERNS))
        assert DEFAULT_TEST_FILE_PATTERNS
        assert DEFAULT_MR_TEMPLATE_SECTIONS

    def test_no_creation_path_reintroduces_a_literal_copy(self) -> None:
        # Guards the drift this refactor removed: a hardcoded test-file glob in
        # any course-creation path means the defaults diverged again.
        offenders = [
            p.name
            for p in _CREATION_PATHS
            if re.search(r'"\*\*/test_\*\.py"', p.read_text(encoding="utf-8"))
        ]
        assert not offenders, f"Inline default patterns reintroduced in: {offenders}"

    def test_creation_paths_use_the_shared_constants(self) -> None:
        for p in _CREATION_PATHS:
            body = p.read_text(encoding="utf-8")
            assert "DEFAULT_TEST_FILE_PATTERNS" in body, f"{p.name} lost the shared default"

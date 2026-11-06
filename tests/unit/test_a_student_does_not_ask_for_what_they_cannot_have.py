"""Analysis discovery follows feature availability and staff read permissions."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "src/app/templates/static/js"


@pytest.mark.parametrize(
    ("part", "call"),
    [
        ("_parts/team-detail/20-analysis-boot.js", "llm-analysis-status"),
        ("_parts/project-detail/30-live-intel.js", "llm-analysis-status"),
    ],
)
def test_the_analysis_status_check_is_staff_only(part: str, call: str) -> None:
    """`MAY_SEE_ANALYSIS` mirrors the endpoint's own TeacherAuth guard."""
    src = (JS / part).read_text(encoding="utf-8")
    assert call in src, f"{part} no longer asks for the analysis status - update this test"
    assert "MAY_SEE_ANALYSIS" in src, (
        f"{part} asks for the AI-analysis status without checking that the reader is staff"
    )


@pytest.mark.parametrize(
    "part", ["_parts/team-detail/00-core.js", "_parts/project-detail/00-core.js"]
)
def test_the_flag_checks_the_feature_and_role_not_the_edit_lock(part: str) -> None:
    """`canEdit` is also false for a teacher on an ARCHIVED course, who may still
    watch an analysis that was already running. The endpoint checks the role, so
    this must too."""
    src = (JS / part).read_text(encoding="utf-8")
    declaration = re.search(r"const MAY_SEE_ANALYSIS\s*=\s*([^;]+);", src)
    assert declaration, f"{part}: missing analysis permission flag"
    expression = declaration[1]
    assert "isTeacher" in expression, f"{part}: the flag ignores teachers"
    assert "isAdmin" in expression, f"{part}: the flag ignores admins"
    assert "llmEnabled" in expression, f"{part}: the flag ignores feature availability"
    assert "canEdit" not in expression, f"{part}: the flag uses the edit lock, not the role"

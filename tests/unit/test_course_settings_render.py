"""Render the course-settings page end to end.

Everything else about this page is checked in pieces - macros in isolation,
element ids by regex, JS by syntax check. None of that catches the failure that
actually reaches a teacher: the page 500s because a template touches an
attribute or macro that no longer exists.

It is the most macro-dense page in the app (compliance checks, weekly
deadlines, webhooks, AI analysis, six modals), so rendering it exercises most
of the shared component surface in one go.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from starlette.requests import Request

from app.api.dashboard._helpers import _templates
from app.i18n import get_template_i18n_context
from app.models.course import Course
from app.models.course_settings import CourseSettings

_SETTINGS_FIELDS: dict[str, Any] = {
    "check_configs": {},
    "branch_pattern": "",
    "test_file_patterns": [],
    "mr_template_required_sections": [],
    "enabled_checks": [],
    "weekly_deadlines": [],
    "green_threshold": 0.8,
    "yellow_threshold": 0.5,
    "llm_course_type": "default",
    "llm_custom_prompt": "",
    "llm_resource_urls": [],
    "semester_start_date": None,
    "semester_end_date": None,
    "skip_auto_archive": False,
    "min_reviews_per_mr": 1,
    "min_review_word_count": 10,
    "min_distinct_mrs_reviewed": 1,
    "mr_creation_deadline": None,
    "merge_deadline": None,
    "gitlab_group_path": None,
}


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/dashboard/courses/x/settings",
            "raw_path": b"/dashboard/courses/x/settings",
            "query_string": b"",
            "headers": [],
            "root_path": "",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 1),
            "app": None,
        }
    )


@pytest.fixture
def rendered() -> str:
    """The page as a teacher with edit rights would receive it."""
    request = _request()
    course = Course(
        id=uuid.uuid4(),
        code="ZSI",
        name="Test course",
        academic_year="2025/2026",
        semester="summer",
    )
    course.is_active = True
    course.description = ""
    course.updated_at = datetime.now(UTC)

    settings = CourseSettings(course_id=course.id)
    for key, value in _SETTINGS_FIELDS.items():
        setattr(settings, key, value)
    settings.updated_at = datetime.now(UTC)

    context: dict[str, Any] = {
        "request": request,
        "course": course,
        "settings": settings,
        "checks_first_json": {"checks": [], "total_weight": 0.0, "weight_valid": False},
        "csrf_token": "test-csrf",
        "csp_nonce": "test-nonce",
        "multi_tenant_enabled": True,
        "transfer_teams": [],
        "llm_enabled": True,
        "llm_api_key_configured": True,
        "llm_resource_urls": [],
        "llm_custom_prompt": "",
        "llm_prompt_presets": {"default": "prompt"},
        "semester_status": None,
        "semester_presets": [],
        "semester_date_max_iso": "",
        "semester_date_min_iso": "",
        "is_admin": True,
        "is_teacher": True,
        "can_edit": True,
        **get_template_i18n_context(request),
    }
    return _templates(request).env.get_template("course_settings.html").render(**context)


def test_page_renders(rendered: str) -> None:
    assert len(rendered) > 10_000


def test_shared_components_are_on_the_page(rendered: str) -> None:
    """The controls the check editor clones/uses at runtime must be present."""
    # Cloned by the check editor to build parameter rows.
    assert 'id="tplNumberStepper"' in rendered
    assert "data-number-input" in rendered
    # One JSON surface for the weekly schedule.
    assert "data-json-drop" in rendered
    assert 'name="weekly_deadlines"' in rendered


def test_ai_analysis_sits_inside_the_form_above_the_save_bar(rendered: str) -> None:
    """Outside the form its edits never armed the save guard."""
    form_start = rendered.index('id="courseSettingsForm"')
    save_bar = rendered.index("settings-sticky-footer")
    ai_section = rendered.index("llm_course_type")
    form_end = rendered.index("</form>", form_start)

    assert form_start < ai_section < save_bar < form_end


def test_patterns_moved_out_of_their_own_card(rendered: str) -> None:
    """The three pattern inputs now live in the R02/R03/R05 check editors."""
    assert 'name="branch_pattern"' not in rendered
    assert 'name="test_file_patterns"' not in rendered
    assert 'name="mr_template_required_sections"' not in rendered
    # Their replacement - the convention presets - is present instead.
    assert 'data-action="applyPatternPreset"' in rendered


def test_no_unrendered_jinja_or_undefined_leaks_into_the_html(rendered: str) -> None:
    """Catches a macro that silently produced nothing, or a missing context key.

    The embedded i18n catalog is excluded: translated strings legitimately
    carry `{{current}}`-style tokens that the CLIENT interpolates, so scanning
    it for `{{` would always trip.
    """
    catalog_start = rendered.index('id="gp-i18n-config"')
    catalog_end = rendered.index("</script>", catalog_start)
    markup = rendered[:catalog_start] + rendered[catalog_end:]

    assert "{{" not in markup
    assert "{%" not in markup
    assert "Undefined" not in markup

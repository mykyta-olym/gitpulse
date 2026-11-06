"""Native form transport for the same command used by enhanced settings saves."""

import json
from typing import Any

from starlette.datastructures import FormData

from app.schemas.courses import CourseConfigurationUpdate, CourseSettingsUpdate


def configuration_from_form(form: FormData) -> CourseConfigurationUpdate:
    """Convert present fields only; hidden optional modules never clear stored values."""
    course: dict[str, Any] = {
        field: form["course_" + field]
        for field in ("code", "name", "description", "academic_year", "semester")
        if "course_" + field in form
    }
    course["expected_updated_at"] = form.get("expected_course_updated_at") or None
    settings: dict[str, Any] = {
        field: form[field] for field in CourseSettingsUpdate.model_fields if field in form
    }
    settings["expected_updated_at"] = form.get("expected_settings_updated_at") or None
    for field in (
        "semester_start_date",
        "semester_end_date",
        "mr_creation_deadline",
        "merge_deadline",
    ):
        if field in settings:
            settings[field] = settings[field] or None
    for field in ("weekly_deadlines", "check_configs"):
        if field in settings:
            settings[field] = json.loads(str(settings[field]))
    if "llm_resource_urls_json" in form:
        settings["llm_resource_urls"] = json.loads(str(form["llm_resource_urls_json"]))
    for field in ("mr_template_required_sections", "test_file_patterns"):
        if field in settings:
            settings[field] = [v.strip() for v in str(settings[field]).split(",") if v.strip()]
    if "skip_auto_archive_present" in form:
        settings["skip_auto_archive"] = bool(form.get("skip_auto_archive"))
    if "checks_present" in form:
        settings["enabled_checks"] = form.getlist("enabled_checks")
    checks = {
        str(code): {
            "is_active": str(code) in form.getlist("active_custom_checks"),
            "expected_updated_at": form.get("check_updated_at_" + str(code)) or None,
        }
        for code in form.getlist("custom_check_codes")
    }
    return CourseConfigurationUpdate.model_validate(
        {"course": course, "settings": settings, "checks": checks}
    )

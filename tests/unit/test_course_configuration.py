"""The native and enhanced settings transports share omission and disable semantics."""

from datetime import date

import pytest
from pydantic import ValidationError
from starlette.datastructures import FormData

from app.api.dashboard.courses.settings_form import configuration_from_form
from app.schemas.courses import CourseSettingsUpdate
from app.schemas.custom_check import CheckUpdate
from app.services.course_settings import apply_settings_update
from tests.unit.test_compliance_engine import StubCourseSettings


def test_absent_optional_fields_are_not_submitted_as_defaults():
    data = configuration_from_form(FormData({"course_name": "Renamed"}))
    assert data.course.name == "Renamed"
    assert data.settings.model_fields_set == {"expected_updated_at"}


@pytest.mark.parametrize(
    "payload",
    [
        {"green_threshold": None},
        {"enabled_checks": None},
        {"min_reviews_per_mr": 0},
        {"weight_issue_ownership": float("nan")},
    ],
)
def test_invalid_non_nullable_settings_are_rejected(payload):
    with pytest.raises(ValidationError):
        CourseSettingsUpdate.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [{"is_active": "false"}, {"weight": None}, {"weight": float("nan")}, {"category": "unknown"}],
)
def test_check_edit_is_validated_before_any_mutation(payload):
    with pytest.raises(ValidationError):
        CheckUpdate.model_validate(payload)


def test_native_form_uses_the_same_strict_threshold_validation():
    with pytest.raises(ValidationError):
        configuration_from_form(FormData({"green_threshold": "2"}))


def test_native_form_can_explicitly_clear_semester_dates():
    data = configuration_from_form(FormData({"semester_start_date": ""}))
    assert "semester_start_date" in data.settings.model_fields_set
    assert data.settings.semester_start_date is None


def test_omitted_dates_leave_existing_semester_untouched():
    cs = StubCourseSettings(semester_start_date=date(2026, 9, 21))
    apply_settings_update(cs, CourseSettingsUpdate(green_threshold=0.9))
    assert cs.semester_start_date == date(2026, 9, 21)


def test_explicit_empty_selection_disables_every_builtin_check():
    from app.compliance.engine_checks import run_all_checks
    from app.compliance.types import StudentContext

    cs = StubCourseSettings(enabled_checks=[])
    checks = run_all_checks(
        StudentContext(student_id="1", gitlab_user_id=1, gitlab_username="test"), cs
    )
    assert len(checks) == 13
    assert all(check.weight == 0 and check.detail == "Check disabled" for check in checks)

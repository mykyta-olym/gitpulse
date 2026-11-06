"""Regression coverage for dashboard member scoring-exclusion helpers."""

import uuid
from dataclasses import dataclass

from app.api.dashboard.projects.routes import _compute_scored_students
from app.api.dashboard.teams.member_exclusion import (
    ACTIVE_JOB_STATUSES,
    ACTIVE_SCORING_JOB_TYPES,
    member_base_category,
    member_can_toggle_scoring,
    member_visible_category,
)
from app.api.helpers.job_guards import (
    active_job_conflict_fields,
    active_job_conflict_message,
    advisory_lock_key,
)
from app.models.background_job import BackgroundJob


@dataclass
class _Member:
    is_teacher: bool = False
    is_mentor: bool = False
    excluded_from_scoring: bool = False
    membership_source: str = "direct"
    is_synthetic: bool = False


@dataclass
class _Student:
    id: uuid.UUID
    gitlab_username: str


def test_member_visible_category_keeps_original_source_when_reincluded() -> None:
    member = _Member(excluded_from_scoring=True, membership_source="inherited")

    assert member_visible_category(member) == "excluded"

    member.excluded_from_scoring = False

    assert member_base_category(member) == "inherited"
    assert member_visible_category(member) == "inherited"


def test_member_toggle_hidden_for_role_excluded_members() -> None:
    assert not member_can_toggle_scoring(_Member(is_teacher=True))
    assert not member_can_toggle_scoring(_Member(is_mentor=True))
    assert member_can_toggle_scoring(_Member())


def test_scoring_toggle_blocks_active_mutating_jobs() -> None:
    assert ACTIVE_SCORING_JOB_TYPES == ("sync", "run_checks")
    assert set(ACTIVE_JOB_STATUSES) == {"enqueued", "started", "running"}


def test_destructive_action_conflict_payload_includes_active_job_metadata() -> None:
    job_id = uuid.uuid4()
    job = BackgroundJob(id=job_id, job_type="run_checks", status="running")

    assert active_job_conflict_message("delete group", job) == (
        "Cannot delete group while run_checks is running. "
        "Wait for the active process to finish, then try again."
    )
    assert active_job_conflict_fields(job) == {
        "job_id": str(job_id),
        "job_type": "run_checks",
        "job_status": "running",
    }


def test_advisory_lock_key_stays_in_postgres_signed_integer_range() -> None:
    key = advisory_lock_key(uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))

    assert 0 <= key < 2**31


def test_project_scored_students_skip_excluded_members() -> None:
    kept = _Student(id=uuid.uuid4(), gitlab_username="kept")
    excluded = _Student(id=uuid.uuid4(), gitlab_username="excluded")
    inherited = _Student(id=uuid.uuid4(), gitlab_username="inherited")
    students = [kept, excluded, inherited]
    memberships = {
        kept.id: _Member(),
        excluded.id: _Member(excluded_from_scoring=True),
        inherited.id: _Member(membership_source="inherited"),
    }

    assert _compute_scored_students(students, memberships, set()) == [kept]

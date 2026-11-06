"""Course reports count the same eligible students and expected checks."""

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, MetaData, Table, Uuid, create_engine
from sqlalchemy.orm import Session

from app.api.dashboard.admin.analytics import _checklist, _trends_from_snapshots
from app.compliance.check_registry import CHECK_DEFS
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.services.compliance_history import ComplianceHistoryService

TODAY = date(2026, 10, 23)


@pytest.fixture
def cohort():
    metadata = MetaData()
    teams = Table(
        "teams",
        metadata,
        Column("id", Uuid),
        Column("course_id", Uuid),
        Column("is_active", Boolean, default=True),
    )
    members = Table(
        "team_members",
        metadata,
        Column("team_id", Uuid),
        Column("student_id", Uuid),
        *(
            Column(flag, Boolean, default=flag == "is_active")
            for flag in ("is_active", "is_teacher", "is_mentor", "excluded_from_scoring")
        ),
    )
    snapshots = Table(
        "metric_snapshots",
        metadata,
        Column("id", Uuid, primary_key=True),
        Column("course_id", Uuid),
        Column("team_id", Uuid),
        Column("student_id", Uuid),
        Column("computed_at", DateTime),
        Column("weighted_score", Float, default=1),
        Column("checks_detail", JSON, default=dict),
        *(Column(attr, Boolean, default=True) for attr, _, _ in CHECK_DEFS),
    )
    Table(
        "student_compliance_snapshots",
        metadata,
        Column("course_id", Uuid),
        Column("team_id", Uuid),
        Column("student_id", Uuid),
    )
    Table(
        "custom_checks",
        metadata,
        *(
            Column(
                c.name, JSON if c.name == "evaluation_rule" else c.type, primary_key=c.primary_key
            )
            for c in CustomCheck.__table__.columns
        ),
    )
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    course, team = uuid.uuid4(), uuid.uuid4()
    with Session(engine) as session:
        session.execute(teams.insert(), {"id": team, "course_id": course})

        def add_member(**flags):
            student = uuid.uuid4()
            session.execute(members.insert(), {"team_id": team, "student_id": student, **flags})
            return student

        def add_snapshot(student, **values):
            session.execute(
                snapshots.insert(),
                {
                    "id": uuid.uuid4(),
                    "course_id": course,
                    "team_id": team,
                    "student_id": student,
                    "computed_at": datetime(2026, 10, 22, tzinfo=UTC),
                    **values,
                },
            )

        yield SimpleNamespace(
            db=Mock(execute=AsyncMock(side_effect=session.execute)),
            session=session,
            course=course,
            team=team,
            teams=teams,
            members=members,
            add_member=add_member,
            add_snapshot=add_snapshot,
            weekly=metadata.tables["student_compliance_snapshots"],
            custom=metadata.tables["custom_checks"],
        )
    engine.dispose()


@pytest.mark.parametrize("excluded", ["excluded_from_scoring", "is_active", "team_inactive"])
async def test_reports_use_the_same_current_scoring_cohort(cohort, excluded):
    kept = cohort.add_member()
    removed = cohort.add_member(
        **({excluded: excluded != "is_active"} if excluded != "team_inactive" else {})
    )
    if excluded == "team_inactive":
        inactive = uuid.uuid4()
        cohort.session.execute(
            cohort.teams.insert(), {"id": inactive, "course_id": cohort.course, "is_active": False}
        )
        cohort.session.execute(
            cohort.members.update()
            .where(cohort.members.c.student_id == removed)
            .values(team_id=inactive)
        )
    cohort.add_snapshot(kept)
    cohort.add_snapshot(removed)
    rows, _, students, has_data = await _checklist(cohort.db, cohort.course, None, TODAY, "en", 50)
    assert students == 1
    assert has_data
    assert all(row["passed"] == 1 and row["pct"] == 100 for row in rows)
    trends = await _trends_from_snapshots(cohort.db, cohort.course, date(2026, 10, 19), TODAY)
    assert trends[0]["students_count"] == 1

    # Run the weekly service's actual WHERE clause; SQLite does not implement
    # PostgreSQL's ordered percentile aggregate.
    for student in (kept, removed):
        cohort.session.execute(
            cohort.weekly.insert(),
            {"course_id": cohort.course, "team_id": cohort.team, "student_id": student},
        )
    captured = Mock(execute=AsyncMock(return_value=Mock(all=lambda: [])))
    await ComplianceHistoryService(captured).get_weekly_compliance_trends(cohort.course)
    statement = captured.execute.call_args.args[0]
    predicate = (
        statement.with_only_columns(StudentComplianceSnapshot.student_id)
        .group_by(None)
        .order_by(None)
        .limit(None)
    )
    assert cohort.session.execute(predicate).scalars().all() == [kept]


async def test_one_student_with_two_simultaneous_team_snapshots_counts_once(cohort):
    student = cohort.add_member()
    other_team = uuid.uuid4()
    cohort.session.execute(cohort.teams.insert(), {"id": other_team, "course_id": cohort.course})
    cohort.session.execute(cohort.members.insert(), {"team_id": other_team, "student_id": student})
    cohort.add_snapshot(student)
    cohort.add_snapshot(student, team_id=other_team)
    rows, _, students, _ = await _checklist(cohort.db, cohort.course, None, TODAY, "en", 50)
    assert students == 1
    assert all(row["passed"] == 1 and row["pct"] == 100 for row in rows)


async def test_at_risk_uses_each_students_expected_checks(cohort):
    current, later = cohort.add_member(), cohort.add_member()
    flags = {attr: False for attr, _, _ in CHECK_DEFS}
    flags["r01_issue_assigned"] = True
    detail = {code: {"expected": False} for _, code, _ in CHECK_DEFS}
    cohort.add_snapshot(
        current,
        **flags,
        checks_detail={**detail, "R01": {"expected": True}},
    )
    cohort.add_snapshot(
        later, checks_detail={code: {"expected": True} for _, code, _ in CHECK_DEFS}
    )
    _, at_risk, _, _ = await _checklist(cohort.db, cohort.course, None, TODAY, "en", 50)
    assert at_risk == 0


async def test_exclusion_toggle_updates_reports_without_deleting_history(cohort):
    student = cohort.add_member()
    cohort.add_snapshot(student)
    for excluded in (False, True, False):
        cohort.session.execute(
            cohort.members.update()
            .where(cohort.members.c.student_id == student)
            .values(excluded_from_scoring=excluded)
        )
        rows, at_risk, students, has_data = await _checklist(
            cohort.db, cohort.course, None, TODAY, "en", 50
        )
        assert students == (0 if excluded else 1)
        assert has_data is not excluded
        assert at_risk == 0
        assert all(row["passed"] == students for row in rows)


async def test_membership_in_two_teams_does_not_double_the_denominator(cohort):
    student = cohort.add_member()
    other_team = uuid.uuid4()
    cohort.session.execute(cohort.teams.insert(), {"id": other_team, "course_id": cohort.course})
    cohort.session.execute(cohort.members.insert(), {"team_id": other_team, "student_id": student})
    cohort.add_snapshot(student)
    rows, _, students, _ = await _checklist(cohort.db, cohort.course, None, TODAY, "en", 50)
    assert students == 1
    assert all(row["pct"] == 100 for row in rows)


async def test_at_risk_respects_custom_check_deadlines_for_each_student(cohort):
    current, later = cohort.add_member(), cohort.add_member()
    cohort.session.execute(
        cohort.custom.insert(),
        {
            "id": uuid.uuid4(),
            "course_id": cohort.course,
            "check_code": "C01",
            "name": "Project milestone",
            "is_active": True,
            "sort_order": 0,
        },
    )
    cohort.add_snapshot(current, checks_detail={"C01": {"expected": False, "pass": False}})
    cohort.add_snapshot(later, checks_detail={"C01": {"expected": True, "pass": True}})
    settings = CourseSettings(enabled_checks=["R01"])
    _, at_risk, _, _ = await _checklist(cohort.db, cohort.course, settings, TODAY, "en", 80)
    assert at_risk == 0

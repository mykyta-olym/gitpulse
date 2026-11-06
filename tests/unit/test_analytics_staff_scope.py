"""A teaching role in another course must not remove a student's scores."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine

from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.services.compliance_history import ComplianceHistoryService


@pytest.mark.parametrize("flag", ["is_teacher", "is_mentor"])
@pytest.mark.parametrize("staff_in_course", [False, True])
async def test_only_staff_of_the_requested_course_are_excluded(flag, staff_in_course):
    course, other_course, team, staff_team, student = [uuid.uuid4() for _ in range(5)]
    db = Mock(execute=AsyncMock(return_value=Mock(all=lambda: [])))
    await ComplianceHistoryService(db).get_weekly_compliance_trends(course)
    statement = db.execute.call_args.args[0]
    # Execute the service's membership predicate against a small real database.
    # SQLite cannot run percentile_cont, so retain the predicate and select IDs.
    predicate = (
        statement.with_only_columns(StudentComplianceSnapshot.student_id)
        .group_by(None)
        .order_by(None)
        .limit(None)
    )
    metadata = MetaData()
    teams = Table(
        "teams",
        metadata,
        Column("id", String),
        Column("course_id", String),
        Column("is_active", Boolean, default=True),
    )
    members = Table(
        "team_members",
        metadata,
        Column("team_id", String),
        Column("student_id", String),
        Column("is_teacher", Boolean),
        Column("is_mentor", Boolean),
        Column("is_active", Boolean, default=True),
        Column("excluded_from_scoring", Boolean, default=False),
    )
    snapshots = Table(
        "student_compliance_snapshots",
        metadata,
        Column("course_id", String),
        Column("team_id", String),
        Column("student_id", String),
    )
    engine = create_engine("sqlite://")
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                teams.insert(),
                [
                    {"id": team.hex, "course_id": course.hex},
                    {
                        "id": staff_team.hex,
                        "course_id": (course if staff_in_course else other_course).hex,
                    },
                ],
            )
            connection.execute(
                members.insert(),
                {"team_id": staff_team.hex, "student_id": student.hex, flag: True},
            )
            connection.execute(
                members.insert(),
                {"team_id": team.hex, "student_id": student.hex},
            )
            connection.execute(
                snapshots.insert(),
                [
                    {"course_id": course.hex, "team_id": team.hex, "student_id": student.hex},
                    {
                        "course_id": (course if staff_in_course else other_course).hex,
                        "team_id": staff_team.hex,
                        "student_id": student.hex,
                    },
                ],
            )
            assert connection.execute(predicate).scalars().all() == (
                [] if staff_in_course else [student]
            )
    finally:
        engine.dispose()

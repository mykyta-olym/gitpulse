"""Compliance history: a student's weekly snapshots and a course's weekly trend."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.errors import raise_not_found
from app.api.helpers.utils import require_course_staff
from app.dependencies import DbSession, get_current_teacher, get_current_user
from app.models.user import User
from app.schemas.compliance import ComplianceTrendResponse, StudentComplianceHistoryResponse
from app.services.compliance_history import ComplianceHistoryService

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get(
    "/{course_id}/student/{student_id}",
    response_model=list[StudentComplianceHistoryResponse],
    summary="Get student compliance history",
)
async def get_student_compliance_history(
    course_id: uuid.UUID,
    student_id: uuid.UUID,
    db: DbSession,
    weeks: int = Query(default=52, ge=1, le=52),
    current_user: User = Depends(get_current_user),
) -> list[StudentComplianceHistoryResponse]:
    """Get compliance history for a student.

    Teachers/admins can view any student.  Students can view only their
    own data (matched by ``gitlab_username``).
    """
    if current_user.role == "student":
        from sqlalchemy import select as _sel

        from app.models.student import Student as _Stu

        _stu = await db.execute(_sel(_Stu).where(_Stu.id == student_id))
        _student = _stu.scalar_one_or_none()
        if (
            not current_user.gitlab_username
            or not _student
            or (
                (_student.gitlab_username or "").lower()
                != (current_user.gitlab_username or "").lower()
            )
        ):
            raise_not_found("Not found")
    else:
        # Teacher/admin - verify they instruct this course
        await require_course_staff(db, course_id, current_user)
    history = await ComplianceHistoryService(db).get_student_compliance_history(
        student_id, course_id, weeks
    )
    return [StudentComplianceHistoryResponse.model_validate(item) for item in history]


@router.get(
    "/{course_id}/trends",
    response_model=list[ComplianceTrendResponse],
    summary="Get compliance trends",
)
async def get_compliance_trends(
    course_id: uuid.UUID,
    db: DbSession,
    weeks: int = Query(default=52, ge=1, le=52),
    current_user: User = Depends(get_current_teacher),
) -> list[ComplianceTrendResponse]:
    """Get weekly compliance trends for a course."""
    await require_course_staff(db, course_id, current_user)
    trends = await ComplianceHistoryService(db).get_weekly_compliance_trends(course_id, weeks)
    return [
        ComplianceTrendResponse(
            week_number=t.week_number,
            week_start=t.week_start.isoformat() if t.week_start else None,
            avg_score=t.avg_score,
            std_dev=t.std_dev,
            min_score=t.min_score,
            max_score=t.max_score,
            students_count=t.students_count,
            improved_count=t.improved_count,
            declined_count=t.declined_count,
        )
        for t in trends
    ]

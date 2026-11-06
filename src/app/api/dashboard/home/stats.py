"""Dashboard home statistic-card queries.

The home route is mostly orchestration and template context assembly.
Keeping the role-specific stat SQL here gives the heavy-card logic one
owner and avoids duplicating the "latest team snapshot" subquery across
the dashboard home helpers.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select

from app.api.dashboard._helpers import _student_match_condition
from app.api.dashboard._stats import latest_team_snapshot_subquery
from app.dependencies import DbSession
from app.models.course import Course
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_metric_snapshot import TeamMetricSnapshot
from app.models.user import User

StatCard = dict[str, Any]

# Compliance bands, shared by every role so a teacher and their student read the
# same number the same way. Same thresholds as the traffic lights on the course
# pages - a card must never say "fine" about a score a table calls red.
_COMPLIANCE_DANGER_BELOW = 50
_COMPLIANCE_WARNING_BELOW = 75


def _compliance_state(score: int | None, *, has_data: bool = True) -> str:
    """Tone for a compliance percentage: empty / danger / warning / success."""
    if not has_data or score is None:
        return "empty"
    if score < _COMPLIANCE_DANGER_BELOW:
        return "danger"
    if score < _COMPLIANCE_WARNING_BELOW:
        return "warning"
    return "success"


def _apply_states(cards: list[StatCard]) -> list[StatCard]:
    """Give every card a state so the dashboard reflects the system, not just
    counts. A zero is a situation, not a healthy number: a card with nothing
    behind it says so instead of reading like a normal reading of 0.
    """
    for card in cards:
        if "state" in card:
            continue
        value = card.get("value")
        card["state"] = "empty" if value in (0, "0", "0%", None, "") else ""
    return cards


async def _count_red_teams(
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> int:
    """Count teams whose latest metric snapshot has RED traffic light.

    The same set the ids come from, so it asks for them and counts. These were
    two statements - `count(id)` here, `team_id` there - over an identical
    join, and both run on one render: the stat card wants the number while the
    attention list wants the ids to link precisely.
    """
    return len(await _red_team_ids(active_ids, db))


async def _red_team_ids(
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> list[uuid.UUID]:
    """Return the team IDs whose latest snapshot is RED (for precise linking).

    Cached on the session, which lives exactly one request: the stat card and
    the attention list both want this set, and it is a three-table join.
    """
    if not active_ids:
        return []
    cache: dict[tuple[str, ...], list[uuid.UUID]] = db.info.setdefault("red_team_ids_cache", {})
    key = tuple(sorted(str(cid) for cid in active_ids))
    cached = cache.get(key)
    if cached is not None:
        return cached
    latest_sq = latest_team_snapshot_subquery(active_ids)
    rows = await db.execute(
        select(TeamMetricSnapshot.team_id)
        .join(
            latest_sq,
            (TeamMetricSnapshot.team_id == latest_sq.c.team_id)
            & (TeamMetricSnapshot.computed_at == latest_sq.c.max_at),
        )
        .where(TeamMetricSnapshot.overall_traffic_light == "RED"),
    )
    found: list[uuid.UUID] = [r[0] for r in rows.all()]
    cache[key] = found
    return found


async def _count_student_open_mrs(
    active_ids: list[uuid.UUID],
    db: DbSession,
    auth: dict[str, str],
) -> int:
    """Count OPEN merge requests authored by the logged-in student."""
    if not active_ids:
        return 0
    student_sq = (
        select(Student.id, Student.gitlab_user_id).where(_student_match_condition(auth)).subquery()
    )
    result = await db.execute(
        select(func.count(MergeRequest.id))
        .select_from(MergeRequest)
        .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
        .join(Team, GitLabProject.team_id == Team.id)
        .join(
            student_sq,
            or_(
                MergeRequest.author_id == student_sq.c.id,
                MergeRequest.author_gitlab_id == student_sq.c.gitlab_user_id,
            ),
        )
        .where(MergeRequest.state == "opened", Team.course_id.in_(active_ids)),
    )
    return int(result.scalar() or 0)


async def _count_red_teams_per_course(
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> dict[uuid.UUID, int]:
    """Count RED-traffic-light teams grouped by course."""
    if not active_ids:
        return {}
    latest_sq = latest_team_snapshot_subquery(active_ids)
    rows = await db.execute(
        select(TeamMetricSnapshot.course_id, func.count(TeamMetricSnapshot.id))
        .join(
            latest_sq,
            (TeamMetricSnapshot.team_id == latest_sq.c.team_id)
            & (TeamMetricSnapshot.computed_at == latest_sq.c.max_at),
        )
        .where(TeamMetricSnapshot.overall_traffic_light == "RED")
        .group_by(TeamMetricSnapshot.course_id),
    )
    return {course_id: int(count or 0) for course_id, count in rows.all()}


async def _average_team_compliance(active_ids: list[uuid.UUID], db: DbSession) -> int:
    """Return the average latest team compliance score as a percentage."""
    if not active_ids:
        return 0
    latest_sq = latest_team_snapshot_subquery(active_ids)
    result = await db.execute(
        select(func.avg(TeamMetricSnapshot.avg_weighted_score)).join(
            latest_sq,
            (TeamMetricSnapshot.team_id == latest_sq.c.team_id)
            & (TeamMetricSnapshot.computed_at == latest_sq.c.max_at),
        )
    )
    raw = result.scalar()
    return round(float(raw) * 100) if raw is not None else 0


def _student_stat_cards(
    *,
    active_courses_count: int,
    my_teams: int,
    avg_score: int,
    open_mrs: int,
    course_link: str = "",
) -> list[StatCard]:
    """Build student stat-card dictionaries from already-computed values."""
    return _apply_states(
        [
            {
                "id": "statActiveCourses",
                "label": "Courses",
                "icon": "book",
                "value": active_courses_count,
                "desc": "Enrolled courses",
                "time": "Current semester",
                # The caption names the period on screen (see _content.html).
                "scoped": True,
                "link": course_link,
            },
            {
                "id": "statMyTeams",
                "label": "Groups",
                "icon": "users",
                "value": my_teams,
                "desc": "Your groups",
                "time": "Active enrollments",
                "link": course_link,
            },
            {
                "id": "statCompliance",
                "label": "Score",
                "icon": "check-circle",
                "value": f"{avg_score}%",
                "desc": "Compliance score",
                "time": "Weighted average",
                "link": course_link,
                "state": _compliance_state(avg_score, has_data=active_courses_count > 0),
            },
            {
                "id": "statOpenMrs",
                "label": "Open MRs",
                "icon": "git-merge",
                "value": open_mrs,
                "desc": "Your merge requests",
                "time": "Awaiting review",
                "link": course_link,
            },
        ]
    )


async def _build_student_stat_cards(
    active_courses: list[Course],
    active_ids: list[uuid.UUID],
    db: DbSession,
    auth: dict[str, str],
) -> list[StatCard]:
    """Build student stat cards, skipping DB work when no active course exists."""
    if not active_ids:
        return _student_stat_cards(
            active_courses_count=0,
            my_teams=0,
            avg_score=0,
            open_mrs=0,
        )

    student_match = _student_match_condition(auth)
    my_teams_r = await db.execute(
        select(func.count(func.distinct(Team.id)))
        .select_from(TeamMember)
        .join(Team, TeamMember.team_id == Team.id)
        .join(Student, TeamMember.student_id == Student.id)
        .where(
            Team.course_id.in_(active_ids),
            Team.is_active.is_(True),
            student_match,
        ),
    )
    my_teams = int(my_teams_r.scalar() or 0)

    latest_student_sq = (
        select(
            MetricSnapshot.team_id,
            func.max(MetricSnapshot.computed_at).label("max_at"),
        )
        .join(Student, MetricSnapshot.student_id == Student.id)
        .where(
            MetricSnapshot.course_id.in_(active_ids),
            student_match,
        )
        .group_by(MetricSnapshot.team_id)
        .subquery()
    )
    avg_score_r = await db.execute(
        select(func.avg(MetricSnapshot.weighted_score))
        .select_from(MetricSnapshot)
        .join(Student, MetricSnapshot.student_id == Student.id)
        .join(
            latest_student_sq,
            (MetricSnapshot.team_id == latest_student_sq.c.team_id)
            & (MetricSnapshot.computed_at == latest_student_sq.c.max_at),
        )
        .where(
            MetricSnapshot.course_id.in_(active_ids),
            student_match,
        ),
    )
    raw_score = avg_score_r.scalar()
    avg_score = round(float(raw_score) * 100) if raw_score is not None else 0
    open_mrs = await _count_student_open_mrs(active_ids, db, auth)

    one_course = active_courses[0].id if len(active_courses) == 1 else None
    return _student_stat_cards(
        active_courses_count=len(active_courses),
        my_teams=my_teams,
        avg_score=avg_score,
        open_mrs=open_mrs,
        course_link=f"/dashboard/courses/{one_course}" if one_course else "",
    )


async def _build_stat_cards(
    role: str,
    active_courses: list[Course],
    active_ids: list[uuid.UUID],
    db: DbSession,
    auth: dict[str, str],
    *,
    total_teams: int = 0,
    total_students: int = 0,
    period_key: str = "",
) -> list[StatCard]:
    """Build stat cards appropriate for the user's dashboard role.

    Cards marked ``scoped`` describe the courses of the academic period on
    screen, and their caption says which period instead of a fixed "Current
    semester". ``period_key`` carries that period into the links, so the page a
    card opens shows the figure the card showed.
    """
    _period_q = f"period={period_key}" if period_key else ""
    if role == "admin":
        users_r = await db.execute(
            select(func.count(User.id)).where(User.is_active.is_(True), User.is_bot.is_(False))
        )
        total_users = int(users_r.scalar() or 0)
        avg_comp = await _average_team_compliance(active_ids, db)
        return _apply_states(
            [
                {
                    "id": "statTotalUsers",
                    "label": "Users",
                    "icon": "users",
                    "value": total_users,
                    "desc": "Active users",
                    "time": "All roles",
                    # Every account, so every period - User Management opens
                    # on one term by default and would show fewer.
                    "link": "/dashboard/admin/users?period=all",
                },
                {
                    "id": "statTotalStudents",
                    "label": "Students",
                    "icon": "user",
                    "value": total_students,
                    "desc": "Student accounts",
                    "time": "Registered users",
                    "scoped": True,
                    "link": "/dashboard/admin/users?role=student"
                    + (f"&{_period_q}" if _period_q else ""),
                },
                {
                    "id": "statCompliance",
                    "label": "Compliance",
                    "icon": "check-circle",
                    "value": f"{avg_comp}%",
                    "desc": "Avg. compliance score",
                    "time": "Across all active courses",
                    "scoped": True,
                    "link": "/dashboard/admin/courses" + (f"?{_period_q}" if _period_q else ""),
                    "state": _compliance_state(avg_comp, has_data=bool(active_ids)),
                },
                {
                    "id": "statGroups",
                    "label": "Groups",
                    "icon": "users",
                    "value": total_teams,
                    "desc": "Active groups",
                    "time": "Across active courses",
                    "scoped": True,
                    "link": "/dashboard/admin/courses" + (f"?{_period_q}" if _period_q else ""),
                },
            ]
        )

    if role == "teacher":
        avg_comp = await _average_team_compliance(active_ids, db)
        one_course = active_courses[0].id if len(active_courses) == 1 else None
        course_link = f"/dashboard/courses/{one_course}" if one_course else ""
        analytics_link = f"/dashboard/courses/{one_course}/analytics" if one_course else ""
        return _apply_states(
            [
                {
                    "id": "statActiveCourses",
                    "label": "Courses",
                    "icon": "book",
                    "value": len(active_courses),
                    "desc": "Active courses",
                    "time": "Current semester",
                    "scoped": True,
                    "link": course_link,
                },
                {
                    "id": "statTotalStudents",
                    "label": "Students",
                    "icon": "user",
                    "value": total_students,
                    "desc": "Student accounts",
                    "time": "Registered users",
                    "scoped": True,
                    "link": course_link,
                },
                {
                    "id": "statCompliance",
                    "label": "Compliance",
                    "icon": "check-circle",
                    "value": f"{avg_comp}%",
                    "desc": "Avg. compliance score",
                    "time": "Across all active courses",
                    "scoped": True,
                    "link": analytics_link,
                    "state": _compliance_state(avg_comp, has_data=bool(active_ids)),
                },
                {
                    "id": "statGroups",
                    "label": "Groups",
                    "icon": "users",
                    "value": total_teams,
                    "desc": "Active groups",
                    "time": "Across active courses",
                    "scoped": True,
                    "link": course_link,
                },
            ]
        )

    return await _build_student_stat_cards(active_courses, active_ids, db, auth)

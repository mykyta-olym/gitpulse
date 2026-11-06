"""Access-control helpers for dashboard routes."""

import structlog
from fastapi import Request
from sqlalchemy import or_, select

from app.config import get_settings
from app.dependencies import DbSession, _extract_bearer_token, _validate_session
from app.models.course import Course
from app.models.course_membership import COURSE_ROLES, CourseMembership
from app.models.student import Student
from app.models.team import Team
from app.models.user import User
from app.security.course_roles import role_gte
from app.utils.constants import NO_LOGIN_HASH

from ._helpers import _student_match_condition

logger = structlog.get_logger(__name__)


async def _session_user_id(db: DbSession, session_data: dict[str, str]) -> object | None:
    """The logged-in user's User id, by GitLab username or username."""
    gitlab_username = session_data.get("gitlab_username", "")
    username = session_data.get("user", "")

    user_stmt = select(User.id).where(User.is_active.is_(True))
    conditions = []
    if gitlab_username:
        conditions.append(User.gitlab_username == gitlab_username)
    if username:
        conditions.append(User.username == username)
    if not conditions:
        return None

    user_row = (await db.execute(user_stmt.where(or_(*conditions)))).first()
    return user_row[0] if user_row else None


async def _membership_role(
    db: DbSession,
    course_id: object,
    session_data: dict[str, str],
) -> str | None:
    """Return the CourseMembership role for the logged-in user, or None."""
    user_id = await _session_user_id(db, session_data)
    if user_id is None:
        return None

    mem_stmt = select(CourseMembership.role).where(
        CourseMembership.user_id == user_id,
        CourseMembership.course_id == course_id,
    )
    return (await db.execute(mem_stmt)).scalar_one_or_none()


#: The course roles that run a course - ``is_course_staff``'s "teacher or
#: above". What only they (and an admin) may touch - the classroom assistant:
#: its page, its bot token, its tools - is closed to everyone else who can
#: merely see the course: a member of one of its teams, a mentor, someone
#: whose course role is student.
COURSE_STAFF_ROLES = tuple(r for r in COURSE_ROLES if role_gte(r, "teacher"))


def _runs_course(session_data: dict[str, str], course_role: str | None) -> bool:
    """An admin, or the course's owner or teacher."""
    return session_data.get("role") == "admin" or course_role in COURSE_STAFF_ROLES


async def _can_manage_course(course: Course, session_data: dict[str, str], db: DbSession) -> bool:
    """Configuration belongs to the course's staff, even for global teachers."""
    if session_data.get("role") == "admin":
        return True
    return _runs_course(session_data, await _membership_role(db, course.id, session_data))


async def _can_manage_team(team: Team, session_data: dict[str, str], db: DbSession) -> bool:
    """Team mutations require course staff, rather than team membership alone."""
    if session_data.get("role") == "admin":
        return True
    return _runs_course(session_data, await _membership_role(db, team.course_id, session_data))


async def _staff_course_ids(
    db: DbSession, course_ids: list[object], session_data: dict[str, str]
) -> set[object]:
    """Of ``course_ids``, the ones the reader runs (``_runs_course``)."""
    if session_data.get("role") == "admin":
        return set(course_ids)
    user_id = await _session_user_id(db, session_data)
    if user_id is None or not course_ids:
        return set()
    stmt = select(CourseMembership.course_id).where(
        CourseMembership.user_id == user_id,
        CourseMembership.course_id.in_(course_ids),
        CourseMembership.role.in_(COURSE_STAFF_ROLES),
    )
    return set((await db.execute(stmt)).scalars().all())


async def _can_view_course(
    course: Course,
    session_data: dict[str, str],
    db: DbSession | None = None,
) -> bool:
    """Check if current user can view the course.

    Access rules (evaluated in order):
    1. Admin: can view ALL courses
    2. CourseMembership: any membership role grants visibility
    3. Team membership: student or teacher in a team -> can view
    """
    role = session_data.get("role", "student")

    # 1. Admins see everything
    if role == "admin":
        return True

    if db is not None:
        # 2. Check CourseMembership (source of truth for per-course roles)
        mem_role = await _membership_role(db, course.id, session_data)
        if mem_role is not None:
            return True

    # 3. Any non-admin user: must be a member of a team in this course
    if db is not None:
        from app.models.team_member import TeamMember

        student_stmt = (
            select(TeamMember)
            .join(Team, TeamMember.team_id == Team.id)
            .join(Student, TeamMember.student_id == Student.id)
            .where(
                Team.course_id == course.id,
                _student_match_condition(session_data),
            )
        )
        result = await db.execute(student_stmt)
        return result.first() is not None

    return False


async def _can_view_team(team: Team, session_data: dict[str, str], db: DbSession) -> bool:
    """Check if current user can view the team.

    Access rules:
    1. Admin: can view ALL teams
    2. CourseMembership with role >= teacher: can view any team in the course
    3. Team membership: must be a member of THIS team
    """
    role = session_data.get("role", "student")

    # 1. Admins see everything
    if role == "admin":
        return True

    # Load course for checks
    course = await db.get(Course, team.course_id)
    if not course:
        return False

    # 2. CourseMembership check
    mem_role = await _membership_role(db, course.id, session_data)
    if mem_role is not None and role_gte(mem_role, "teacher"):
        return True

    # 3. Any non-admin user: must be a member of THIS team
    from app.models.team_member import TeamMember

    member_stmt = (
        select(TeamMember)
        .join(Student, TeamMember.student_id == Student.id)
        .where(
            TeamMember.team_id == team.id,
            _student_match_condition(session_data),
        )
    )
    result = await db.execute(member_stmt)
    return result.first() is not None


async def can_manage_via_request(
    request: Request,
    db: DbSession,
    *,
    course: Course | None = None,
    team: Team | None = None,
    project: object | None = None,
) -> bool:
    """Authorize API writes for admins, bearer clients or the owning course's staff.

    Supply one scope. Viewing a course or belonging to a team alone does not
    grant mutation rights to a session-authenticated global teacher.
    """
    if _extract_bearer_token(request) is not None:
        return True

    session_data = _validate_session(request, get_settings())
    if not session_data:
        return False
    if session_data.get("role") == "admin":
        return True

    if course is not None:
        return await _can_manage_course(course, session_data, db)
    if team is not None:
        return await _can_manage_team(team, session_data, db)
    if project is not None:
        team_id = getattr(project, "team_id", None)
        if team_id is None:
            return False
        owning_team = await db.get(Team, team_id)
        return bool(owning_team and await _can_manage_team(owning_team, session_data, db))
    return False


async def can_view_student_via_request(
    request: Request,
    db: DbSession,
    student: Student,
) -> bool:
    """Authorize viewing a single Student for a REST endpoint that authenticates
    with ``ApiTeacherAuth`` (a bare string identity).

    The read counterpart of :func:`can_manage_via_request`. Bearer tokens and
    admins are unrestricted; a session teacher must share at least one course
    with the student - resolved via the student's active team memberships
    intersected with the teacher's CourseMembership rows - so a teacher can't
    read the name/email of a student in a course they don't teach.
    """
    if _extract_bearer_token(request) is not None:
        return True

    session_data = _validate_session(request, get_settings())
    if not session_data:
        return False
    if session_data.get("role") == "admin":
        return True

    from app.models.team_member import TeamMember

    viewer_id = await _session_user_id(db, session_data)
    if viewer_id is None:
        return False

    student_courses = (
        select(Team.course_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.student_id == student.id, TeamMember.is_active.is_(True))
    )
    shared = (
        await db.execute(
            select(CourseMembership.id)
            .where(
                CourseMembership.user_id == viewer_id,
                CourseMembership.course_id.in_(student_courses),
            )
            .limit(1)
        )
    ).first()
    return shared is not None


async def _filter_courses_for_user(
    courses: list[Course],
    session_data: dict[str, str],
    db: DbSession,
) -> list[Course]:
    """Filter courses to only those the user can view.

    Checks CourseMembership first, then team membership.
    """
    role = session_data.get("role", "student")

    # Admins see everything
    if role == "admin":
        return courses

    if not courses:
        return []

    membership_course_ids: set[object] = set()
    user_id = await _session_user_id(db, session_data)
    if user_id is not None:
        course_ids_all = [c.id for c in courses]
        mem_stmt = select(CourseMembership.course_id).where(
            CourseMembership.user_id == user_id,
            CourseMembership.course_id.in_(course_ids_all),
        )
        mem_result = await db.execute(mem_stmt)
        membership_course_ids = {row[0] for row in mem_result.all()}

    accessible: list[Course] = []
    remaining: list[Course] = []

    for c in courses:
        if c.id in membership_course_ids:
            accessible.append(c)
        else:
            remaining.append(c)

    # For remaining courses, check team membership
    if remaining:
        from app.models.team_member import TeamMember

        rem_ids = [c.id for c in remaining]
        member_stmt = (
            select(Team.course_id)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .join(Student, TeamMember.student_id == Student.id)
            .where(
                Team.course_id.in_(rem_ids),
                _student_match_condition(session_data),
            )
            .distinct()
        )
        result = await db.execute(member_stmt)
        member_course_ids = {row[0] for row in result.all()}
        accessible.extend(c for c in remaining if c.id in member_course_ids)

    return accessible


async def _filter_teams_for_user(
    teams: list[Team],
    session_data: dict[str, str],
    db: DbSession,
) -> list[Team]:
    """Filter teams to only those the user can view.

    Checks CourseMembership (role >= teacher) first, then team-level membership.
    """
    role = session_data.get("role", "student")

    if role == "admin":
        return teams

    if not teams:
        return []

    membership_course_ids: set[object] = set()
    user_id = await _session_user_id(db, session_data)
    if user_id is not None:
        course_ids_from_teams = list({t.course_id for t in teams})
        mem_stmt = select(CourseMembership.course_id).where(
            CourseMembership.user_id == user_id,
            CourseMembership.course_id.in_(course_ids_from_teams),
            CourseMembership.role.in_(COURSE_STAFF_ROLES),
        )
        mem_result = await db.execute(mem_stmt)
        membership_course_ids = {row[0] for row in mem_result.all()}

    # Teams in courses where user has a staff membership -> visible
    staff_teams: list[Team] = []
    member_check_teams: list[Team] = []

    for t in teams:
        if t.course_id in membership_course_ids:
            staff_teams.append(t)
        else:
            member_check_teams.append(t)

    # For remaining teams, check team-level membership
    if member_check_teams:
        from app.models.team_member import TeamMember

        check_ids = [t.id for t in member_check_teams]
        member_stmt = (
            select(TeamMember.team_id)
            .distinct()
            .join(Student, TeamMember.student_id == Student.id)
            .where(
                TeamMember.team_id.in_(check_ids),
                _student_match_condition(session_data),
            )
        )
        result = await db.execute(member_stmt)
        member_ids = {row[0] for row in result.all()}
        staff_teams.extend(t for t in member_check_teams if t.id in member_ids)

    return staff_teams


async def _ensure_session_user_in_db(
    db: DbSession,
    auth: dict[str, str],
) -> None:
    """Guarantee the session user has a row in the Users table.

    After a DB restart/wipe the session cookie is still valid but the
    Users table is empty.  This causes dashboard stat cards to show
    ``0 Active Users``.  Calling this at the start of every
    ``dashboard_home`` request makes the dashboard self-healing.
    Only creates new rows in debug mode to match the existing dev-login
    pattern.
    """
    from app.models.user import User

    username = auth.get("user")
    if not username:
        return

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is not None:
        return

    settings = get_settings()
    if not settings.debug:
        return

    new_user = User(
        username=username,
        full_name=auth.get("full_name", username),
        email=auth.get("email", f"{username}@dev.local"),
        password_hash=NO_LOGIN_HASH,
        role=auth.get("role", "student"),
        is_active=True,
        gitlab_username=auth.get("gitlab_username", username),
    )
    db.add(new_user)
    await db.flush()


async def _is_session_user_active(
    db: DbSession,
    auth: dict[str, str],
) -> bool:
    """Return True when the session user exists and is active.

    Used as a guard on sensitive dashboard routes to immediately reject
    deactivated accounts even before their session cookie expires.
    """
    from app.models.user import User

    username = auth.get("user")
    if not username:
        return False

    result = await db.execute(select(User.is_active).where(User.username == username))
    row = result.first()
    # If user not in DB, allow (they may be on the login page or debug mode)
    if row is None:
        return True
    return bool(row[0])

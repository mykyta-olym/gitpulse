"""What a members table reads about its people beyond the roster itself."""

from typing import Any

from sqlalchemy import select

from app.dependencies import DbSession
from app.models.course import Course


async def member_roles(
    db: DbSession,
    students: list[Any],
    course: Course | None,
) -> tuple[dict[str, str], dict[str, str]]:
    """The app role (``User.role``) and the course role (owner / teacher) of
    each member, keyed by lower-cased GitLab username - the badges on the group
    and project members tables."""
    user_roles: dict[str, str] = {}
    course_roles: dict[str, str] = {}
    usernames = [s.gitlab_username for s in students if s.gitlab_username]
    if not usernames:
        return user_roles, course_roles
    from app.models.user import User

    role_stmt = select(User.gitlab_username, User.role).where(User.gitlab_username.in_(usernames))
    for uname, role in (await db.execute(role_stmt)).all():
        if uname:
            user_roles[uname.lower()] = role
    if course:
        from app.models.course_membership import CourseMembership

        cm_stmt = (
            select(User.gitlab_username, CourseMembership.role)
            .join(CourseMembership, CourseMembership.user_id == User.id)
            .where(
                User.gitlab_username.in_(usernames),
                CourseMembership.course_id == course.id,
                CourseMembership.role.in_(("owner", "teacher")),
            )
        )
        for uname, crole in (await db.execute(cm_stmt)).all():
            if uname:
                course_roles[uname.lower()] = crole
    return user_roles, course_roles

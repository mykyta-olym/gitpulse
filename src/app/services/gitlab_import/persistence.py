"""Persistence layer for GitLab group import: course/team/student/project upserts."""

import secrets
import uuid
from collections import deque
from datetime import UTC, date, datetime
from datetime import datetime as _dt
from typing import Any

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.membership_change import MembershipChange
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.security.webhook_auth import (
    compute_webhook_lookup_key,
    generate_webhook_secret,
    hash_webhook_secret,
)
from app.services.gitlab.client import GitLabClient
from app.services.gitlab_import.helpers import is_bot_user
from app.services.gitlab_import.normalize import (
    _normalize_nonempty,
    _normalize_optional,
    _to_int,
    _to_positive_int,
)
from app.utils.constants import DEFAULT_MR_TEMPLATE_SECTIONS, DEFAULT_TEST_FILE_PATTERNS

logger = structlog.get_logger(__name__)


_TEACHER_ACCESS_LEVEL = 40  # Maintainer / Owner


async def _collect_subgroups(client: GitLabClient, root_group_id: int) -> list[dict[str, Any]]:
    """Recursively collect all descendant subgroups."""
    descendants: list[dict[str, Any]] = []
    seen: set[int] = set()
    queue: deque[int] = deque([root_group_id])

    while queue:
        current_group_id = queue.popleft()
        direct_subgroups = await client.get_group_subgroups(current_group_id)
        for subgroup in direct_subgroups:
            subgroup_id = _to_int(subgroup.get("id"))
            if subgroup_id <= 0 or subgroup_id in seen:
                continue
            seen.add(subgroup_id)
            descendants.append(subgroup)
            queue.append(subgroup_id)

    return descendants


def _ensure_not_archived(course: Course) -> None:
    """Refuse to import into an archived course (it is read-only)."""
    if not course.is_active:
        raise ValueError(
            f"Course {course.code} ({course.academic_year} {course.semester}) is archived "
            "and read-only. Reactivate it before importing into it."
        )


async def _get_or_create_course(
    db: AsyncSession,
    *,
    target_course_id: uuid.UUID | None,
    code: str,
    name: str,
    academic_year: str,
    semester: str,
    semester_start_date: date | None = None,
    semester_end_date: date | None = None,
) -> tuple[Course, CourseSettings, bool]:
    created = False

    if target_course_id is not None:
        course = await db.get(Course, target_course_id)
        if course is None:
            raise ValueError(f"Target course not found: {target_course_id}")
        # An archived course is read-only. Importing into one used to silently
        # flip is_active back to True, un-archiving it as a side effect.
        _ensure_not_archived(course)
    else:
        stmt = select(Course).where(
            Course.code == code,
            Course.academic_year == academic_year,
            Course.semester == semester,
        )
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()

        if course is None:
            course = Course(
                code=code,
                name=name,
                academic_year=academic_year,
                semester=semester,
            )
            db.add(course)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                result = await db.execute(stmt)
                course = result.scalar_one()
            else:
                created = True
        else:
            # Same guard as the explicit-target branch: a re-import that happens
            # to match an archived course by code/year/semester must not quietly
            # bring it back to life.
            _ensure_not_archived(course)
            course.name = name

    settings_stmt = select(CourseSettings).where(CourseSettings.course_id == course.id)
    settings_result = await db.execute(settings_stmt)
    course_settings = settings_result.scalar_one_or_none()
    if course_settings is None:
        course_settings = CourseSettings(
            course_id=course.id,
            mr_template_required_sections=list(DEFAULT_MR_TEMPLATE_SECTIONS),
            test_file_patterns=list(DEFAULT_TEST_FILE_PATTERNS),
            semester_start_date=semester_start_date,
            semester_end_date=semester_end_date,
        )
        db.add(course_settings)
        await db.flush()
    else:
        # Only fill missing values - never overwrite existing dates so a
        # second import run with a different / empty preset can't wipe
        # what the teacher already configured manually.
        if semester_start_date is not None and course_settings.semester_start_date is None:
            course_settings.semester_start_date = semester_start_date
        if semester_end_date is not None and course_settings.semester_end_date is None:
            course_settings.semester_end_date = semester_end_date

    return course, course_settings, created


async def _upsert_team(
    db: AsyncSession,
    *,
    course_id: uuid.UUID,
    name: str,
    gitlab_group_id: int,
    gitlab_group_path: str,
) -> tuple[Team, bool]:
    # 1. Exact match by GitLab group/project ID
    stmt = select(Team).where(Team.course_id == course_id, Team.gitlab_group_id == gitlab_group_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    # 2. Exact match by GitLab group path
    if team is None:
        stmt_by_path = select(Team).where(
            Team.course_id == course_id,
            Team.gitlab_group_path == gitlab_group_path,
        )
        result_by_path = await db.execute(stmt_by_path)
        team = result_by_path.scalar_one_or_none()

    # 3. Path-prefix match: a group import should subsume a single-project
    #    team whose path is a child of the group being imported.
    #    e.g. importing group "zsi-labs/.../km-3" should match existing team
    #    with path "zsi-labs/.../km-3/mines-8939" (created by single-project import).
    if team is None:
        prefix = gitlab_group_path.lower() + "/"
        all_course_teams_stmt = select(Team).where(
            Team.course_id == course_id,
            Team.gitlab_group_path.isnot(None),
        )
        all_teams_result = await db.execute(all_course_teams_stmt)
        for candidate in all_teams_result.scalars().all():
            cpath = (candidate.gitlab_group_path or "").lower()
            if cpath.startswith(prefix) or cpath == gitlab_group_path.lower():
                team = candidate
                break

    # 4. Exact match by name
    if team is None:
        stmt_by_name = select(Team).where(Team.course_id == course_id, Team.name == name)
        result_by_name = await db.execute(stmt_by_name)
        team = result_by_name.scalar_one_or_none()

    if team is None:
        team = Team(
            course_id=course_id,
            name=name,
            gitlab_group_id=gitlab_group_id,
            gitlab_group_path=gitlab_group_path,
        )
        db.add(team)
        await db.flush()
        return team, True

    team.name = name
    team.gitlab_group_id = gitlab_group_id
    team.gitlab_group_path = gitlab_group_path
    # Do NOT re-activate soft-deleted teams - respect manual deletion
    await db.flush()
    return team, False


async def _upsert_student(db: AsyncSession, member: dict[str, Any]) -> tuple[Student, bool]:
    gitlab_user_id = _to_positive_int(member.get("id"), "GitLab user id")
    username = _normalize_nonempty(member.get("username"), fallback=f"user-{gitlab_user_id}")
    full_name = _normalize_optional(member.get("name"))
    email = _normalize_optional(member.get("email")) or "PRIVATE"

    stmt = select(Student).where(Student.gitlab_user_id == gitlab_user_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if student is None:
        student = Student(
            gitlab_user_id=gitlab_user_id,
            gitlab_username=username,
            full_name=full_name,
            email=email,
        )
        db.add(student)
        await db.flush()
        return student, True

    if username and username != student.gitlab_username:
        student.gitlab_username = username
    if full_name and not student.full_name:
        student.full_name = full_name
    if email and email != "PRIVATE" and (not student.email or student.email == "PRIVATE"):
        student.email = email
    await db.flush()
    return student, False


async def _import_student_team_member(
    db: AsyncSession,
    *,
    member: dict[str, Any],
    team: Team,
    discovered_teachers: set[str],
    seen_gitlab_user_ids: set[int],
    membership_source: str = "direct",
    is_group_member: bool = False,
    root_group_usernames: set[str] | None = None,
) -> tuple[bool, bool, str] | None:
    """Import one member as team student membership when applicable.

    Returns:
    - tuple(created_student, created_membership, role_label) when member was imported,
      where role_label is 'owner', 'teacher', or 'student'.
    - None when member should be skipped (invalid/bot/already processed).
    """
    gitlab_user_id = _to_int(member.get("id"))
    if gitlab_user_id <= 0 or gitlab_user_id in seen_gitlab_user_ids:
        return None
    seen_gitlab_user_ids.add(gitlab_user_id)

    username = _normalize_optional(member.get("username"))
    if not username:
        return None
    access_level = _to_int(member.get("access_level"))
    if access_level <= 0:
        return None

    # Skip bots / service accounts
    if is_bot_user(username, user_type=_normalize_optional(member.get("user_type"))):
        logger.info("import_skip_bot", username=username)
        return None

    # Detect teachers but still import them as team members so they
    # appear in the members table when they actively participate.
    # Uses only GitLab structure (discovered_teachers + Owner access),
    # NOT the global User.role - a teacher in Course A should not be
    # auto-detected as teacher in Course B.
    is_teacher = _is_teacher_member(
        username=username,
        discovered_teachers=discovered_teachers,
        access_level=access_level,
        is_group_member=is_group_member,
        root_group_usernames=root_group_usernames,
    )

    if is_teacher:
        discovered_teachers.add(username)

    student, created_student = await _upsert_student(db, member)
    # Preserve existing teacher/admin role - don't downgrade to student
    await _upsert_user_role(
        db,
        username=student.gitlab_username,
        email=student.email,
        full_name=student.full_name,
        role="teacher" if is_teacher else "student",
        gitlab_user_id=gitlab_user_id,
    )
    created_membership = await _ensure_team_membership(
        db,
        team.id,
        student.id,
        gitlab_access_level=access_level,
        gitlab_access_role=gitlab_access_role_name(access_level),
        membership_source=membership_source,
        is_teacher=is_teacher,
    )
    # Determine display label from the *course* role (CourseMembership),
    # not from GitLab access_level - a GitLab Owner may only be an
    # teacher in this particular course.  Check for ALL members,
    # not just GitLab-detected teachers, because someone may have
    # been manually assigned as teacher in the course settings
    # despite having a low GitLab access level.
    from app.models.course_membership import CourseMembership

    cm_stmt = (
        select(CourseMembership.role)
        .join(User, CourseMembership.user_id == User.id)
        .where(
            or_(
                User.gitlab_username == username,
                User.username == username,
            ),
            CourseMembership.course_id == team.course_id,
        )
    )
    cm_role = (await db.execute(cm_stmt)).scalar_one_or_none()
    if cm_role in ("owner", "teacher"):
        _role_label = cm_role
    elif is_teacher:
        _role_label = "teacher"
    else:
        _role_label = "student"
    return created_student, created_membership, _role_label


async def _ensure_team_membership(
    db: AsyncSession,
    team_id: uuid.UUID,
    student_id: uuid.UUID,
    *,
    gitlab_access_level: int | None,
    gitlab_access_role: str | None,
    membership_source: str = "direct",
    is_teacher: bool = False,
) -> bool:

    now = _dt.now(UTC)
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.student_id == student_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        changed = False
        if gitlab_access_level is not None and existing.gitlab_access_level != gitlab_access_level:
            existing.gitlab_access_level = gitlab_access_level
            changed = True
        if gitlab_access_role and existing.gitlab_access_role != gitlab_access_role:
            existing.gitlab_access_role = gitlab_access_role
            changed = True
        if existing.membership_source != membership_source:
            existing.membership_source = membership_source
            changed = True
        if existing.is_teacher != is_teacher:
            existing.is_teacher = is_teacher
            changed = True
        # Ensure active on import
        if not existing.is_active:
            existing.is_active = True
            existing.left_at = None
            changed = True
        existing.last_synced_at = now
        if changed:
            await db.flush()
        return False

    db.add(
        TeamMember(
            team_id=team_id,
            student_id=student_id,
            gitlab_access_level=gitlab_access_level,
            gitlab_access_role=gitlab_access_role,
            membership_source=membership_source,
            is_teacher=is_teacher,
            is_active=True,
            last_synced_at=now,
        )
    )
    await db.flush()
    return True


async def _upsert_project(
    db: AsyncSession,
    team_id: uuid.UUID,
    project_data: dict[str, Any],
) -> tuple[GitLabProject, bool]:
    gitlab_project_id = _to_positive_int(project_data.get("id"), "GitLab project id")
    path_with_namespace = _normalize_nonempty(
        project_data.get("path_with_namespace"),
        fallback=_normalize_optional(project_data.get("path")) or "",
    )
    if not path_with_namespace:
        raise ValueError("Project is missing path_with_namespace")

    # GitLab leaves "deletion_scheduled" tombstone projects visible via the
    # API for a short window after a project is deleted.  Persisting them
    # creates ghost rows under teams that show up as duplicates in the UI.
    if "deletion_scheduled" in path_with_namespace.lower():
        logger.info(
            "import_skip_deletion_scheduled_project",
            gitlab_project_id=gitlab_project_id,
            path=path_with_namespace,
        )
        raise ValueError(
            f"Skipping GitLab tombstone project '{path_with_namespace}' "
            f"(marked deletion_scheduled by GitLab)"
        )

    name = _normalize_optional(project_data.get("name")) or path_with_namespace.split("/")[-1]
    default_branch = _normalize_optional(project_data.get("default_branch")) or "main"

    stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        # Path collision: another project already occupies this path with a
        # different gitlab_project_id.  Real-world cause: the original GitLab
        # project was deleted/renamed and a fresh one was created at the same
        # path.  GitLab paths are unique, so the old DB row is now stale and
        # must be soft-deleted to prevent ghost duplicates in the UI.
        path_collision_stmt = select(GitLabProject).where(
            GitLabProject.gitlab_project_path == path_with_namespace,
            GitLabProject.gitlab_project_id != gitlab_project_id,
            GitLabProject.is_active.is_(True),
        )
        for stale in (await db.execute(path_collision_stmt)).scalars().all():
            logger.warning(
                "import_path_collision_deactivate_stale",
                stale_project_db_id=str(stale.id),
                stale_gitlab_project_id=stale.gitlab_project_id,
                new_gitlab_project_id=gitlab_project_id,
                path=path_with_namespace,
            )
            stale.is_active = False

        _new_secret = generate_webhook_secret()
        webhook_secret_hash = hash_webhook_secret(_new_secret)
        project = GitLabProject(
            team_id=team_id,
            gitlab_project_id=gitlab_project_id,
            gitlab_project_path=path_with_namespace,
            gitlab_project_name=name,
            default_branch=default_branch,
            webhook_secret_hash=webhook_secret_hash,
            webhook_secret_lookup=compute_webhook_lookup_key(_new_secret),
            is_active=True,
        )
        db.add(project)
        await db.flush()
        return project, True

    # -- Existing project found - check for cross-course conflict --
    old_team_id = project.team_id
    if old_team_id != team_id:
        # Load both teams to compare courses
        old_team = await db.get(Team, old_team_id)
        new_team = await db.get(Team, team_id)
        if old_team and new_team and old_team.course_id != new_team.course_id:
            # Cross-course reassignment - refuse to steal project
            logger.warning(
                "import_cross_course_project_conflict",
                gitlab_project_id=gitlab_project_id,
                path=path_with_namespace,
                existing_course_id=str(old_team.course_id),
                new_course_id=str(new_team.course_id),
                existing_team=old_team.name,
                new_team=new_team.name,
            )
            raise ValueError(
                f"Project '{path_with_namespace}' (GitLab ID {gitlab_project_id}) "
                f"already belongs to another course (team '{old_team.name}'). "
                f"Remove it from the other course first, or use the same target course."
            )

        # Same-course reassignment - transfer student memberships from old team
        if old_team and new_team and old_team.course_id == new_team.course_id:
            await _transfer_memberships_on_reassign(db, old_team_id, team_id)

    project.team_id = team_id
    project.gitlab_project_path = path_with_namespace
    project.gitlab_project_name = name
    project.default_branch = default_branch
    # Do NOT re-activate soft-deleted projects - respect manual deletion
    if not project.webhook_secret_hash:
        project.webhook_secret_hash = hash_webhook_secret(generate_webhook_secret())
    await db.flush()
    return project, False


async def _deactivate_missing_projects_for_course(
    db: AsyncSession,
    *,
    course_id: uuid.UUID,
    root_group_path: str,
    live_gitlab_project_ids: set[int],
) -> tuple[int, int]:
    """Deactivate active DB projects no longer returned by the GitLab group import.

    A direct project sync handles 404s one project at a time. Course/group import
    has a stronger signal: GitLab returns the complete current project list for
    the configured group tree. After a successful import, any active project in
    this course and under that group path that is absent from the live list is a
    stale ghost and must disappear from active views.

    This helper deliberately flushes but does not commit; import endpoints commit
    once after all course/team/project state is consistent.
    """
    root_path = _normalize_optional(root_group_path)
    if not root_path:
        return 0, 0
    if not live_gitlab_project_ids:
        # An empty answer is not a list of what is gone. GitLab returns 200 []
        # for a group whose projects the token cannot see, and this used to
        # read that as "every project was deleted" and deactivate the whole
        # course. With nothing observed there is nothing to reconcile against.
        logger.warning(
            "import_reconcile_skipped_empty_live_list",
            course_id=str(course_id),
            root_group_path=root_path,
        )
        return 0, 0

    project_stmt = (
        select(GitLabProject)
        .join(Team, Team.id == GitLabProject.team_id)
        .where(
            Team.course_id == course_id,
            GitLabProject.is_active.is_(True),
            or_(
                GitLabProject.gitlab_project_path == root_path,
                GitLabProject.gitlab_project_path.like(f"{root_path}/%"),
            ),
        )
    )
    project_stmt = project_stmt.where(
        GitLabProject.gitlab_project_id.notin_(live_gitlab_project_ids)
    )

    stale_projects = list((await db.execute(project_stmt)).scalars().all())
    if not stale_projects:
        return 0, 0

    now = datetime.now(UTC)
    affected_team_ids = {project.team_id for project in stale_projects}
    for project in stale_projects:
        logger.info(
            "import_deactivate_missing_project",
            project_id=str(project.id),
            gitlab_project_id=project.gitlab_project_id,
            path=project.gitlab_project_path,
            course_id=str(course_id),
            root_group_path=root_path,
        )
        project.is_active = False
        project.last_synced_at = now

    orphaned_members = 0
    for team_id in affected_team_ids:
        active_projects = await db.scalar(
            select(func.count())
            .select_from(GitLabProject)
            .where(
                GitLabProject.team_id == team_id,
                GitLabProject.is_active.is_(True),
            )
        )
        if active_projects and active_projects > 0:
            continue

        members_stmt = (
            select(TeamMember)
            .options(selectinload(TeamMember.student))
            .where(
                TeamMember.team_id == team_id,
                TeamMember.is_active.is_(True),
            )
        )
        members = list((await db.execute(members_stmt)).scalars().all())
        for member in members:
            if (
                member.student
                and member.student.gitlab_user_id
                and member.student.gitlab_user_id < 0
            ):
                continue
            member.is_active = False
            member.left_at = now
            member.last_synced_at = now
            db.add(
                MembershipChange(
                    team_id=team_id,
                    student_id=member.student_id,
                    gitlab_username=member.student.gitlab_username if member.student else None,
                    change_type="left",
                    old_role=member.gitlab_access_role,
                    old_access_level=member.gitlab_access_level,
                    source="import",
                    detected_at=now,
                    details=(
                        "GitLab project missing from group import - "
                        "team has no active projects remaining"
                    ),
                )
            )
            orphaned_members += 1

    await db.flush()
    return len(stale_projects), orphaned_members


async def _transfer_memberships_on_reassign(
    db: AsyncSession,
    old_team_id: uuid.UUID,
    new_team_id: uuid.UUID,
) -> None:
    """Copy active student memberships from old_team to new_team when a project moves.

    Only copies memberships that don't already exist on the target team.
    Does NOT delete old memberships -- old team might still have other projects.
    """
    # Find active members of old team that are NOT already in new team
    existing_in_new = select(TeamMember.student_id).where(TeamMember.team_id == new_team_id)
    old_members_stmt = select(TeamMember).where(
        TeamMember.team_id == old_team_id,
        TeamMember.is_active.is_(True),
        TeamMember.student_id.notin_(existing_in_new),
    )
    old_members_result = await db.execute(old_members_stmt)
    members_to_copy = old_members_result.scalars().all()

    for m in members_to_copy:
        new_member = TeamMember(
            team_id=new_team_id,
            student_id=m.student_id,
            gitlab_access_level=m.gitlab_access_level,
            gitlab_access_role=m.gitlab_access_role,
            is_teacher=m.is_teacher,
            is_mentor=m.is_mentor,
            excluded_from_scoring=m.excluded_from_scoring,
            membership_source=m.membership_source,
        )
        db.add(new_member)

    if members_to_copy:
        await db.flush()
        logger.info(
            "import_memberships_transferred",
            old_team_id=str(old_team_id),
            new_team_id=str(new_team_id),
            count=len(members_to_copy),
        )


async def _upsert_user_role(
    db: AsyncSession,
    *,
    username: str,
    email: str | None,
    full_name: str | None = None,
    role: str,
    gitlab_user_id: int | None = None,
) -> None:
    """Upsert RBAC user role based on imported GitLab structure.

    This keeps explicit/admin roles intact and only upgrades when new role has higher priority.
    """
    normalized_username = _normalize_nonempty(username)
    stmt = (
        select(User)
        .where(
            or_(
                User.gitlab_username == normalized_username,
                User.username == normalized_username,
            )
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        db.add(
            User(
                username=normalized_username,
                gitlab_username=normalized_username,
                email=email,
                full_name=full_name,
                password_hash=f"gitlab-import:{secrets.token_hex(32)}",
                role=role,
                is_active=True,
                gitlab_user_id=gitlab_user_id,
                is_bot=is_bot_user(normalized_username, email=email),
            )
        )
        await db.flush()
        return

    email_usable = email and email != "PRIVATE"
    if email_usable and (not existing_user.email or existing_user.email == "PRIVATE"):
        existing_user.email = email
    if full_name and not existing_user.full_name:
        existing_user.full_name = full_name
    if not existing_user.gitlab_username:
        existing_user.gitlab_username = normalized_username
    if gitlab_user_id and not existing_user.gitlab_user_id:
        existing_user.gitlab_user_id = gitlab_user_id
    existing_user.is_active = True

    if _role_priority(role) > _role_priority(existing_user.role) and not existing_user.role_locked:
        existing_user.role = role
    await db.flush()


def _role_priority(role: str) -> int:
    priorities = {"student": 0, "teacher": 2, "admin": 3}
    return priorities.get(role, 0)


def _is_teacher_access_level(access_level: int) -> bool:
    return access_level >= _TEACHER_ACCESS_LEVEL


def _is_teacher_member(
    *,
    username: str,
    discovered_teachers: set[str],
    access_level: int = 0,
    is_group_member: bool = False,
    root_group_usernames: set[str] | None = None,
) -> bool:
    """Multi-layer teacher detection during team/project member import.

    Detection layers (evaluated in priority order):

    Layer 1 - **Explicit**:
        Username is in the ``discovered_teachers`` set, built from:
        (a) root-group members with ``access_level >= 40`` (Maintainer / Owner),
        (b) ``teacher_usernames`` parameter supplied during import (legacy name),
        (c) existing ``CourseMembership`` records with ``role='teacher'`` from prior imports,
        (d) ``params.teacher_usernames`` supplied during import (legacy name).

    Layer 2 - **Structural cross-reference** (root-group members):
        Username belongs to the *root* group (any access level) AND has
        ``access_level >= 40`` in the subgroup / project being scanned.
        For group members: Maintainer (40) is sufficient.
        For project members: Owner (50) is required (Maintainer in a
        single project is too common for students).
        Students who have high access but are **not** members of the
        root group are correctly excluded.

    Layer 3 - **Default**:
        High access in a subgroup / project alone is **not** sufficient.
        Students frequently receive Maintainer / Owner access in their
        own team subgroup (e.g. because they created the repository or
        were appointed project leads).  Without root-group membership
        as a corroborating signal, these users remain students.
    """
    # Layer 1: Explicitly known teacher
    if username in discovered_teachers:
        return True

    # Layer 2: Root-group member + Owner access in a *subgroup*.
    # Maintainer (40) is too common for students who are promoted to
    # Maintainer in their own team subgroup, so require Owner (50).
    return (
        root_group_usernames is not None
        and username in root_group_usernames
        and is_group_member
        and access_level >= 50
    )


def gitlab_access_role_name(access_level: int) -> str:
    """Map GitLab numeric access level to a normalized role name."""
    if access_level >= 50:
        return "owner"
    if access_level >= 40:
        return "maintainer"
    if access_level >= 30:
        return "developer"
    if access_level >= 20:
        return "reporter"
    if access_level >= 10:
        return "guest"
    if access_level > 0:
        return "minimal_access"
    return "unknown"


def _derive_team_name(group_record: dict[str, Any]) -> str:
    explicit_name = _normalize_optional(group_record.get("name"))
    full_path = _normalize_optional(group_record.get("full_path"))
    leaf = full_path.rsplit("/", maxsplit=1)[-1] if full_path else None
    return explicit_name or leaf or f"team-{group_record.get('id', 'unknown')}"


async def _sync_course_memberships_from_teachers(
    db: AsyncSession,
    course_id: uuid.UUID,
    discovered_teachers: set[str],
) -> None:
    """Create CourseMembership rows for discovered teachers.

    Only adds new memberships - never removes existing ones (to preserve
    manually-assigned roles from the teacher management page).
    Existing membership roles are not overwritten.
    """
    from app.models.course_membership import CourseMembership

    for username in discovered_teachers:
        if not username:
            continue
        normalized = _normalize_nonempty(username)
        # Find the user by gitlab_username or username
        user_stmt = (
            select(User.id)
            .where(
                or_(
                    User.gitlab_username == normalized,
                    User.username == normalized,
                )
            )
            .limit(1)
        )
        user_row = (await db.execute(user_stmt)).first()
        if not user_row:
            continue

        # Only create if no membership exists (preserve manually-set roles)
        existing_stmt = select(CourseMembership.id).where(
            CourseMembership.user_id == user_row[0],
            CourseMembership.course_id == course_id,
        )
        if (await db.execute(existing_stmt)).first():
            continue

        db.add(
            CourseMembership(
                user_id=user_row[0],
                course_id=course_id,
                role="teacher",
            )
        )
    await db.flush()


def _project_namespace_path(project: dict[str, Any]) -> str | None:
    namespace = project.get("namespace")
    if isinstance(namespace, dict):
        full_path = _normalize_optional(namespace.get("full_path"))
        if full_path:
            return full_path

    path_with_namespace = _normalize_optional(project.get("path_with_namespace"))
    if not path_with_namespace or "/" not in path_with_namespace:
        return None
    return path_with_namespace.rsplit("/", maxsplit=1)[0]

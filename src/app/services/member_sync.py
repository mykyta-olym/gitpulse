"""Membership sync service - detect membership changes between GitLab and GitPulse.

Handles all import scenarios:
- Group -> subgroup -> project hierarchy (inherited members)
- One-team-per-project mode (direct project members)
- Membership additions, removals, role changes, reactivations
- Audit trail via membership_changes table
"""

import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.compliance.roles import access_role_name as _access_role_name
from app.models.membership_change import MembershipChange
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.services.gitlab_import.persistence import _upsert_user_role
from app.services.member_sync_types import MemberSyncResult, _GitLabMemberInfo

if TYPE_CHECKING:
    from app.services.gitlab.client import GitLabClient

logger = logging.getLogger(__name__)


async def _load_teacher_usernames(db: AsyncSession, course_id: UUID) -> set[str]:
    """Load the set of usernames that are teachers for this course.

    Checks CourseMembership (staff roles), global teacher/admin roles,
    and env-configured usernames.  A person who is a teacher in
    Course A must not be automatically treated as an teacher in
    Course B where they may be a regular student.

    Returns lowercased usernames for case-insensitive comparison.
    """
    from app.models.course_membership import CourseMembership
    from app.models.user import User

    teacher_set: set[str] = set()

    # 1. CourseMembership (source of truth)
    cm_stmt = (
        select(User.gitlab_username, User.username)
        .join(CourseMembership, CourseMembership.user_id == User.id)
        .where(
            CourseMembership.course_id == course_id,
            CourseMembership.role.in_(("owner", "teacher")),
        )
    )
    cm_result = await db.execute(cm_stmt)
    for row in cm_result:
        name = row.gitlab_username or row.username
        if name and name.strip():
            teacher_set.add(name.strip().lower())

    # 3. Global teacher/admin role from User table (includes env-based
    #    GITLAB_TEACHER_USERNAMES / GITLAB_ADMIN_USERNAMES synced on login)
    role_stmt = select(User.gitlab_username).where(
        User.role.in_(("teacher", "admin")),
        User.gitlab_username.isnot(None),
        User.is_bot.is_(False),
    )
    role_result = await db.execute(role_stmt)
    for (glu,) in role_result.all():
        if glu and glu.strip():
            teacher_set.add(glu.strip().lower())

    # 4. Env-configured teacher/admin usernames (works even on fresh DB
    #    before any User records exist from OAuth login)
    from app.config import get_settings

    settings = get_settings()
    for u in settings.gitlab_teacher_usernames or []:
        if u and u.strip():
            teacher_set.add(u.strip().lower())
    for u in settings.gitlab_admin_usernames or []:
        if u and u.strip():
            teacher_set.add(u.strip().lower())

    # 5. Remove users explicitly demoted by admin (role_locked + student).
    #    When an admin demotes a teacher/admin to student via the admin panel,
    #    role_locked is set to True.  These users must NOT be treated as
    #    teachers even if they appear in env config or CourseMembership.
    locked_student_stmt = select(User.gitlab_username).where(
        User.role_locked.is_(True),
        User.role == "student",
        User.gitlab_username.isnot(None),
    )
    locked_result = await db.execute(locked_student_stmt)
    for (glu,) in locked_result.all():
        if glu and glu.strip():
            teacher_set.discard(glu.strip().lower())

    return teacher_set


def _parse_gitlab_member(raw: dict[str, Any], source: str = "direct") -> _GitLabMemberInfo | None:
    """Parse a raw GitLab member dict into a structured object."""
    from app.services.gitlab_import.service import is_bot_user

    user_id = raw.get("id")
    if not user_id or not isinstance(user_id, int) or user_id <= 0:
        return None
    username = (raw.get("username") or "").strip().lower()
    if not username:
        return None
    access_level = raw.get("access_level", 0)
    if not isinstance(access_level, int) or access_level <= 0:
        return None

    # Skip bots / service accounts
    if is_bot_user(username, user_type=raw.get("user_type")):
        logger.info("sync_skip_bot username=%s", username)
        return None

    # Skip blocked/deactivated users - they cannot contribute
    user_state = (raw.get("state") or "active").lower()
    if user_state in ("blocked", "deactivated", "banned"):
        logger.info("sync_skip_blocked username=%s state=%s", username, user_state)
        return None

    return _GitLabMemberInfo(
        gitlab_user_id=user_id,
        username=username,
        full_name=(raw.get("name") or "").strip() or None,
        email=(raw.get("email") or "").strip() or None,
        access_level=access_level,
        access_role=_access_role_name(access_level),
        source=source,
    )


def _extract_mentor_name_tokens(team_name: str) -> set[str]:
    """Extract lowercased name tokens from the parenthetical in a team name.

    Examples:
      "Apl 7 (Maťaš - Antypenko)"  -> {'maťaš', 'antypenko'}
      "Team A (Smith, Jones)"       -> {'smith', 'jones'}
      "No Mentors"                 -> set()
    """
    match = re.search(r"\(([^)]+)\)", team_name)
    if not match:
        return set()
    raw = match.group(1)
    # Split on common separators used between names: hyphen, comma, slash
    parts = re.split(r"[-,/]", raw)
    return {p.strip().lower() for p in parts if p.strip()}


def _is_staff_email(email: str | None) -> bool:
    """tuke.sk (but NOT student.tuke.sk) -> teacher / staff.

    Single source of truth for the institutional email → role rule, shared by
    both membership-sync entry points. A drift between two copies here would
    silently misclassify teachers as students (or vice versa) and skew the
    scored cohort, so it lives module-level, not as a per-function closure.
    """
    if not email:
        return False
    return email.endswith("@university.edu") or (
        email.endswith(".tuke.sk")
        and not email.endswith(".student.tuke.sk")
        and not email.endswith("@student.university.edu")
    )


async def _upsert_student(
    db: AsyncSession,
    member: _GitLabMemberInfo,
) -> Student:
    """Find or create a Student record for this GitLab member.

    Uses SELECT ... FOR UPDATE to prevent concurrent sync processes
    from creating duplicate Student records for the same GitLab user.
    """
    stmt = (
        select(Student)
        .where(Student.gitlab_user_id == member.gitlab_user_id)
        .with_for_update(skip_locked=False)
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if student is None:
        # Try by username
        stmt2 = (
            select(Student)
            .where(Student.gitlab_username == member.username)
            .with_for_update(skip_locked=False)
        )
        result2 = await db.execute(stmt2)
        student = result2.scalar_one_or_none()

    if student is None:
        student = Student(
            gitlab_user_id=member.gitlab_user_id,
            gitlab_username=member.username,
            full_name=member.full_name,
            email=member.email or "PRIVATE",
        )
        db.add(student)
        await db.flush()
        return student

    # Update if needed
    changed = False
    if student.gitlab_user_id != member.gitlab_user_id and member.gitlab_user_id > 0:
        student.gitlab_user_id = member.gitlab_user_id
        changed = True
    if member.full_name and not student.full_name:
        student.full_name = member.full_name
        changed = True
    email_usable = member.email and member.email != "PRIVATE"
    if email_usable and (not student.email or student.email == "PRIVATE"):
        student.email = member.email
        changed = True
    if changed:
        await db.flush()
    return student


async def _record_change(
    db: AsyncSession,
    *,
    team_id: UUID,
    student_id: UUID,
    gitlab_username: str | None,
    change_type: str,
    old_role: str | None = None,
    new_role: str | None = None,
    old_access_level: int | None = None,
    new_access_level: int | None = None,
    source: str = "sync",
    details: str | None = None,
) -> None:
    """Record a membership change in the audit log."""
    db.add(
        MembershipChange(
            team_id=team_id,
            student_id=student_id,
            gitlab_username=gitlab_username,
            change_type=change_type,
            old_role=old_role,
            new_role=new_role,
            old_access_level=old_access_level,
            new_access_level=new_access_level,
            source=source,
            detected_at=datetime.now(UTC),
            details=details,
        )
    )


async def _team_members_by_gitlab_id(db: AsyncSession, team: Team) -> dict[int, TeamMember]:
    """The team's memberships (inactive ones too), keyed by GitLab user id."""
    stmt = (
        select(TeamMember)
        .options(selectinload(TeamMember.student))
        .where(TeamMember.team_id == team.id)
    )
    members: dict[int, TeamMember] = {}
    for tm in (await db.execute(stmt)).scalars().all():
        if tm.student and tm.student.gitlab_user_id and tm.student.gitlab_user_id > 0:
            members[int(tm.student.gitlab_user_id)] = tm
    return members


class _Roles:
    """Who on the team is a teacher and who a peer mentor."""

    def __init__(
        self,
        teacher_usernames: set[str],
        team_name: str,
        db_members: dict[int, TeamMember],
    ) -> None:
        self.teacher_usernames = teacher_usernames
        # "Apl 7 (Maťaš - Antypenko)" -> {'maťaš', 'antypenko'}
        self.mentor_name_tokens = _extract_mentor_name_tokens(team_name or "")
        # The stored addresses, so role detection by email works even when
        # the GitLab API returns email=null.
        self.email_by_uid = {
            uid: tm.student.email.lower()
            for uid, tm in db_members.items()
            if tm.student and tm.student.email and tm.student.email not in ("PRIVATE", "")
        }

    def email(self, m: _GitLabMemberInfo) -> str | None:
        """The best available email for a member (API or DB)."""
        if m.email and m.email not in ("PRIVATE", ""):
            return m.email.lower()
        return self.email_by_uid.get(m.gitlab_user_id)

    def is_teacher(self, m: _GitLabMemberInfo) -> bool:
        """A known teacher username (CourseMembership, env config, ...), or a
        staff address: tuke.sk but NOT student.tuke.sk."""
        if m.username.lower() in self.teacher_usernames:
            return True
        return bool(_is_staff_email(self.email(m)))

    def is_mentor(self, m: _GitLabMemberInfo) -> bool:
        """A peer mentor named in the team name's parenthetical: their first or
        last name matches one of its tokens. A teacher never is one."""
        if not self.mentor_name_tokens or self.is_teacher(m) or not m.full_name:
            return False
        name_parts = {p.strip().lower() for p in m.full_name.split() if p.strip()}
        return bool(name_parts & self.mentor_name_tokens)


async def _ensure_user(db: AsyncSession, m: _GitLabMemberInfo, is_teacher: bool) -> None:
    await _upsert_user_role(
        db,
        username=m.username,
        email=m.email,
        full_name=m.full_name,
        role="teacher" if is_teacher else "student",
        gitlab_user_id=m.gitlab_user_id,
    )


def _role_change_details(old_role: Any, old_level: Any, m: _GitLabMemberInfo) -> str:
    return f"Role changed from {old_role}({old_level}) to {m.access_role}({m.access_level})"


def _publish_roster_change(
    team: Team, team_extra: dict[str, Any], course_extra: dict[str, Any]
) -> None:
    """Tell the open group and course pages that the roster changed."""
    try:
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", str(team.id), "roster_changed", extra=team_extra)
        if team.course_id:
            publish_dashboard_update(
                "course", str(team.course_id), "roster_changed", extra=course_extra
            )
    except Exception:
        logger.debug("roster_event_publish_failed", exc_info=True)


async def _fetch_team_gitlab_members(
    gl: "GitLabClient", team: Team, result: MemberSyncResult
) -> dict[int, _GitLabMemberInfo] | None:
    """The team's GitLab members - the group's (when the team is a group) and
    every project's, inherited ones included, each tagged direct or inherited,
    the highest access level kept. None when the group itself cannot be read;
    a project that cannot be read is an error on ``result``.

    One-team-per-project mode stores a project id in ``gitlab_group_id``; a
    team is group-based only when that id is not one of its projects'.
    """
    gitlab_members: dict[int, _GitLabMemberInfo] = {}
    projects = team.projects or []
    project_ids = {int(p.gitlab_project_id) for p in projects if p.gitlab_project_id is not None}
    is_group_based = team.gitlab_group_id is not None and team.gitlab_group_id not in project_ids
    try:
        if is_group_based:
            raw_members = await gl.get_group_members(
                int(team.gitlab_group_id),  # type: ignore[arg-type]
                include_inherited=True,
            )
            for raw in raw_members:
                parsed = _parse_gitlab_member(raw, source="inherited")
                if parsed:
                    gitlab_members[parsed.gitlab_user_id] = parsed
            # Direct group members, to tag the source correctly
            direct_members = await gl.get_group_members(
                int(team.gitlab_group_id),  # type: ignore[arg-type]
                include_inherited=False,
            )
            for raw in direct_members:
                parsed = _parse_gitlab_member(raw, source="direct")
                if parsed and parsed.gitlab_user_id in gitlab_members:
                    gitlab_members[parsed.gitlab_user_id].source = "direct"

        for project in projects:
            if project.gitlab_project_id is None:
                continue
            try:
                raw_members = await gl.get_project_members(
                    int(project.gitlab_project_id), include_inherited=True
                )
                for raw in raw_members:
                    parsed = _parse_gitlab_member(raw, source="inherited")
                    if parsed:
                        # Keep the highest access level if already seen
                        existing = gitlab_members.get(parsed.gitlab_user_id)
                        if existing is None or parsed.access_level > existing.access_level:
                            gitlab_members[parsed.gitlab_user_id] = parsed
                direct_proj_members = await gl.get_project_members(
                    int(project.gitlab_project_id), include_inherited=False
                )
                for raw in direct_proj_members:
                    parsed_direct = _parse_gitlab_member(raw, source="direct")
                    if parsed_direct and parsed_direct.gitlab_user_id in gitlab_members:
                        gitlab_members[parsed_direct.gitlab_user_id].source = "direct"
            except Exception:
                logger.warning(
                    "Failed to fetch members for project %s",
                    project.gitlab_project_id,
                    exc_info=True,
                )
                result.errors.append(
                    f"Failed to fetch members for project {project.gitlab_project_id}"
                )
    except Exception:
        logger.error(
            "Failed to fetch GitLab members for team %s",
            team.name,
            exc_info=True,
        )
        result.errors.append(f"Failed to fetch GitLab members for team {team.name}")
        return None
    return gitlab_members


async def sync_team_members(
    db: AsyncSession,
    gl: "GitLabClient",
    team: Team,
    *,
    source: str = "sync",
) -> MemberSyncResult:
    """Synchronize team membership from GitLab.

    Fetches current members from GitLab (project + inherited), compares with
    DB records, and applies additions / removals / role changes.

    Works for both modes:
    - Standard (subgroup-based): team.gitlab_group_id is a group -> fetch group members
    - One-team-per-project: team.gitlab_group_id is a project -> fetch project members

    In both cases, we use include_inherited=True to capture the full hierarchy.
    """
    result = MemberSyncResult(team_id=team.id, team_name=team.name)
    sync = _TeamMemberSync(db, team, result, source, datetime.now(UTC))
    teacher_usernames = await _load_teacher_usernames(db, team.course_id)
    gitlab_members = await _fetch_team_gitlab_members(gl, team, result)
    if gitlab_members is None:
        return result
    db_members = await _team_members_by_gitlab_id(db, team)
    sync.roles = _Roles(teacher_usernames, team.name or "", db_members)

    gitlab_ids = set(gitlab_members)
    db_active_ids = {uid for uid, tm in db_members.items() if tm.is_active}
    db_inactive_ids = {uid for uid, tm in db_members.items() if not tm.is_active}

    for uid in gitlab_ids - set(db_members):
        await sync.add(gitlab_members[uid])
    for uid in gitlab_ids & db_inactive_ids:
        await sync.reactivate(gitlab_members[uid], db_members[uid])
    # Guard against wiping the roster on an incomplete read. ANY fetch error
    # means our view of GitLab membership is partial: a per-project fetch that
    # raised leaves only the group members in ``gitlab_members``, so a member
    # who is *only* a direct member of that failed project would be absent from
    # ``gitlab_ids`` and wrongly removed. We cannot distinguish "this member
    # genuinely left" from "their project's fetch failed", so on any error we
    # skip removals entirely and let a later clean sync reconcile. Additions
    # and role changes from the data we DID get still apply - they are never
    # destructive. A clean run with zero members (and no errors) is a
    # legitimate "everyone left" and is allowed to remove. (A deleted project's
    # members endpoint returns [] without raising, so it does NOT count as an
    # error and its departed members are still reconciled away correctly.)
    if result.errors:
        logger.warning(
            "member_sync_skip_removal team=%s reason=fetch_errors errors=%d gitlab_members=%d",
            team.name,
            len(result.errors),
            len(gitlab_ids),
        )
    else:
        for uid in db_active_ids - gitlab_ids:
            await sync.remove(db_members[uid])
    for uid in db_active_ids & gitlab_ids:
        await sync.refresh(gitlab_members[uid], db_members[uid])

    team.members_synced_at = sync.now
    await db.flush()
    if (
        result.members_added
        or result.members_removed
        or result.members_reactivated
        or result.roles_changed
    ):
        _publish_roster_change(
            team,
            {"added": result.members_added, "removed": result.members_removed},
            {"team_id": str(team.id)},
        )
    logger.info(
        "member_sync_complete team=%s added=%d removed=%d"
        " reactivated=%d role_changes=%d unchanged=%d errors=%d",
        team.name,
        result.members_added,
        result.members_removed,
        result.members_reactivated,
        result.roles_changed,
        result.members_unchanged,
        len(result.errors),
    )
    return result


class _TeamMemberSync:
    """The four changes a team sync makes to a roster, one member at a time."""

    roles: _Roles

    def __init__(
        self,
        db: AsyncSession,
        team: Team,
        result: MemberSyncResult,
        source: str,
        now: datetime,
    ) -> None:
        self.db = db
        self.team = team
        self.result = result
        self.source = source
        self.now = now

    async def add(self, gl_member: _GitLabMemberInfo) -> None:
        """In GitLab, not in the database at all: a new membership."""
        try:
            student = await _upsert_student(self.db, gl_member)
            is_instr = self.roles.is_teacher(gl_member)
            await _ensure_user(self.db, gl_member, is_instr)
            self.db.add(
                TeamMember(
                    team_id=self.team.id,
                    student_id=student.id,
                    gitlab_access_level=gl_member.access_level,
                    gitlab_access_role=gl_member.access_role,
                    is_teacher=is_instr,
                    is_mentor=self.roles.is_mentor(gl_member),
                    is_active=True,
                    membership_source=gl_member.source,
                    last_synced_at=self.now,
                )
            )
            await _record_change(
                self.db,
                team_id=self.team.id,
                student_id=student.id,
                gitlab_username=gl_member.username,
                change_type="joined",
                new_role=gl_member.access_role,
                new_access_level=gl_member.access_level,
                source=self.source,
                details=f"New member detected via {gl_member.source} membership",
            )
            self.result.members_added += 1
        except Exception:
            logger.warning("Failed to add member %s", gl_member.username, exc_info=True)
            self.result.errors.append(f"Failed to add member {gl_member.username}")

    async def reactivate(self, gl_member: _GitLabMemberInfo, tm: TeamMember) -> None:
        """In GitLab again after having left."""
        await _ensure_user(self.db, gl_member, self.roles.is_teacher(gl_member))
        # The old values first, for an accurate audit trail
        old_role = tm.gitlab_access_role
        old_level = tm.gitlab_access_level
        tm.is_active = True
        tm.left_at = None
        tm.gitlab_access_level = gl_member.access_level
        tm.gitlab_access_role = gl_member.access_role
        tm.is_teacher = self.roles.is_teacher(gl_member)
        tm.is_mentor = self.roles.is_mentor(gl_member)
        tm.membership_source = gl_member.source
        tm.last_synced_at = self.now
        await _record_change(
            self.db,
            team_id=self.team.id,
            student_id=tm.student_id,
            gitlab_username=gl_member.username,
            change_type="reactivated",
            old_role=old_role,
            new_role=gl_member.access_role,
            old_access_level=old_level,
            new_access_level=gl_member.access_level,
            source=self.source,
            details="Member re-appeared in GitLab after previous removal",
        )
        self.result.members_reactivated += 1

    async def remove(self, tm: TeamMember) -> None:
        """Active in the database, gone from GitLab. A CSV placeholder (negative
        GitLab id) is never removed."""
        if tm.student and tm.student.gitlab_user_id and tm.student.gitlab_user_id < 0:
            return
        tm.is_active = False
        tm.left_at = self.now
        tm.last_synced_at = self.now
        await _record_change(
            self.db,
            team_id=self.team.id,
            student_id=tm.student_id,
            gitlab_username=tm.student.gitlab_username if tm.student else None,
            change_type="left",
            old_role=tm.gitlab_access_role,
            old_access_level=tm.gitlab_access_level,
            source=self.source,
            details="Member no longer found in GitLab project/group membership",
        )
        self.result.members_removed += 1

    async def refresh(self, gl_member: _GitLabMemberInfo, tm: TeamMember) -> None:
        """Still a member: role, source and the teacher / mentor flags follow
        GitLab, and the User record is made sure of (members imported before
        it was written on sync have none)."""
        is_instr = self.roles.is_teacher(gl_member)
        await _ensure_user(self.db, gl_member, is_instr)
        old_level = tm.gitlab_access_level
        old_role = tm.gitlab_access_role
        role_changed = False
        if tm.gitlab_access_level != gl_member.access_level:
            tm.gitlab_access_level = gl_member.access_level
            role_changed = True
        if tm.gitlab_access_role != gl_member.access_role:
            tm.gitlab_access_role = gl_member.access_role
            role_changed = True
        # e.g. inherited -> direct
        if tm.membership_source != gl_member.source:
            tm.membership_source = gl_member.source
        if tm.is_teacher != is_instr:
            tm.is_teacher = is_instr
        # The team name may change, or the member's name
        is_mntr = self.roles.is_mentor(gl_member)
        if tm.is_mentor != is_mntr:
            tm.is_mentor = is_mntr
        tm.last_synced_at = self.now
        if not role_changed:
            self.result.members_unchanged += 1
            return
        await _record_change(
            self.db,
            team_id=self.team.id,
            student_id=tm.student_id,
            gitlab_username=gl_member.username,
            change_type="role_changed",
            old_role=old_role,
            new_role=gl_member.access_role,
            old_access_level=old_level,
            new_access_level=gl_member.access_level,
            source=self.source,
            details=_role_change_details(old_role, old_level, gl_member),
        )
        self.result.roles_changed += 1


async def _fetch_project_gitlab_members(
    gl: "GitLabClient", project_gitlab_id: int
) -> dict[int, _GitLabMemberInfo]:
    """One project's members, inherited ones included; a direct membership
    wins unless an inherited one grants more."""
    gitlab_members: dict[int, _GitLabMemberInfo] = {}
    for raw in await gl.get_project_members(int(project_gitlab_id), include_inherited=True):
        parsed = _parse_gitlab_member(raw, source="inherited")
        if parsed:
            gitlab_members[parsed.gitlab_user_id] = parsed
    for raw in await gl.get_project_members(int(project_gitlab_id), include_inherited=False):
        parsed = _parse_gitlab_member(raw, source="direct")
        if not parsed:
            continue
        existing = gitlab_members.get(parsed.gitlab_user_id)
        if existing is None or parsed.access_level >= existing.access_level:
            gitlab_members[parsed.gitlab_user_id] = parsed
        else:
            existing.source = "direct"
    return gitlab_members


async def sync_project_members_into_team(
    db: AsyncSession,
    gl: "GitLabClient",
    team: Team,
    project: Any,
    *,
    source: str = "project_sync",
) -> MemberSyncResult:
    """Upsert members of one GitLab project into the owning team.

    This is intentionally non-destructive. A manual project sync has a project
    scope, so it may add/reactivate/update members proven by that project, but
    it must not remove team members who belong to other projects in the group.
    Full team/course sync remains the destructive reconciliation path.
    """
    result = MemberSyncResult(team_id=team.id, team_name=team.name)
    now = datetime.now(UTC)
    project_gitlab_id = getattr(project, "gitlab_project_id", None)
    if project_gitlab_id is None:
        result.errors.append("Project has no GitLab id")
        return result

    teacher_usernames = await _load_teacher_usernames(db, team.course_id)
    try:
        gitlab_members = await _fetch_project_gitlab_members(gl, int(project_gitlab_id))
    except Exception:
        logger.warning(
            "Failed to fetch project members for project %s",
            project_gitlab_id,
            exc_info=True,
        )
        result.errors.append(f"Failed to fetch members for project {project_gitlab_id}")
        return result
    db_members = await _team_members_by_gitlab_id(db, team)
    roles = _Roles(teacher_usernames, team.name or "", db_members)

    for uid, gl_member in gitlab_members.items():
        try:
            student = await _upsert_student(db, gl_member)
            is_instr = roles.is_teacher(gl_member)
            await _ensure_user(db, gl_member, is_instr)
            tm = db_members.get(uid) or await db.get(TeamMember, (team.id, student.id))
            if tm is None:
                tm = TeamMember(team_id=team.id, student_id=student.id)
                db.add(tm)
                db_members[uid] = tm
                _apply_project_membership(tm, gl_member, is_instr, roles, now)
                await _record_change(
                    db,
                    team_id=team.id,
                    student_id=tm.student_id,
                    gitlab_username=gl_member.username,
                    change_type="joined",
                    new_role=gl_member.access_role,
                    new_access_level=gl_member.access_level,
                    source=source,
                    details=f"New project member detected via {gl_member.source} membership",
                )
                result.members_added += 1
                continue

            old_role = tm.gitlab_access_role
            old_level = tm.gitlab_access_level
            was_active = tm.is_active
            role_changed = old_role != gl_member.access_role or old_level != gl_member.access_level
            _apply_project_membership(tm, gl_member, is_instr, roles, now)
            if not was_active:
                await _record_change(
                    db,
                    team_id=team.id,
                    student_id=tm.student_id,
                    gitlab_username=gl_member.username,
                    change_type="reactivated",
                    old_role=old_role,
                    new_role=gl_member.access_role,
                    old_access_level=old_level,
                    new_access_level=gl_member.access_level,
                    source=source,
                    details="Project member re-appeared in GitLab",
                )
                result.members_reactivated += 1
            elif role_changed:
                await _record_change(
                    db,
                    team_id=team.id,
                    student_id=tm.student_id,
                    gitlab_username=gl_member.username,
                    change_type="role_changed",
                    old_role=old_role,
                    new_role=gl_member.access_role,
                    old_access_level=old_level,
                    new_access_level=gl_member.access_level,
                    source=source,
                    details=_role_change_details(old_role, old_level, gl_member),
                )
                result.roles_changed += 1
            else:
                result.members_unchanged += 1
        except Exception:
            logger.warning("Failed to upsert project member %s", gl_member.username, exc_info=True)
            result.errors.append(f"Failed to upsert project member {gl_member.username}")

    team.members_synced_at = now
    await db.flush()
    if result.members_added or result.members_reactivated or result.roles_changed:
        project_id = str(getattr(project, "id", ""))
        _publish_roster_change(
            team,
            {
                "added": result.members_added,
                "reactivated": result.members_reactivated,
                "project_id": project_id,
            },
            {"team_id": str(team.id), "project_id": project_id},
        )
    logger.info(
        "project_member_sync_complete team=%s project=%s added=%d reactivated=%d "
        "role_changes=%d unchanged=%d errors=%d",
        team.name,
        project_gitlab_id,
        result.members_added,
        result.members_reactivated,
        result.roles_changed,
        result.members_unchanged,
        len(result.errors),
    )
    return result


def _apply_project_membership(
    tm: TeamMember,
    gl_member: _GitLabMemberInfo,
    is_teacher: bool,
    roles: _Roles,
    now: datetime,
) -> None:
    """A project-proven membership: active, with GitLab's role and source."""
    tm.is_active = True
    tm.left_at = None
    tm.gitlab_access_level = gl_member.access_level
    tm.gitlab_access_role = gl_member.access_role
    tm.is_teacher = is_teacher
    tm.is_mentor = roles.is_mentor(gl_member)
    tm.membership_source = gl_member.source
    tm.last_synced_at = now

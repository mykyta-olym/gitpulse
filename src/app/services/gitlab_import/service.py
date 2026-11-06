"""Import a GitLab group hierarchy into Course/Team/Student/Project records."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.course_settings import CourseSettings
from app.models.team import Team
from app.models.user import User
from app.services.gitlab.client import GitLabClient
from app.services.gitlab_import.email_enrichment import (
    _enrich_student_emails,
    _enrich_student_emails_arena,
    _enrich_student_emails_fast,
    _enrich_user_emails_arena,
)
from app.services.gitlab_import.helpers import (
    _detect_historical_projects,
    extract_group_path_from_input,
    is_bot_user,
    match_team_group_path,
    select_team_group_records,
)
from app.services.gitlab_import.normalize import (
    _normalize_nonempty,
    _normalize_optional,
    _to_int,
    _to_positive_int,
)
from app.services.gitlab_import.persistence import (
    _collect_subgroups,
    _deactivate_missing_projects_for_course,
    _derive_team_name,
    _get_or_create_course,
    _import_student_team_member,
    _is_teacher_access_level,
    _project_namespace_path,
    _sync_course_memberships_from_teachers,
    _upsert_project,
    _upsert_team,
    _upsert_user_role,
)

logger = structlog.get_logger(__name__)

__all__ = [
    "GitLabGroupImportParams",
    "GitLabGroupImportResult",
    "extract_group_path_from_input",
    "import_gitlab_group_to_course",
    "is_bot_user",
    "match_team_group_path",
    "select_team_group_records",
]

Member = dict[str, Any]
Emit = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(slots=True)
class GitLabGroupImportParams:
    """Parameters for one group import run."""

    group_url: str
    course_code: str
    course_name: str
    academic_year: str
    target_course_id: uuid.UUID | None = None
    semester: str = "summer"
    include_subgroups: bool = True
    teacher_usernames: list[str] | None = None
    one_team_per_project: bool = False  # Create separate team for each project
    semester_start_date: date | None = None
    semester_end_date: date | None = None


@dataclass(slots=True)
class GitLabGroupImportResult:
    """Summary of what was imported/updated."""

    course_id: uuid.UUID
    course_code: str
    course_name: str
    group_path: str
    created_course: bool
    teams_created: int
    teams_updated: int
    students_created: int
    students_updated: int
    teachers_created: int
    memberships_created: int
    projects_created: int
    projects_updated: int
    teachers_detected: list[str]
    projects_deactivated: int = 0
    warnings: list[str] | None = None
    # The period of the course the import landed in - see the API response.
    course_academic_year: str = ""
    course_semester: str = ""


@dataclass
class _Counts:
    teams_created: int = 0
    teams_updated: int = 0
    students_created: int = 0
    students_updated: int = 0
    teachers_created: int = 0
    memberships_created: int = 0
    projects_created: int = 0
    projects_updated: int = 0


def _ceil_share(total: int, tenths: int) -> int:
    return -(-(total * tenths) // 10)


@dataclass
class _Import:
    """One import run: what it has found so far, and how it reports."""

    db: AsyncSession
    client: GitLabClient
    params: GitLabGroupImportParams
    emit: Emit
    counts: _Counts = field(default_factory=_Counts)
    teachers: set[str] = field(default_factory=set)
    # Name / e-mail / GitLab id of the teachers found, for their User rows.
    teacher_info: dict[str, dict[str, str]] = field(default_factory=dict)
    # Teacher-level members of the root group (and its parents).
    root_usernames: set[str] = field(default_factory=set)
    # GitLab user ids already imported into each team.
    seen_by_team: dict[uuid.UUID, set[int]] = field(default_factory=dict)
    # Why the last project could not be imported.
    skip_reason: str = ""

    def __post_init__(self) -> None:
        # Named in the request, and configured for the installation - so they
        # are found even on a first import, before any User row exists. Admin
        # is NEVER assigned by an import; only teachers are detected.
        self.teachers = self.param_teachers() | {
            u.strip() for u in get_settings().gitlab_teacher_usernames or [] if u and u.strip()
        }

    def param_teachers(self) -> set[str]:
        return {
            username
            for raw in (self.params.teacher_usernames or [])
            if (username := _normalize_optional(raw))
        }

    def result(
        self,
        course: Course,
        created_course: bool,
        group_path: str,
        warnings: list[str] | None,
        projects_deactivated: int = 0,
    ) -> GitLabGroupImportResult:
        c = self.counts
        return GitLabGroupImportResult(
            course_id=course.id,
            course_code=course.code,
            course_academic_year=course.academic_year,
            course_semester=course.semester,
            course_name=course.name,
            group_path=group_path,
            created_course=created_course,
            teams_created=c.teams_created,
            teams_updated=c.teams_updated,
            students_created=c.students_created,
            students_updated=c.students_updated,
            teachers_created=c.teachers_created,
            memberships_created=c.memberships_created,
            projects_created=c.projects_created,
            projects_updated=c.projects_updated,
            teachers_detected=sorted(self.teachers),
            projects_deactivated=projects_deactivated,
            warnings=warnings,
        )

    async def upsert_teacher(self, member: Member, role: str = "teacher") -> None:
        await _upsert_user_role(
            self.db,
            username=_normalize_optional(member.get("username")) or "",
            email=_normalize_optional(member.get("email")) or "PRIVATE",
            full_name=_normalize_optional(member.get("name")),
            role=role,
            gitlab_user_id=_to_int(member.get("id")) or None,
        )

    # -- The course and its teachers ------------------------------------------

    async def course(self) -> tuple[Course, CourseSettings, bool]:
        p = self.params
        return await _get_or_create_course(
            db=self.db,
            target_course_id=p.target_course_id,
            code=p.course_code.strip(),
            name=p.course_name.strip(),
            academic_year=p.academic_year.strip(),
            semester=p.semester.strip(),
            semester_start_date=p.semester_start_date,
            semester_end_date=p.semester_end_date,
        )

    async def add_course_teachers(self, course_id: uuid.UUID) -> None:
        """The course's teachers from earlier imports or the admin UI - they
        may have low GitLab access - kept on a re-import."""
        rows = await self.db.execute(
            select(User.username)
            .join(CourseMembership, CourseMembership.user_id == User.id)
            .where(
                CourseMembership.course_id == course_id,
                CourseMembership.role.in_(("owner", "teacher")),
            )
        )
        self.teachers.update(u for (u,) in rows.all() if u)

    async def apply_admin_decisions(self) -> None:
        """What an admin decided wins over detection: a user locked as teacher
        is one, a user locked as student is not, and an admin is no course's
        teacher (their access comes from the admin role).

        Only LOCKED teachers are added: loading every teacher made one false
        positive of the frequency detection persist across re-imports and
        spread to other courses.
        """
        locked = await self.db.execute(
            select(User.username, User.gitlab_username, User.role).where(
                User.role_locked.is_(True), User.role.in_(("teacher", "student"))
            )
        )
        rows = locked.all()
        self.teachers.update(u for u, _, role in rows if role == "teacher" and u)
        for _, gitlab_username, role in rows:
            if role == "student" and gitlab_username and gitlab_username.strip():
                self.teachers.discard(gitlab_username.strip())
                self.teachers.discard(gitlab_username.strip().lower())
        for admin in get_settings().gitlab_admin_usernames or []:
            if admin and admin.strip():
                self.teachers.discard(admin.strip())
                self.teachers.discard(admin.strip().lower())

    async def emit_teachers(self) -> None:
        """Every teacher found, in the log and counters - also those who are
        only inherited members, in no subgroup or project."""
        for username in sorted(self.teachers):
            await self.emit(
                {
                    "type": "teacher",
                    "username": username,
                    "name": self.teacher_info.get(username, {}).get("name", ""),
                    "created": False,
                    "role_label": "teacher",
                }
            )

    # -- Members ---------------------------------------------------------------

    async def import_members(
        self, members: list[Member], team: Team, seen: set[int], **how: Any
    ) -> set[str]:
        """Each member into the team - as a student, or recognised as a
        teacher; the usernames of all of them."""
        for member in members:
            imported = await _import_student_team_member(
                self.db,
                member=member,
                team=team,
                discovered_teachers=self.teachers,
                seen_gitlab_user_ids=seen,
                **how,
            )
            if imported is None:
                continue
            created, created_membership, role_label = imported
            is_teacher = role_label in ("teacher", "owner")
            if is_teacher:
                self.counts.teachers_created += 1 if created else 0
            elif created:
                self.counts.students_created += 1
            else:
                self.counts.students_updated += 1
            self.counts.memberships_created += 1 if created_membership else 0
            await self.emit(
                {
                    "type": "teacher" if is_teacher else "student",
                    "username": _normalize_optional(member.get("username")) or "?",
                    "name": _normalize_optional(member.get("name")) or "",
                    "created": created,
                    "role_label": role_label,
                }
            )
        return {u for m in members if (u := _normalize_optional(m.get("username")))}

    async def add_inherited_users(
        self, fetch: Awaitable[list[Member]], direct: set[str], **where: Any
    ) -> None:
        """Inherited members get User rows too, so they appear in User
        Management - teachers or students by their access."""
        try:
            for member in await fetch:
                username = _normalize_optional(member.get("username"))
                if not username or username in direct:
                    continue
                if is_bot_user(username, user_type=_normalize_optional(member.get("user_type"))):
                    continue
                teacher = _is_teacher_access_level(_to_int(member.get("access_level")))
                await self.upsert_teacher(member, "teacher" if teacher else "student")
        except Exception as exc:
            logger.debug("inherited_members_fetch_failed", error=str(exc), **where)

    async def detect_by_frequency(self, member_lists: list[list[Member]], per: str) -> None:
        """Teachers from how often a user appears across the teams' subgroups
        or projects (``per``): a student has high access in one team, their
        own, so high access in at least half of them (5 at least) marks a
        teacher/TA; and a user who is a member of 90 % of them (6 at least),
        at any access, is one too - a TA added to every team as Developer
        and absent from the root group.

        A flat threshold of 3 made students who are Maintainers of their own
        subgroup false positives.
        """
        high: dict[str, int] = {}
        seen_in: dict[str, int] = {}
        info: dict[str, dict[str, str]] = {}
        for members in member_lists:
            for m in members:
                username = _normalize_optional(m.get("username"))
                if not username or is_bot_user(
                    username, user_type=_normalize_optional(m.get("user_type"))
                ):
                    continue
                seen_in[username] = seen_in.get(username, 0) + 1
                info.setdefault(
                    username,
                    {
                        "name": _normalize_optional(m.get("name")) or "",
                        "gitlab_user_id": str(_to_int(m.get("id")) or ""),
                    },
                )
                if _is_teacher_access_level(_to_int(m.get("access_level"))):
                    high[username] = high.get(username, 0) + 1
        total = len(member_lists)
        by_subgroup = per == "subgroup"
        for username, count in high.items():
            if count >= max(5, _ceil_share(total, 5)) and username not in self.teachers:
                logger.info(
                    "import_frequency_teacher_detected",
                    username=username,
                    high_access=count,
                    total=total,
                    per=per,
                )
                self.teachers.add(username)
                await self.emit(
                    {
                        "type": "teacher",
                        "username": username,
                        "name": info[username]["name"],
                        "created": False,
                        "role_label": "teacher",
                        "detection": "frequency",
                    }
                )
        for username, count in seen_in.items():
            if count >= max(6, _ceil_share(total, 9)) and username not in self.teachers:
                logger.info(
                    "import_cross_teacher_detected",
                    username=username,
                    present_in=count,
                    total=total,
                    per=per,
                )
                self.teachers.add(username)
                uid = info[username]["gitlab_user_id"]
                await _upsert_user_role(
                    self.db,
                    username=username,
                    email="PRIVATE",
                    full_name=info[username]["name"] or None,
                    role="teacher",
                    gitlab_user_id=int(uid) if by_subgroup and uid else None,
                )
                await self.emit(
                    {
                        "type": "teacher",
                        "username": username,
                        "name": info[username]["name"],
                        "created": False,
                        "role_label": "teacher",
                        "detection": f"cross_{per}",
                    }
                )
        if by_subgroup:
            # Their name and id, for the final all-teacher upsert.
            for username, i in info.items():
                if username in self.teachers and username not in self.teacher_info:
                    self.teacher_info[username] = i

    async def enrich_emails(self) -> None:
        await self.emit({"type": "stage", "message": "Matching emails from user records..."})
        await _enrich_student_emails_fast(self.db)
        await self.emit({"type": "stage", "message": "Enriching emails from Arena API..."})
        await _enrich_student_emails_arena(self.db)
        await _enrich_user_emails_arena(self.db)
        await self.emit({"type": "stage", "message": "Enriching missing emails from GitLab API..."})
        await _enrich_student_emails(self.db, self.client, on_progress=self.emit)

    async def upsert_team(self, **team: Any) -> Team:
        row, created = await _upsert_team(db=self.db, **team)
        if created:
            self.counts.teams_created += 1
        else:
            self.counts.teams_updated += 1
        await self.emit({"type": "team", "name": team["name"], "created": created})
        return row

    async def upsert_project(self, team: Team, project: Member, shown_name: str) -> bool:
        """The project under the team. False when it cannot be (it belongs to
        another course) - a warning, not a failure."""
        try:
            _, created = await _upsert_project(self.db, team.id, project)
        except ValueError as exc:
            await self.emit({"type": "warning", "message": str(exc)})
            logger.warning("import_project_skipped", reason=str(exc))
            self.skip_reason = str(exc)
            return False
        if created:
            self.counts.projects_created += 1
        else:
            self.counts.projects_updated += 1
        await self.emit({"type": "project", "name": shown_name, "created": created})
        return True


# -- A single project ---------------------------------------------------------


async def _import_single_project(
    run: _Import, project: Member, group_path: str
) -> GitLabGroupImportResult:
    """The URL named one project: that project only, as a one-team course -
    its parent group's high-access members are its teachers."""
    client, db = run.client, run.db
    project_path = _normalize_nonempty(project.get("path_with_namespace"), fallback=group_path)
    project_name = (
        _normalize_optional(project.get("name"))
        or _normalize_optional(project.get("path"))
        or group_path.rsplit("/", 1)[-1]
    )
    project_id = _to_positive_int(project.get("id"), "GitLab project id")
    await run.emit({"type": "stage", "message": f"Importing single project: {project_path}"})

    namespace = project.get("namespace") or {}
    namespace_id = _to_int(namespace.get("id"))
    if _normalize_optional(namespace.get("kind")) == "group" and namespace_id > 0:
        parent = await client.get_group(namespace_id)
        parent_id = _to_int((parent or {}).get("id"))
        if parent_id > 0:
            try:
                for m in await client.get_group_members(parent_id, include_inherited=True):
                    username = _normalize_optional(m.get("username"))
                    if (
                        username
                        and _is_teacher_access_level(_to_int(m.get("access_level")))
                        and not is_bot_user(
                            username, user_type=_normalize_optional(m.get("user_type"))
                        )
                    ):
                        run.teachers.add(username)
                        run.teacher_info[username] = {
                            "name": _normalize_optional(m.get("name")) or ""
                        }
                        await run.upsert_teacher(m)
            except Exception:
                logger.debug("parent_group_members_fetch_failed", exc_info=True)
    for m in await client.get_project_members(project_id, include_inherited=True):
        if _normalize_optional(m.get("username")) in run.teachers:
            await run.upsert_teacher(m)

    course, course_settings, created_course = await run.course()
    course_settings.gitlab_group_path = project_path
    await run.add_course_teachers(course.id)
    await run.apply_admin_decisions()
    # Every teacher needs a User row with the teacher role, which the
    # CourseMembership rows reference.
    for username in run.teachers:
        if username:
            info = run.teacher_info.get(username, {})
            await _upsert_user_role(
                db,
                username=username,
                email=info.get("email") or "PRIVATE",
                full_name=info.get("name") or None,
                role="teacher",
            )
    await db.flush()
    await _sync_course_memberships_from_teachers(db, course.id, run.teachers)
    await db.flush()
    await run.emit(
        {"type": "course", "name": course.name, "code": course.code, "created": created_course}
    )
    await run.emit_teachers()

    team = await run.upsert_team(
        course_id=course.id,
        name=project_name,
        gitlab_group_id=project_id,
        gitlab_group_path=project_path,
    )
    if not await run.upsert_project(team, project, project_path):
        return run.result(course, created_course, project_path, [run.skip_reason])

    direct = await run.import_members(
        await client.get_project_members(project_id, include_inherited=False), team, set()
    )
    await run.add_inherited_users(
        client.get_project_members(project_id, include_inherited=True),
        direct,
        project_id=project_id,
    )
    await run.enrich_emails()
    warnings = _detect_historical_projects(
        [project], course_settings.semester_start_date if course_settings else None
    )
    return run.result(course, created_course, project_path, warnings or None)


# -- A group ------------------------------------------------------------------


async def _root_teachers(run: _Import, root_id: int) -> None:
    """Teachers from the root group: its direct and inherited (parent-group)
    Owners/Maintainers. `members/all` at the root adds members of PARENT
    groups, not of the subgroups, so an inherited high-access user there is a
    teacher, not a student - students live in the subgroups."""
    client = run.client
    root_all = await client.get_group_members(root_id, include_inherited=True)
    root_direct = await client.get_group_members(root_id, include_inherited=False)

    def teacher_level(m: Member) -> str | None:
        username = _normalize_optional(m.get("username"))
        if (
            username
            and _is_teacher_access_level(_to_int(m.get("access_level")))
            and not is_bot_user(username, user_type=_normalize_optional(m.get("user_type")))
        ):
            return username
        return None

    run.root_usernames = {u for m in [*root_direct, *root_all] if (u := teacher_level(m))}
    admins = {
        u.strip().lower() for u in get_settings().gitlab_admin_usernames or [] if u and u.strip()
    }

    def note(username: str, m: Member) -> dict[str, str]:
        return {
            "name": _normalize_optional(m.get("name")) or "",
            "email": _normalize_optional(m.get("email")) or "PRIVATE",
            "gitlab_user_id": str(_to_int(m.get("id")) or ""),
        }

    for m in root_all:
        username = _normalize_optional(m.get("username"))
        if not username or is_bot_user(username, user_type=_normalize_optional(m.get("user_type"))):
            continue
        if _is_teacher_access_level(_to_int(m.get("access_level"))):
            if username.lower() not in admins:
                run.teachers.add(username)
            run.teacher_info[username] = note(username, m)
            await run.upsert_teacher(m)
        else:
            # Reporters/Developers inherited here get a User row, so they
            # appear in User Management.
            await run.upsert_teacher(m, "student")

    # Nobody found beyond the named ones: the root's own Maintainers and
    # Owners are the teachers - not every direct member, who may be students
    # in a flat course.
    named = run.param_teachers()
    if not (run.teachers - named):
        for m in root_direct:
            username = teacher_level(m)
            if not username:
                continue
            if username.lower() not in admins:
                run.teachers.add(username)
            run.teacher_info.setdefault(username, note(username, m))
            await run.upsert_teacher(m)
        logger.info(
            "import_direct_root_fallback",
            found=len(run.teachers - named),
            usernames=sorted(run.teachers - named),
        )


async def _import_subgroup_members(
    run: _Import, team_records: list[Member], team_by_path: dict[str, Team]
) -> None:
    """Each team's members from its subgroup's DIRECT membership - inherited
    membership would bring every other team's noise."""
    client = run.client
    cache: dict[int, list[Member]] = {}
    if len(team_records) >= 2:
        for record in team_records:
            gid = _to_positive_int(record.get("id"), "GitLab subgroup id")
            cache[gid] = await client.get_group_members(gid, include_inherited=False)
        await run.detect_by_frequency(list(cache.values()), "subgroup")
    for record in team_records:
        gid = _to_positive_int(record.get("id"), "GitLab subgroup id")
        full_path = _normalize_optional(record.get("full_path")) or str(record.get("id", "unknown"))
        team = team_by_path.get(full_path)
        if team is None:
            continue
        members = (
            cache[gid]
            if gid in cache
            else await client.get_group_members(gid, include_inherited=False)
        )
        direct = await run.import_members(
            members,
            team,
            run.seen_by_team.setdefault(team.id, set()),
            is_group_member=True,
            root_group_usernames=run.root_usernames,
        )
        await run.add_inherited_users(
            client.get_group_members(gid, include_inherited=True), direct, group_id=gid
        )


async def _import_one_team_per_project(
    run: _Import, course: Course, projects: list[Member]
) -> tuple[list[Member], set[int]]:
    """A root group holding only projects: a team per project. Returns the
    projects imported and their GitLab ids."""
    imported: list[Member] = []
    teams: dict[int, Team] = {}
    for project in projects:
        name = _normalize_optional(project.get("name")) or _normalize_optional(project.get("path"))
        project_id = _to_int(project.get("id"))
        if not name or project_id <= 0:
            continue
        path = _normalize_optional(project.get("path_with_namespace")) or ""
        # The project's id stands in for the team's group id.
        team = await run.upsert_team(
            course_id=course.id, name=name, gitlab_group_id=project_id, gitlab_group_path=path
        )
        if not await run.upsert_project(
            team, project, _normalize_optional(project.get("path_with_namespace")) or name
        ):
            continue
        imported.append(project)
        teams[project_id] = team

    # The members, ten projects at a time.
    members: dict[int, list[Member]] = {}
    ids = list(teams)
    for i in range(0, len(ids), 10):
        batch = ids[i : i + 10]
        results = await asyncio.gather(
            *[run.client.get_project_members(pid, include_inherited=False) for pid in batch],
            return_exceptions=True,
        )
        for pid, result in zip(batch, results, strict=False):
            if isinstance(result, BaseException):
                logger.warning("Failed to fetch members for project %s: %s", pid, result)
                members[pid] = []
            else:
                members[pid] = result
    if len(members) >= 2:
        await run.detect_by_frequency(list(members.values()), "project")
    for project_id, team in teams.items():
        direct = await run.import_members(
            members.get(project_id, []), team, set(), root_group_usernames=run.root_usernames
        )
        await run.add_inherited_users(
            run.client.get_project_members(project_id, include_inherited=True),
            direct,
            project_id=project_id,
        )
    return imported, set(teams)


async def _import_projects_into_teams(
    run: _Import,
    projects: list[Member],
    team_records: list[Member],
    team_by_path: dict[str, Team],
    root_group_path: str,
) -> tuple[list[Member], set[int]]:
    """Each project into the team whose group holds it, then its members.
    Returns the projects imported and their GitLab ids."""
    imported: list[Member] = []
    observed: set[int] = set()
    members: list[tuple[Team, list[Member]]] = []
    team_paths = list(team_by_path)
    for project in projects:
        namespace = _project_namespace_path(project)
        if namespace is None:
            continue
        matched = match_team_group_path(namespace, team_paths)
        if matched is None and len(team_records) == 1:
            matched = root_group_path
        team = team_by_path.get(matched) if matched is not None else None
        if team is None:
            continue
        if not await run.upsert_project(
            team, project, _normalize_optional(project.get("path_with_namespace")) or "?"
        ):
            continue
        imported.append(project)
        project_id = _to_int(project.get("id"))
        if project_id <= 0:
            continue
        observed.add(project_id)
        members.append(
            (team, await run.client.get_project_members(project_id, include_inherited=False))
        )
    if len(members) >= 2:
        await run.detect_by_frequency([ms for _, ms in members], "project")
    for team, team_members in members:
        await run.import_members(
            team_members,
            team,
            run.seen_by_team.setdefault(team.id, set()),
            root_group_usernames=run.root_usernames,
        )
    return imported, observed


async def _import_group(
    run: _Import, root_group: Member, group_path: str
) -> GitLabGroupImportResult:
    client, db, params = run.client, run.db, run.params
    root_id = _to_positive_int(root_group.get("id"), "GitLab group id")
    root_path = _normalize_nonempty(root_group.get("full_path"), fallback=group_path)
    await run.emit({"type": "stage", "message": f"Connected - group: {root_path}"})
    await _root_teachers(run, root_id)

    course, course_settings, created_course = await run.course()
    course_settings.gitlab_group_path = root_path
    await run.add_course_teachers(course.id)
    await run.apply_admin_decisions()
    await db.flush()
    await run.emit(
        {"type": "course", "name": course.name, "code": course.code, "created": created_course}
    )
    logger.info(
        "import_discovered_teachers", count=len(run.teachers), usernames=sorted(run.teachers)
    )
    await run.emit_teachers()

    groups = [root_group]
    if params.include_subgroups:
        groups.extend(await _collect_subgroups(client, root_id))
    projects = await client.get_group_projects(
        root_id, include_subgroups=params.include_subgroups, include_archived=False
    )
    await run.emit(
        {"type": "stage", "message": f"Found {len(groups)} group(s), {len(projects)} project(s)"}
    )
    # Subgroups make the teams; a root group holding only projects makes a
    # team of each project.
    one_team_per_project = params.one_team_per_project or (len(groups) <= 1 and bool(projects))
    logger.info(
        "gitlab_import_auto_detect",
        group_path=root_path,
        has_subgroups=len(groups) > 1,
        has_projects=bool(projects),
        use_one_team_per_project=one_team_per_project,
    )

    team_records = select_team_group_records(
        groups,
        root_group_id=root_id,
        project_namespace_paths={
            ns for project in projects if (ns := _project_namespace_path(project))
        },
    )
    team_by_path: dict[str, Team] = {}
    for record in team_records:
        full_path = _normalize_optional(record.get("full_path")) or str(record.get("id", "unknown"))
        team_by_path[full_path] = await run.upsert_team(
            course_id=course.id,
            name=_derive_team_name(record),
            gitlab_group_id=_to_positive_int(record.get("id"), "GitLab subgroup id"),
            gitlab_group_path=full_path,
        )
    await _import_subgroup_members(run, team_records, team_by_path)
    # The final membership sync comes after the projects' members, which can
    # name more teachers.
    await run.add_course_teachers(course.id)
    await db.flush()

    if one_team_per_project:
        imported, observed = await _import_one_team_per_project(run, course, projects)
    else:
        imported, observed = await _import_projects_into_teams(
            run, projects, team_records, team_by_path, root_path
        )
    await run.enrich_emails()

    await run.apply_admin_decisions()
    # Every teacher gets a User row with the teacher role, which their
    # CourseMembership references: several detections only add the name.
    # _upsert_user_role never downgrades (teacher < admin).
    for username in run.teachers:
        if username:
            info = run.teacher_info.get(username, {})
            uid = info.get("gitlab_user_id")
            await _upsert_user_role(
                db,
                username=username,
                email=info.get("email") or "PRIVATE",
                full_name=info.get("name") or None,
                role="teacher",
                gitlab_user_id=int(uid) if uid else None,
            )
    # The configured admins get User rows too, or they are missing from the
    # teachers page until they first log in.
    for admin in get_settings().gitlab_admin_usernames or []:
        if admin and admin.strip():
            info = run.teacher_info.get(admin.strip(), {})
            uid = info.get("gitlab_user_id")
            await _upsert_user_role(
                db,
                username=admin.strip(),
                email=info.get("email") or "PRIVATE",
                full_name=info.get("name") or None,
                role="admin",
                gitlab_user_id=int(uid) if uid else None,
            )
    await db.flush()
    await _sync_course_memberships_from_teachers(db, course.id, run.teachers)
    await db.flush()
    logger.info(
        "import_final_teacher_set",
        count=len(run.teachers),
        usernames=sorted(run.teachers),
        teachers_created=run.counts.teachers_created,
    )

    settings_row = (
        await db.execute(select(CourseSettings).where(CourseSettings.course_id == course.id))
    ).scalar_one_or_none()
    deactivated, members_deactivated = await _deactivate_missing_projects_for_course(
        db, course_id=course.id, root_group_path=root_path, live_gitlab_project_ids=observed
    )
    warnings = list(
        _detect_historical_projects(
            imported, settings_row.semester_start_date if settings_row else None
        )
    )
    if deactivated:
        message = f"Deactivated {deactivated} project(s) missing from GitLab."
        await run.emit({"type": "warning", "message": message})
        logger.info(
            "import_missing_projects_reconciled",
            course_id=str(course.id),
            root_group_path=root_path,
            projects_deactivated=deactivated,
            members_deactivated=members_deactivated,
        )
        warnings.append(message)
    return run.result(course, created_course, root_path, warnings or None, deactivated)


async def import_gitlab_group_to_course(
    db: AsyncSession,
    *,
    gitlab_base_url: str,
    gitlab_api_token: str,
    params: GitLabGroupImportParams,
    on_progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> GitLabGroupImportResult:
    """Import one GitLab group into a course with auto-upsert semantics."""
    if not gitlab_api_token or not gitlab_api_token.strip():
        raise ValueError("GITLAB_API_TOKEN is not configured")

    group_path = extract_group_path_from_input(params.group_url, gitlab_base_url)

    async def emit(event: dict[str, Any]) -> None:
        if on_progress is not None:
            await on_progress(event)

    await emit({"type": "stage", "message": "Connecting to GitLab API..."})
    async with GitLabClient(base_url=gitlab_base_url, private_token=gitlab_api_token) as client:
        run = _Import(db, client, params, emit)
        root_group = await client.get_group(group_path)
        if root_group is not None:
            return await _import_group(run, root_group, group_path)
        # Not a group: a project URL imports that one project - not its
        # whole parent group.
        await emit({"type": "stage", "message": "Not a group - trying as project..."})
        project = await client.get_project_by_path(group_path)
        if project is None:
            raise ValueError(
                f"GitLab resource not found: {group_path}. "
                "Make sure the URL points to a valid GitLab group or project "
                "and that the configured API token has access."
            )
        return await _import_single_project(run, project, group_path)

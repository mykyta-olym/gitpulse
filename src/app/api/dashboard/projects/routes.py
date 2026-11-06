"""Project detail, live data, and LLM analysis routes."""

import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dashboard._access import _can_manage_team, _can_view_team
from app.api.dashboard._helpers import (
    CHECK_DEFS,
    _csrf_token,
    _extended_checks,
    _not_found_response,
    _role_context,
    _templates,
    _threshold_pcts,
    logger,
)
from app.api.dashboard._roster import member_roles
from app.api.dashboard._stats import latest_student_metric_map
from app.api.dashboard.projects.llm import router as _projects_llm_router
from app.api.dashboard.teams.member_exclusion import member_base_category, member_visible_category
from app.config import get_settings
from app.dependencies import DashboardAuth, DbSession
from app.i18n import resolve_locale, translate_text
from app.models.course import Course
from app.models.metric_snapshot import MetricSnapshot
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.services.page_cache import (
    CSP_NONCE_PLACEHOLDER as _PAGE_CACHE_NONCE,
)
from app.services.page_cache import (
    CSRF_PLACEHOLDER as _PAGE_CACHE_CSRF,
)
from app.services.page_cache import (
    build_cache_render_ctx as _page_cache_build_ctx,
)
from app.services.page_cache import (
    cacheable_role_ctx as _page_cache_role_ctx,
)
from app.services.page_cache import (
    get_cached as _page_cache_get,
)
from app.services.page_cache import (
    make_role_variant as _page_cache_role_variant,
)
from app.services.page_cache import (
    render_inline as _render_inline,
)
from app.services.page_cache import (
    set_cached as _page_cache_set,
)
from app.utils.constants import PAGE_SIZE_REPORTS

router = APIRouter()
router.include_router(_projects_llm_router)


def _compute_scored_students(
    students: list[Any],
    memberships: dict[uuid.UUID, Any],
    project_direct_usernames: set[str],
) -> list[Any]:
    """Strict scored-cohort filter for the Issues to Address card.

    A student counts toward the project score IFF:
      * They have a real (non-synthetic) team membership.
      * They are not a teacher, mentor, or excluded-from-scoring.
      * Their team-level membership_source is not 'inherited'.
      * When the GitLab project's direct-member list was fetched
        successfully, their GitLab username appears in it (so students
        only inherited via the parent group are not scored against the
        individual project).

    Centralising the rule here ensures the live-data refresh and the
    full-page initial render agree on the cohort - relying on the
    template alone has repeatedly failed because the inputs differ
    between those two code paths (one passes synthetic memberships,
    the other does not).
    """
    out: list[Any] = []
    for s in students:
        m = memberships.get(s.id) if memberships else None
        if m is None:
            continue
        if getattr(m, "is_synthetic", False):
            continue
        if getattr(m, "is_teacher", False):
            continue
        if getattr(m, "is_mentor", False):
            continue
        if getattr(m, "excluded_from_scoring", False):
            continue
        uname = (s.gitlab_username or "").lower()
        # Being a member of THIS project (direct, inherited, or proven by MR
        # activity - all funnel into project_direct_usernames) means the student
        # works on it and must count, EVEN IF their team-level membership_source
        # is 'inherited'. Only drop a team-inherited student when they are not a
        # project member at all (a parent-group spill-over who never touched it).
        is_project_member = bool(project_direct_usernames) and uname in project_direct_usernames
        m_source = getattr(m, "membership_source", "") or ""
        if m_source == "inherited" and not is_project_member:
            continue
        if project_direct_usernames and uname and uname not in project_direct_usernames:
            continue
        out.append(s)
    return out


def _format_bytes(num: float | int | None) -> str:
    """Human-readable byte size, mirroring the JS ``formatBytes`` exactly."""
    if not num:
        return "0 B"
    units = ("B", "KB", "MB", "GB")
    size = float(num)
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{round(size, 1):g} {units[i]}"


def _build_gl_intel_view(gl: dict[str, Any] | None) -> dict[str, Any] | None:
    """Pre-compute the GitLab Intelligence panel for server-side rendering.

    Mirrors the client ``renderProtectedBranches`` / ``renderContributors`` /
    ``renderStatistics`` logic so the three cards paint fully on the server -
    no blank ``-`` placeholders, no JS-fill appearance animation on load.
    """
    if not gl:
        return None

    protected_raw = gl.get("protectedBranches")
    protected = (
        [b.get("name") for b in protected_raw if isinstance(b, dict) and b.get("name")]
        if isinstance(protected_raw, list)
        else []
    )

    contribs_raw = gl.get("contributors")
    merged: dict[str, dict[str, Any]] = {}
    if isinstance(contribs_raw, list):
        for c in contribs_raw:
            if not isinstance(c, dict):
                continue
            name = (c.get("name") or "").strip()
            key = name.lower()
            commits = int(c.get("commits") or 0)
            if key in merged:
                merged[key]["commits"] += commits
            else:
                merged[key] = {"name": name, "commits": commits}
    contributors = sorted(merged.values(), key=lambda c: c["commits"], reverse=True)[:10]
    max_commits = max((c["commits"] for c in contributors), default=0)
    for c in contributors:
        c["pct"] = round(c["commits"] / max_commits * 100) if max_commits > 0 else 0

    stats_raw = gl.get("statistics")
    stats: dict[str, Any] | None = None
    if isinstance(stats_raw, dict) and stats_raw:
        last_activity_dt: datetime | None = None
        raw_activity = stats_raw.get("last_activity_at")
        if isinstance(raw_activity, str) and raw_activity:
            with contextlib.suppress(ValueError):
                last_activity_dt = datetime.fromisoformat(raw_activity)
        elif isinstance(raw_activity, datetime):
            last_activity_dt = raw_activity
        stats = {
            "commit_count": int(stats_raw.get("commit_count") or 0),
            "repo_size": _format_bytes(stats_raw.get("repository_size")),
            "open_issues_count": int(stats_raw.get("open_issues_count") or 0),
            "last_activity_dt": last_activity_dt,
        }

    return {"protected": protected, "contributors": contributors, "stats": stats}


def _stored_usernames(values: Any) -> set[str]:
    """Return normalized usernames from a stored GitLab snapshot field."""
    if not isinstance(values, list):
        return set()
    out: set[str] = set()
    for value in values:
        if isinstance(value, str) and value.strip():
            out.add(value.strip().lower())
    return out


async def _derive_project_member_usernames_from_activity(
    db: DbSession,
    project_id: uuid.UUID,
) -> set[str]:
    """Recover a project cohort from stored MR relationships.

    This is the no-live-GitLab fallback used when an older project has not yet
    stored ``gitlab_intel.members``. It is intentionally project-scoped: we
    never fall back to "all team members" for multi-project teams because that
    produces phantom issue/check rows.
    """
    from app.models.merge_request import MergeRequest

    # Only the DISTINCT participants matter, never the individual rows. Select
    # them distinctly so a project with tens of thousands of merge requests
    # still ships a handful of rows instead of the whole table.
    rows = (
        await db.execute(
            select(
                MergeRequest.author_id,
                MergeRequest.assignee_id,
            )
            .where(MergeRequest.project_id == project_id)
            .distinct()
        )
    ).all()
    student_ids: set[uuid.UUID] = set()
    gitlab_ids: set[int] = set()
    for author_id, assignee_id in rows:
        if author_id:
            student_ids.add(author_id)
        if assignee_id:
            student_ids.add(assignee_id)

    # Reviewer/approver ids live in array columns; unnest them so the DISTINCT
    # happens in the database rather than over every row in Python.
    for id_column in (
        MergeRequest.reviewer_gitlab_ids,
        MergeRequest.approved_by_gitlab_ids,
    ):
        unnested = func.unnest(id_column).label("gitlab_id")
        for (gid,) in (
            await db.execute(
                select(unnested).where(MergeRequest.project_id == project_id).distinct()
            )
        ).all():
            if gid:
                gitlab_ids.add(int(gid))

    # Also count issue participation - a real teammate may have opened / been
    # assigned issues in this project without authoring any MR yet (the "4 shown
    # but 5 on the team" case). Same project-scoped rule, no live GitLab.
    from app.models.issue import Issue

    issue_rows = (
        await db.execute(
            select(
                Issue.author_id,
                Issue.assignee_id,
            )
            .where(Issue.project_id == project_id)
            .distinct()
        )
    ).all()
    for author_id, assignee_id in issue_rows:
        if author_id:
            student_ids.add(author_id)
        if assignee_id:
            student_ids.add(assignee_id)

    _issue_assignees = func.unnest(Issue.all_assignee_gitlab_ids).label("gitlab_id")
    for (gid,) in (
        await db.execute(select(_issue_assignees).where(Issue.project_id == project_id).distinct())
    ).all():
        if gid:
            gitlab_ids.add(int(gid))

    derived: set[str] = set()
    if student_ids:
        derived |= {
            username.strip().lower()
            for (username,) in (
                await db.execute(
                    select(Student.gitlab_username).where(
                        Student.id.in_(student_ids),
                        Student.gitlab_username.is_not(None),
                    )
                )
            ).all()
            if username and username.strip()
        }
    if gitlab_ids:
        derived |= {
            username.strip().lower()
            for (username,) in (
                await db.execute(
                    select(Student.gitlab_username).where(
                        Student.gitlab_user_id.in_(gitlab_ids),
                        Student.gitlab_username.is_not(None),
                    )
                )
            ).all()
            if username and username.strip()
        }
    return derived


async def _team_has_single_active_project(db: DbSession, team_id: uuid.UUID) -> bool:
    """Whether it is safe to use the whole team roster as a project roster."""
    count_stmt = select(func.count(GitLabProject.id)).where(
        GitLabProject.team_id == team_id,
        GitLabProject.is_active.is_(True),
    )
    count = (await db.execute(count_stmt)).scalar_one() or 0
    return int(count) <= 1


async def _resolve_project_member_scope(
    db: DbSession,
    project: GitLabProject,
) -> tuple[set[str], set[str], str]:
    """Resolve the project's student scope without live GitLab reads.

    Returns ``(display_usernames, scored_usernames, source)``.
    Direct project members are the preferred scope for both the table and
    scoring. If the project is from an older sync and lacks that snapshot, we
    fall back to all stored project members, then to MR activity, then only for
    true one-project teams to the whole team roster.
    """
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    direct_usernames = _stored_usernames(stored.get("direct_members"))
    member_usernames = _stored_usernames(stored.get("members"))
    from app.services.gitlab_import.service import is_bot_user as _is_bot_user

    direct_usernames = {u for u in direct_usernames if not _is_bot_user(u)}
    member_usernames = {u for u in member_usernames if not _is_bot_user(u)}

    if direct_usernames:
        return direct_usernames, direct_usernames, "stored_direct"
    if member_usernames:
        return member_usernames, member_usernames, "stored_members"

    derived = await _derive_project_member_usernames_from_activity(db, project.id)
    derived = {u for u in derived if not _is_bot_user(u)}
    if derived:
        return derived, derived, "activity"

    if await _team_has_single_active_project(db, project.team_id):
        return set(), set(), "single_project_team"
    return set(), set(), "unknown"


@dataclass
class _ProjectRoster:
    """The project's students, and what the page and its refresh read about them."""

    students: list[Student]
    memberships: dict[uuid.UUID, Any]
    project_direct_usernames: set[str]
    snapshots: dict[uuid.UUID, MetricSnapshot] = field(default_factory=dict)
    user_roles: dict[str, str] = field(default_factory=dict)
    course_roles: dict[str, str] = field(default_factory=dict)


async def _project_roster(
    db: DbSession,
    project: GitLabProject,
    team: Team,
    course: Course | None,
) -> _ProjectRoster:
    """The project's students - ONE answer for the page and its live refresh.

    The stored project scope narrows the team; a one-project team without a
    stored scope keeps its whole roster minus bots, and an unknown scope shows
    nobody rather than every team member. Students only: never a teacher or a
    mentor (the issue-activity derivation can pull in a Project Manager who
    authored issues, and inherited instructors ride along in the roster).

    Members excluded from scoring ARE on it - the table shows them, greyed. The
    refresh used to drop them, so their rows never refreshed and the
    `excluded_from_scoring` it sent was always False.
    """
    scope = await _resolve_project_member_scope(db, project)
    display_usernames, project_direct_usernames, source = scope
    memberships: dict[uuid.UUID, Any] = {m.student_id: m for m in team.active_members}
    students: list[Student] = []
    if memberships and (display_usernames or source == "single_project_team"):
        member_ids = [m.student_id for m in team.active_members]
        result = await db.execute(select(Student).where(Student.id.in_(member_ids)))
        students = list(result.scalars().all())
        if display_usernames:
            students = [
                s
                for s in students
                if s.gitlab_username and s.gitlab_username.lower() in display_usernames
            ]
        else:
            from app.services.gitlab_import.service import is_bot_user

            students = [
                s for s in students if not (s.gitlab_username and is_bot_user(s.gitlab_username))
            ]
    students = [
        s
        for s in students
        if not (
            getattr(memberships.get(s.id), "is_teacher", False)
            or getattr(memberships.get(s.id), "is_mentor", False)
        )
    ]
    roster = _ProjectRoster(students, memberships, project_direct_usernames)
    if not students:
        return roster

    roster.snapshots = await latest_student_metric_map(db, [s.id for s in students], team.id)
    roster.user_roles, roster.course_roles = await member_roles(db, students, course)
    return roster


@dataclass
class _RepoState:
    """The repository as the stored GitLab snapshot has it."""

    intel: dict[str, Any]
    empty: bool
    template_fork: bool
    dropped_authors: list[dict[str, Any]] = field(default_factory=list)


async def _student_contributors(
    db: DbSession,
    team: Team,
    contributors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split the commit authors into this team's students and everyone else.

    A whitelist: template authors, inherited teachers and bots are not on the
    team, so they drop out by themselves. An author is a student by name, email
    or GitLab username - or by an email whose local part is the username, since
    students commit as `<username>@student.university.edu`. The configured
    `excluded_contributor_names` drop out even when they match.
    """
    student_ids = [
        m.student_id
        for m in team.active_members
        if not m.is_teacher and not getattr(m, "is_mentor", False)
    ]
    idents: set[str] = set()
    username_locals: set[str] = set()
    if student_ids:
        stmt = select(Student.full_name, Student.email, Student.gitlab_username).where(
            Student.id.in_(student_ids)
        )
        for row in (await db.execute(stmt)).all():
            if row.full_name:
                idents.add(row.full_name.lower().strip())
            if row.email and row.email.lower().strip() != "private":
                idents.add(row.email.lower().strip())
            if row.gitlab_username:
                uname = row.gitlab_username.lower().strip()
                idents.add(uname)
                username_locals.add(uname)
    excluded = {n.lower().strip() for n in get_settings().excluded_contributor_names if n}

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for c in contributors:
        name = str(c.get("name") or "").lower().strip()
        email = str(c.get("email") or "").lower().strip()
        if name in excluded or email in excluded:
            dropped.append({"name": c.get("name"), "email": c.get("email"), "reason": "excluded"})
        elif (
            name in idents
            or email in idents
            or ("@" in email and email.split("@", 1)[0] in username_locals)
        ):
            kept.append(c)
        else:
            dropped.append(
                {"name": c.get("name"), "email": c.get("email"), "reason": "no_student_match"}
            )
    return kept, dropped


async def _project_repo_state(
    db: DbSession,
    project: GitLabProject,
    team: Team,
    roster: _ProjectRoster,
) -> _RepoState:
    """Read the stored snapshot once, the same way for the page and its refresh.

    The commit count that matters is the students' own. A fresh fork carries
    the upstream template's history, so its raw count is non-zero while nobody
    has pushed - a "fork of a template" - and a repository with no student
    commits is empty. The refresh counted with a second copy of the whitelist,
    against its narrower roster and without the configured exclusions, and the
    page skipped the snapshot for a student viewer; so both states could flip
    on the first refresh. Without stored statistics, a roster that has no
    snapshot at all is empty.
    """
    stored = (
        project.gitlab_intel
        if project.gitlab_project_id and isinstance(project.gitlab_intel, dict)
        else {}
    )
    intel = {
        k: stored[k] for k in ("protectedBranches", "contributors", "statistics") if stored.get(k)
    }
    dropped: list[dict[str, Any]] = []
    contributors = intel.get("contributors")
    if contributors and isinstance(contributors, list):
        kept, dropped = await _student_contributors(db, team, contributors)
        intel["contributors"] = kept
        stats = intel.get("statistics")
        if stats and isinstance(stats, dict):
            total = int(stats.get("commit_count") or 0)
            own = sum(c.get("commits", 0) for c in kept)
            intel["statistics"] = {
                **stats,
                "commit_count": own,
                "is_template_fork": total > 0 and own == 0,
            }
    stats = intel.get("statistics")
    if isinstance(stats, dict):
        empty = int(stats.get("commit_count") or 0) == 0
        return _RepoState(intel, empty, bool(stats.get("is_template_fork")), dropped)
    return _RepoState(intel, not roster.snapshots and bool(roster.students), False, dropped)


def _render_issues_card(request: Request, roster: _ProjectRoster, repo: _RepoState) -> str:
    """The Issues to Address card, as the page renders it."""
    return (
        _templates(request)
        .env.get_template("partials/project/_issues_to_address.html")
        .render(
            request=request,
            students=roster.students,
            scored_students=_compute_scored_students(
                roster.students, roster.memberships, roster.project_direct_usernames
            ),
            snapshots=roster.snapshots,
            memberships=roster.memberships,
            user_roles=roster.user_roles,
            course_roles=roster.course_roles,
            project_direct_usernames=roster.project_direct_usernames,
            repo_empty=repo.empty,
            template_fork=repo.template_fork,
        )
    )


@router.get("/projects/{project_id}/live-data")
async def project_live_data(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Return project student metrics as JSON for live DOM updates.

    Read exactly as the page is (`_project_roster`, `_project_repo_state`), so
    a refresh cannot disagree with the render it updates.
    """
    project = await db.get(GitLabProject, project_id)
    if not project:
        return JSONResponse({"error": "not_found"}, status_code=404)

    team_stmt = select(Team).where(Team.id == project.team_id).options(selectinload(Team.members))
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    if not team:
        return JSONResponse({"error": "not_found"}, status_code=404)

    if not await _can_view_team(team, _auth, db):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    course = await db.get(Course, team.course_id)
    roster = await _project_roster(db, project, team, course)
    repo = await _project_repo_state(db, project, team, roster)

    students_data = []
    all_bottlenecks = []
    _locale = resolve_locale(request)
    visible_students = roster.students
    if _auth.get("role") == "student" and not await _can_manage_team(team, _auth, db):
        visible_students = []
    for s in sorted(visible_students, key=lambda x: x.full_name or x.gitlab_username or ""):
        snap = roster.snapshots.get(s.id)
        membership = roster.memberships.get(s.id)
        checks = {}
        if snap:
            detail = snap.checks_detail or {}
            for attr, code, _ in CHECK_DEFS:
                cd = detail.get(code)
                if cd and isinstance(cd, dict):
                    checks[code] = {"pass": cd.get("pass"), "expected": cd.get("expected", True)}
                else:
                    val = getattr(snap, attr, None)
                    checks[code] = {"pass": val, "expected": True}
            # Include custom check results from checks_detail
            for cid, cinfo in detail.items():
                if cid not in checks and isinstance(cinfo, dict):
                    checks[cid] = {
                        "pass": cinfo.get("pass"),
                        "expected": cinfo.get("expected", True),
                    }
            if snap.bottlenecks:
                for bn in snap.bottlenecks:
                    bn_text = translate_text(_locale, bn)
                    if bn_text not in all_bottlenecks:
                        all_bottlenecks.append(bn_text)

        students_data.append(
            {
                "id": str(s.id),
                "name": s.full_name or s.gitlab_username or "Unknown",
                "gitlab_username": s.gitlab_username,
                "excluded_from_scoring": bool(getattr(membership, "excluded_from_scoring", False)),
                "member_category": (
                    member_visible_category(membership) if membership else "direct"
                ),
                "member_base_category": (
                    member_base_category(membership) if membership else "direct"
                ),
                # The stored snapshots of an empty repository predate it being
                # emptied: the banner says empty, so the metrics are blank.
                "checks": {} if repo.empty else checks,
                "score": (
                    round(snap.weighted_score * 100)
                    if snap and snap.weighted_score is not None and not repo.empty
                    else None
                ),
                "traffic_light": snap.traffic_light if snap and not repo.empty else None,
            },
        )

    # The Issues to Address card refreshes with every poll (exclusion toggle,
    # role change, run checks...).
    try:
        issues_html = _render_issues_card(request, roster, repo)
    except Exception as _e:  # pragma: no cover - template render is best-effort
        logger.warning("Failed to render issues partial", error=str(_e))
        issues_html = ""

    return JSONResponse(
        {
            "students": students_data,
            "bottlenecks": all_bottlenecks,
            "issues_html": issues_html,
            "repo_empty": repo.empty,
            "template_fork": repo.template_fork,
        },
    )


async def _project_llm_context(
    db: DbSession,
    project_id: uuid.UUID,
) -> tuple[list[Any], dict[str, Any] | None, Any]:
    """The project's AI analyses, its latest error when newer, and a running job."""
    from app.models.llm_log import LLMAnalysisLog

    # Fetch successful analyses (target_type='mr')
    llm_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type == "mr",
        )
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
        .limit(PAGE_SIZE_REPORTS)
    )
    llm_result = await db.execute(llm_stmt)
    llm_analyses = list(llm_result.scalars().all())

    # Fetch latest error entry if any (only from last 24 hours)
    llm_last_error = None
    error_cutoff = datetime.now(UTC) - timedelta(hours=24)
    error_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type.in_(("error", "job_failed")),
            LLMAnalysisLog.analysis_timestamp > error_cutoff,
        )
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
        .limit(1)
    )
    error_result = await db.execute(error_stmt)
    error_entry = error_result.scalar_one_or_none()
    if error_entry:
        # Only show error if it's more recent than last successful analysis
        latest_success_time = llm_analyses[0].analysis_timestamp if llm_analyses else None
        if not latest_success_time or error_entry.analysis_timestamp > latest_success_time:
            llm_last_error = dict(error_entry.structured_result)
            # Normalize job_failed entries to match error card template expectations
            if error_entry.target_type == "job_failed" and "error" in llm_last_error:
                raw_err = llm_last_error["error"]
                # Clean up raw tracebacks stored in the error field
                if "Traceback" in raw_err or "\n" in raw_err:
                    lines = raw_err.strip().splitlines()
                    exc_lines = [ln.strip() for ln in lines if ln.strip()]
                    clean_msg = exc_lines[-1][:200] if exc_lines else raw_err[:200]
                else:
                    clean_msg = raw_err[:200]
                # Classify for user-friendly display
                from app.workers.llm_job import classify_llm_error

                try:
                    _etype, _emsg = classify_llm_error(Exception(clean_msg))
                    llm_last_error["error_type"] = _etype.value
                    llm_last_error["error_message"] = _emsg
                except Exception:
                    llm_last_error.setdefault("error_type", "unknown")
                    llm_last_error["error_message"] = clean_msg
                llm_last_error.setdefault("is_error", True)
            llm_last_error["error_id"] = str(error_entry.id)

    # Check for running job
    job_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type == "job_running",
        )
        .limit(1)
    )
    job_result = await db.execute(job_stmt)
    return llm_analyses, llm_last_error, job_result.scalar_one_or_none()


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Project detail page with members table."""
    # Fetch project
    project = await db.get(GitLabProject, project_id)
    if not project:
        return _not_found_response(request, "Project")

    # Fetch team and course
    team_stmt = select(Team).where(Team.id == project.team_id).options(selectinload(Team.members))
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    if not team:
        return _not_found_response(request, "Group")

    # Check access permission
    if not await _can_view_team(team, _auth, db):
        return _not_found_response(
            request,
            "Project",
            message="You don't have access to this project.",
            suggestion="You can only view projects in groups you are a member of.",
        )

    course = await db.get(Course, team.course_id)

    role_ctx = {**_role_context(_auth), "can_edit": await _can_manage_team(team, _auth, db)}
    settings = get_settings()

    # -- GitLab-style single-response delivery -- content inlined into the full
    # page.
    _p_page_ctx = {
        "project": project,
        "team": team,
        "course": course,
        "gitlab_url": settings.gitlab_url,
        "feature_llm_suggestions": settings.llm_analysis_enabled,
    }

    # -- Short-lived Redis cache (60s) for the heavy content body --
    # Project detail resolves stored project scope/intelligence and runs
    # LLM queries - easily 1-3s on larger projects. The
    # rendered HTML varies only by locale + viewer role flags; CSRF
    # token, username, avatar_url, full_name and the per-request CSP
    # nonce are rendered as placeholders and substituted by
    # :func:`personalize`.
    _p_variant = _page_cache_role_variant(request, role_ctx)
    _p_cached = _page_cache_get("project", project_id, _p_variant)
    if _p_cached is not None:
        return _render_inline(
            request=request,
            fragment=_p_cached,
            csrf_token=_csrf_token(_auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="project_detail.html",
            page_ctx=_p_page_ctx,
        )

    roster = await _project_roster(db, project, team, course)
    repo = await _project_repo_state(db, project, team, roster)
    if repo.dropped_authors:
        # Diagnostic: which GitLab commit authors fell through the whitelist,
        # so the operator can fix student records or the exclusion list.
        logger.info(
            "Contributor whitelist filtered entries",
            project_id=str(project_id),
            kept=len(repo.intel.get("contributors") or ()),
            dropped=len(repo.dropped_authors),
            dropped_authors=repo.dropped_authors[:20],
        )

    llm_enabled = settings.llm_analysis_enabled
    llm_analyses: list[Any] = []
    llm_last_error = None
    running_job = None
    if llm_enabled:
        llm_analyses, llm_last_error, running_job = await _project_llm_context(db, project_id)

    # Check if analysis was just started (from redirect) or has running job
    analysis_started = (
        request.query_params.get("analysis_started") == "1" or running_job is not None
    )

    green_pct_proj, yellow_pct_proj = _threshold_pcts(course.settings if course else None)

    # The GitLab Intelligence card is staff-only; the repository state it is
    # read from is not.
    gl_intelligence = repo.intel if role_ctx["can_edit"] else {}

    _scored_full = _compute_scored_students(
        roster.students, roster.memberships, roster.project_direct_usernames
    )
    logger.info(
        "project-scored-cohort",
        project_id=str(project_id),
        students_total=len(roster.students),
        scored=len(_scored_full),
        direct_usernames=len(roster.project_direct_usernames or ()),
        synthetic=sum(
            1
            for s in roster.students
            if getattr(roster.memberships.get(s.id), "is_synthetic", False)
        ),
        repo_empty=repo.empty,
    )

    _p_ctx = {
        **_page_cache_build_ctx(request),
        "request": request,
        "project": project,
        "team": team,
        "course": course,
        "students": roster.students,
        "snapshots": roster.snapshots,
        "memberships": roster.memberships,
        "user_roles": roster.user_roles,
        "course_roles": roster.course_roles,
        "project_direct_usernames": roster.project_direct_usernames,
        "scored_students": _scored_full,
        "repo_empty": repo.empty,
        "template_fork": repo.template_fork,
        "checks": await _extended_checks(db, course.id if course else None),
        "feature_llm_suggestions": llm_enabled,
        "llm_analyses": llm_analyses,
        "llm_last_error": llm_last_error,
        "analysis_started": analysis_started,
        "gitlab_url": settings.gitlab_url,
        "csrf_token": _PAGE_CACHE_CSRF,
        "csp_nonce": _PAGE_CACHE_NONCE,
        "green_pct": green_pct_proj,
        "yellow_pct": yellow_pct_proj,
        "gl_intelligence": gl_intelligence,
        "gl_intel_view": _build_gl_intel_view(gl_intelligence),
        **_page_cache_role_ctx(role_ctx),
    }
    _p_rendered = (
        _templates(request).get_template("partials/project/_detail_content.html").render(_p_ctx)
    )
    _page_cache_set("project", project_id, _p_variant, _p_rendered)
    return _render_inline(
        request=request,
        fragment=_p_rendered,
        csrf_token=_csrf_token(_auth),
        role_ctx=role_ctx,
        templates=_templates(request),
        page_template="project_detail.html",
        page_ctx=_p_page_ctx,
    )

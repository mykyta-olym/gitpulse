"""What the student detail page shows - one function per section.

`build_profile_context` gathers every section for one student on one team;
`routes.py` owns access, caching and rendering. Every query is scoped by the
same `Scope`: the student's team, the active projects and the course's
activity window.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any, cast

from sqlalchemy import Row, case, func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dashboard._helpers import (
    _extended_checks,
    _is_own_student_profile,
    _semester_weeks_from_settings,
    _threshold_pcts,
)
from app.api.dashboard.students.diffs import (
    _attach_note_code_context,
    _build_diff_tree,
    _build_diff_views,
    _scope_diff_views,
)
from app.api.dashboard.students.notes import (
    _build_threads,
    _classify_mr_event,
    _note_view,
    _resolve_avatar,
)
from app.compliance.patterns import resolve_patterns
from app.config import get_settings
from app.models.commit import Commit
from app.models.course import Course
from app.models.issue import Issue
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.mr_diff import MergeRequestDiff
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.review_activity import ReviewActivity
from app.models.student import Student
from app.models.team_member import TeamMember
from app.models.user import User
from app.utils.constants import PAGE_SIZE_COMMITS, PAGE_SIZE_DETAIL_ITEMS
from app.utils.semester import get_effective_semester_end

_CLOCK_SKEW_GRACE = timedelta(minutes=5)
# Commits listed per merge-request branch when GitLab did not report the MR's own.
_BRANCH_COMMIT_CAP = 30


def _course_activity_window(
    course: Course | None,
    now: datetime | None = None,
) -> tuple[datetime | None, datetime | None, str]:
    """Return the active course activity window used by dashboard detail pages.

    When a course has a configured semester start, dashboard activity should be
    scoped to that course run. Otherwise old template/fork history imported from
    GitLab can make a 2026 course look like it has valid 2021/2022 work.
    """
    cs = course.settings if course else None
    if cs is None or cs.semester_start_date is None:
        return None, None, ""

    ref = now or datetime.now(UTC)
    start = datetime.combine(cs.semester_start_date, time.min, tzinfo=UTC)

    settings = get_settings()
    end_date = get_effective_semester_end(cs, settings.semester_default_length_weeks)
    if end_date is not None:
        semester_end_exclusive = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=UTC,
        )
        end_exclusive = min(semester_end_exclusive, ref + _CLOCK_SKEW_GRACE)
    else:
        end_exclusive = ref + _CLOCK_SKEW_GRACE

    visible_end = (end_exclusive - timedelta(microseconds=1)).date()
    label = f"{start.date().isoformat()} - {visible_end.isoformat()}"
    return start, end_exclusive, label


def _activity_window_conditions(
    column: Any,
    start: datetime | None,
    end_exclusive: datetime | None,
) -> tuple[Any, ...]:
    """Build SQLAlchemy timestamp predicates for an optional activity window."""
    conditions: list[Any] = []
    if start is not None:
        conditions.append(column >= start)
    if end_exclusive is not None:
        conditions.append(column < end_exclusive)
    return tuple(conditions)


@dataclass(frozen=True, slots=True)
class _PipelineRenderView:
    status: str
    has_test_job: bool
    test_job_status: str | None
    coverage: float | None
    render_coverage: float | None
    total_jobs: int

    @classmethod
    def from_pipeline(
        cls,
        pipeline: Pipeline,
        render_coverage: float | None,
    ) -> _PipelineRenderView:
        return cls(
            status=pipeline.status,
            has_test_job=pipeline.has_test_job,
            test_job_status=pipeline.test_job_status,
            coverage=pipeline.coverage,
            render_coverage=render_coverage,
            total_jobs=pipeline.total_jobs,
        )


@dataclass(frozen=True, slots=True)
class Scope:
    """Whose page this is, and the filters every section applies."""

    student: Student
    student_id: uuid.UUID
    team_id: uuid.UUID
    window_label: str
    mr_by_student: Any
    issue_by_student: Any
    mr_note_by_student: Any
    issue_window: tuple[Any, ...]
    mr_window: tuple[Any, ...]
    mr_note_window: tuple[Any, ...]
    commit_window: tuple[Any, ...]

    @classmethod
    def of(
        cls, student: Student, student_id: uuid.UUID, team_id: uuid.UUID, course: Course | None
    ) -> Scope:
        start, end, label = _course_activity_window(course)
        return cls(
            student=student,
            student_id=student_id,
            team_id=team_id,
            window_label=label,
            # Resolved author, else the GitLab identity the sync recorded.
            mr_by_student=or_(
                MergeRequest.author_id == student_id,
                (MergeRequest.author_id.is_(None))
                & (MergeRequest.author_gitlab_id == student.gitlab_user_id),
            ),
            issue_by_student=or_(
                Issue.author_id == student_id,
                (Issue.author_id.is_(None)) & (Issue.author_gitlab_id == student.gitlab_user_id),
            ),
            mr_note_by_student=or_(
                MRNote.author_id == student_id,
                (MRNote.author_id.is_(None)) & (MRNote.author_username == student.gitlab_username),
            ),
            issue_window=_activity_window_conditions(Issue.created_at, start, end),
            mr_window=_activity_window_conditions(MergeRequest.created_at, start, end),
            mr_note_window=_activity_window_conditions(MRNote.created_at, start, end),
            commit_window=_activity_window_conditions(Commit.committed_at, start, end),
        )

    def on_team(self) -> tuple[Any, ...]:
        """The team's active projects - joined in by every query."""
        return (GitLabProject.team_id == self.team_id, GitLabProject.is_active.is_(True))


@dataclass(frozen=True, slots=True)
class Roster:
    """Everyone on the team, keyed every way the page looks people up."""

    username_map: dict[str, str]
    profile_by_sid: dict[uuid.UUID, str]
    student_url_map: dict[str, str]
    by_gid: dict[int, dict[str, Any]]
    teacher_ids: set[uuid.UUID]
    teacher_gitlab_ids: set[int]


async def _load_roster(db: AsyncSession, team_id: uuid.UUID) -> Roster:
    rows = (
        await db.execute(
            select(
                Student.id,
                Student.gitlab_username,
                Student.full_name,
                Student.gitlab_user_id,
                TeamMember.is_teacher,
            )
            .join(TeamMember, TeamMember.student_id == Student.id)
            .where(TeamMember.team_id == team_id)
        )
    ).all()
    profile = f"/dashboard/students/{{}}/team/{team_id}"
    return Roster(
        # @mentions render as names; unknown handles stay plain @handles.
        username_map={
            (u or "").lower(): (fn or "").strip()
            for _sid, u, fn, _gid, _t in rows
            if u and fn and fn.strip()
        },
        # Teammates link to their GitPulse profile rather than out to GitLab.
        profile_by_sid={sid: profile.format(sid) for sid, _u, _fn, _gid, _t in rows if sid},
        student_url_map={
            (u or "").lower(): profile.format(sid) for sid, u, _fn, _gid, _t in rows if u and sid
        },
        # Explicit MR assignee / reviewers are stored as GitLab ids.
        by_gid={
            int(gid): {
                "name": (fn or "").strip() or f"@{u}",
                "profile_url": profile.format(sid),
                "student_id": sid,
            }
            for sid, u, fn, gid, _t in rows
            if gid
        },
        teacher_ids={sid for sid, _u, _fn, _gid, is_teacher in rows if is_teacher and sid},
        teacher_gitlab_ids={
            int(gid) for _sid, _u, _fn, gid, is_teacher in rows if is_teacher and gid
        },
    )


async def _student_avatar(db: AsyncSession, student: Student, auth: dict[str, str]) -> str | None:
    """The stored GitLab avatar or the session's for one's own page.

    Never a live GitLab call: data reaches GitPulse through sync and webhooks,
    and a render-time fetch stalls whenever the token has expired.
    """
    conditions = []
    if student.gitlab_user_id:
        conditions.append(User.gitlab_user_id == student.gitlab_user_id)
    if student.gitlab_username:
        conditions.append(User.gitlab_username == student.gitlab_username)
    url = None
    if conditions:
        url = (
            await db.execute(
                select(User.avatar_url)
                .where(or_(*conditions), User.avatar_url.is_not(None), User.avatar_url != "")
                .limit(1)
            )
        ).scalar_one_or_none()
    if not url and _is_own_student_profile(student, auth):
        url = auth.get("avatar_url") or None
    return url


async def _activity_counts(db: AsyncSession, sc: Scope) -> dict[str, int]:
    """Issues opened / assigned, MRs opened and comments written - windowed."""
    issues_authored, issues_assigned = (
        await db.execute(
            select(
                func.count(case((sc.issue_by_student, 1))),
                func.count(case((Issue.assignee_id == sc.student_id, 1))),
            )
            .select_from(Issue)
            .join(GitLabProject, Issue.project_id == GitLabProject.id)
            .where(
                *sc.on_team(),
                or_(sc.issue_by_student, Issue.assignee_id == sc.student_id),
                *sc.issue_window,
            )
        )
    ).one()
    mrs_authored = (
        await db.execute(
            select(func.count())
            .select_from(MergeRequest)
            .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
            .where(*sc.on_team(), sc.mr_by_student, *sc.mr_window)
        )
    ).scalar()
    notes_by_student = (
        await db.execute(
            select(func.count())
            .select_from(MRNote)
            .join(MergeRequest, MRNote.merge_request_id == MergeRequest.id)
            .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
            .where(
                *sc.on_team(),
                MRNote.is_system.is_(False),
                sc.mr_note_by_student,
                *sc.mr_window,
                *sc.mr_note_window,
            )
        )
    ).scalar()
    return {
        "issues_authored_count": issues_authored or 0,
        "issues_assigned_count": issues_assigned or 0,
        "mrs_authored_count": mrs_authored or 0,
        "notes_by_student_count": notes_by_student or 0,
    }


async def _issues_involving(db: AsyncSession, sc: Scope) -> list[dict[str, Any]]:
    """Every issue the student opened or is assigned, with both sides named.

    One list, not an "authored" and an "assigned" tab: an issue can be both,
    and the row says which side the student is on.
    """
    assignee = aliased(Student)
    assignee_member = aliased(TeamMember)
    author = aliased(Student)
    author_member = aliased(TeamMember)
    rows = await db.execute(
        select(
            Issue,
            GitLabProject.gitlab_project_path,
            author.full_name,
            author.gitlab_username,
            author_member.is_teacher,
            assignee.full_name,
            assignee.gitlab_username,
            assignee_member.is_teacher,
        )
        .join(GitLabProject, Issue.project_id == GitLabProject.id)
        .outerjoin(author, Issue.author_id == author.id)
        .outerjoin(
            author_member,
            (author_member.student_id == author.id) & (author_member.team_id == sc.team_id),
        )
        .outerjoin(assignee, Issue.assignee_id == assignee.id)
        .outerjoin(
            assignee_member,
            (assignee_member.student_id == assignee.id) & (assignee_member.team_id == sc.team_id),
        )
        .where(
            *sc.on_team(),
            or_(sc.issue_by_student, Issue.assignee_id == sc.student_id),
            *sc.issue_window,
        )
        .order_by(Issue.updated_at.desc().nulls_last(), Issue.created_at.desc().nulls_last())
        .limit(PAGE_SIZE_DETAIL_ITEMS)
    )
    return [
        {
            "issue": issue,
            "project_path": path,
            "author_name": author_name,
            "author_username": author_username,
            "author_is_teacher": bool(author_is_teacher),
            "assignee_name": assignee_name,
            "assignee_username": assignee_username,
            "assignee_is_teacher": bool(assignee_is_teacher),
            "is_author": issue.author_id == sc.student_id
            or (issue.author_id is None and issue.author_gitlab_id == sc.student.gitlab_user_id),
            "is_assignee": issue.assignee_id == sc.student_id,
        }
        for (
            issue,
            path,
            author_name,
            author_username,
            author_is_teacher,
            assignee_name,
            assignee_username,
            assignee_is_teacher,
        ) in rows.all()
    ]


def _commit_author(row: Any, sc: Scope, roster: Roster) -> dict[str, Any]:
    """Resolve a stored commit's author for MR cards."""
    student = sc.student
    return {
        "name": row.author_name
        or (f"GitLab#{row.author_gitlab_id}" if row.author_gitlab_id else None)
        or (row.author_email or "Unknown"),
        "is_page_student": bool(
            (row.author_id is not None and row.author_id == sc.student_id)
            or (
                student.gitlab_user_id is not None
                and row.author_gitlab_id == student.gitlab_user_id
            )
            or (
                student.email
                and row.author_email
                and row.author_email.lower() == student.email.lower()
            )
        ),
        "is_teacher": bool(
            (row.author_id and row.author_id in roster.teacher_ids)
            or (row.author_gitlab_id and row.author_gitlab_id in roster.teacher_gitlab_ids)
        ),
    }


def _decorate_commit(commit: Commit, sc: Scope, roster: Roster) -> Commit:
    """Attach the render-time author fields the MR card's commit list reads."""
    who = _commit_author(commit, sc, roster)
    profile_url = roster.profile_by_sid.get(commit.author_id) if commit.author_id else None
    if (
        not profile_url
        and commit.author_gitlab_id
        and int(commit.author_gitlab_id) in roster.by_gid
    ):
        profile_url = roster.by_gid[int(commit.author_gitlab_id)].get("profile_url")
    commit.is_teacher_commit = who["is_teacher"]  # type: ignore[attr-defined]
    commit.render_author_display = who["name"]  # type: ignore[attr-defined]
    commit.render_author_profile_url = profile_url  # type: ignore[attr-defined]
    return commit


async def _mr_pipelines(
    db: AsyncSession, mr_ids: list[uuid.UUID]
) -> dict[uuid.UUID, _PipelineRenderView]:
    """Each MR's latest pipeline; a missing coverage is taken from another
    pipeline on the same commit that reported one (never from GitLab live)."""
    latest: dict[uuid.UUID, Pipeline] = {}
    for pipeline in (
        await db.execute(
            select(Pipeline)
            .where(Pipeline.merge_request_id.in_(mr_ids))
            .order_by(
                Pipeline.merge_request_id,
                Pipeline.created_at.desc().nulls_last(),
                Pipeline.id.desc(),
            )
        )
    ).scalars():
        if pipeline.merge_request_id is not None and pipeline.merge_request_id not in latest:
            latest[pipeline.merge_request_id] = pipeline

    coverage = {mr_id: p.coverage for mr_id, p in latest.items()}
    missing = {p.sha for p in latest.values() if p.sha and p.coverage is None}
    if missing:
        by_sha: dict[str, float] = {}
        for p in (
            await db.execute(
                select(Pipeline)
                .where(
                    Pipeline.project_id.in_(
                        {p.project_id for p in latest.values() if p.project_id}
                    ),
                    Pipeline.sha.in_(missing),
                    Pipeline.coverage.is_not(None),
                )
                .order_by(Pipeline.sha, Pipeline.created_at.desc().nulls_last(), Pipeline.id.desc())
            )
        ).scalars():
            if p.sha and p.coverage is not None and p.sha not in by_sha:
                by_sha[p.sha] = p.coverage
        for mr_id, p in latest.items():
            if coverage.get(mr_id) is None and p.sha in by_sha:
                coverage[mr_id] = by_sha[p.sha]
    return {
        mr_id: _PipelineRenderView.from_pipeline(p, coverage.get(mr_id))
        for mr_id, p in latest.items()
    }


async def _diff_views(
    db: AsyncSession, mr_ids: list[uuid.UUID], scope: str
) -> dict[uuid.UUID, list[dict[str, Any]]]:
    """Rendered diff files per MR, their anchors scoped by `scope`."""
    raw: dict[uuid.UUID, list[MergeRequestDiff]] = {}
    for diff in (
        await db.execute(
            select(MergeRequestDiff).where(MergeRequestDiff.merge_request_id.in_(mr_ids))
        )
    ).scalars():
        raw.setdefault(diff.merge_request_id, []).append(diff)
    views = {}
    for mr_id, diffs in raw.items():
        views[mr_id] = _build_diff_views(diffs)
        _scope_diff_views(views[mr_id], f"{scope}-{mr_id}")
    return views


async def _mr_commits(
    db: AsyncSession, sc: Scope, roster: Roster, mrs: Sequence[Row[tuple[MergeRequest, str]]]
) -> tuple[
    dict[tuple[uuid.UUID, str], list[Commit]],
    dict[uuid.UUID, list[Commit]],
]:
    """Windowed branch history and the exact commits GitLab reports for each MR."""
    by_branch: dict[tuple[uuid.UUID, str], list[Commit]] = {}
    pairs = [(mr.project_id, mr.source_branch) for mr, _path in mrs if mr.source_branch]
    if pairs:
        # The course window: without it a branch forked from a template listed
        # the template's whole history under a merge request opened this term.
        for commit in (
            await db.execute(
                select(Commit)
                .where(tuple_(Commit.project_id, Commit.ref).in_(pairs), *sc.commit_window)
                .order_by(Commit.committed_at.desc().nulls_last())
            )
        ).scalars():
            bucket = by_branch.setdefault((commit.project_id, commit.ref or ""), [])
            if len(bucket) < _BRANCH_COMMIT_CAP:
                bucket.append(_decorate_commit(commit, sc, roster))

    # By sha rather than out of the branch bucket: that bucket is capped before
    # anything is filtered, so the MR's own commits could fall outside it.
    by_mr: dict[uuid.UUID, list[Commit]] = {}
    by_key: dict[tuple[uuid.UUID, str], Commit] = {}
    sha_pairs = [(mr.project_id, sha) for mr, _p in mrs for sha in (mr.commit_shas or [])]
    if sha_pairs:
        by_key = {
            (c.project_id, c.sha): _decorate_commit(c, sc, roster)
            for c in (
                await db.execute(
                    select(Commit).where(tuple_(Commit.project_id, Commit.sha).in_(sha_pairs))
                )
            ).scalars()
        }
    for mr, _path in mrs:
        if mr.commit_shas is None:
            continue
        found = [
            by_key[(mr.project_id, sha)]
            for sha in dict.fromkeys(mr.commit_shas)
            if (mr.project_id, sha) in by_key
        ]
        found.sort(key=lambda c: (c.committed_at is not None, c.committed_at), reverse=True)
        by_mr[mr.id] = found
    return by_branch, by_mr


@dataclass(slots=True)
class _Discussions:
    notes: dict[uuid.UUID, list[MRNote]]
    events: dict[uuid.UUID, list[MRNote]]
    reviewers: dict[uuid.UUID, list[dict[str, Any]]]
    students: dict[uuid.UUID, Any]


async def _mr_discussions(
    db: AsyncSession, sc: Scope, roster: Roster, mr_ids: list[uuid.UUID], participant_gids: set[int]
) -> _Discussions:
    """Every note on the student's MRs (threads + system events) and who reviewed them."""
    d = _Discussions({}, {}, {}, {sc.student.id: sc.student})
    if not mr_ids:
        return d
    author_ids: set[uuid.UUID] = set()
    for note in (
        await db.execute(
            select(MRNote)
            .where(MRNote.merge_request_id.in_(mr_ids))
            .order_by(MRNote.created_at.asc().nulls_last(), MRNote.id.asc())
        )
    ).scalars():
        (d.events if note.is_system else d.notes).setdefault(note.merge_request_id, []).append(note)
        if note.author_id:
            author_ids.add(note.author_id)
    if author_ids or participant_gids:
        for s in (
            await db.execute(
                select(Student).where(
                    or_(Student.id.in_(author_ids), Student.gitlab_user_id.in_(participant_gids))
                )
            )
        ).scalars():
            d.students[s.id] = s

    for ra, rs in (
        await db.execute(
            select(ReviewActivity, Student)
            .outerjoin(Student, ReviewActivity.reviewer_id == Student.id)
            .where(ReviewActivity.merge_request_id.in_(mr_ids))
            .order_by(ReviewActivity.note_count.desc(), Student.full_name.asc())
        )
    ).all():
        if rs is not None:
            d.students.setdefault(rs.id, rs)
        d.reviewers.setdefault(ra.merge_request_id, []).append(
            {
                "name": (rs.full_name or f"@{rs.gitlab_username}") if rs else "Unknown",
                "note_count": ra.note_count,
                "total_words": ra.total_words,
                "is_meaningful": ra.is_meaningful,
                "is_page_student": ra.reviewer_id == sc.student_id,
                "is_teacher": ra.reviewer_id in roster.teacher_ids,
                "profile_url": roster.profile_by_sid.get(rs.id) if rs else None,
                "_gid": rs.gitlab_user_id if rs else None,
                "_uname": rs.gitlab_username if rs else None,
            }
        )
    return d


async def _avatars(
    db: AsyncSession, d: _Discussions, sc: Scope, student_avatar_url: str | None
) -> tuple[dict[int, str], dict[str, str]]:
    """Avatars of every participant, by GitLab id and by username - one query."""
    gids: set[int] = set()
    unames: set[str] = set()
    for s in d.students.values():
        if s.gitlab_user_id:
            gids.add(int(s.gitlab_user_id))
        if s.gitlab_username:
            unames.add(s.gitlab_username.lower())
    for notes in (*d.notes.values(), *d.events.values()):
        for note in notes:
            if note.author_gitlab_id:
                gids.add(int(note.author_gitlab_id))
            if note.author_username:
                unames.add(note.author_username.lower())
    by_gid: dict[int, str] = {}
    by_uname: dict[str, str] = {}
    if gids or unames:
        conds = []
        if gids:
            conds.append(User.gitlab_user_id.in_(gids))
        if unames:
            conds.append(func.lower(User.gitlab_username).in_(unames))
        for gid, uname, url in (
            await db.execute(
                select(User.gitlab_user_id, User.gitlab_username, User.avatar_url).where(
                    or_(*conds), User.avatar_url.is_not(None), User.avatar_url != ""
                )
            )
        ).all():
            if gid:
                by_gid[int(gid)] = url
            if uname:
                by_uname[uname.lower()] = url
    # The page student's own avatar is already resolved, fallbacks included.
    if student_avatar_url and sc.student.gitlab_user_id:
        by_gid.setdefault(int(sc.student.gitlab_user_id), student_avatar_url)
    if student_avatar_url and sc.student.gitlab_username:
        by_uname.setdefault(sc.student.gitlab_username.lower(), student_avatar_url)
    return by_gid, by_uname


class _NoteViews:
    """`_note_view` with everything but the note bound."""

    def __init__(
        self,
        d: _Discussions,
        sc: Scope,
        roster: Roster,
        by_gid: dict[int, str],
        by_uname: dict[str, str],
    ) -> None:
        self._args = (
            d.students,
            roster.username_map,
            roster.teacher_ids,
            roster.teacher_gitlab_ids,
            sc.student_id,
            by_gid,
            by_uname,
            roster.profile_by_sid,
        )

    def __call__(self, note: Any) -> dict[str, Any]:
        return _note_view(note, *self._args)


def _mr_reviewers(
    mr: MergeRequest, commented: list[dict[str, Any]], roster: Roster, by_gid: dict[int, str]
) -> list[dict[str, Any]]:
    """Who commented (ReviewActivity) merged with GitLab's explicit reviewers and approvals."""
    approved = {int(g) for g in (mr.approved_by_gitlab_ids or [])}
    assigned = {int(g) for g in (mr.reviewer_gitlab_ids or [])}
    reviewers = list(commented)
    seen: set[int] = set()
    for r in reviewers:
        gid = r.get("_gid")
        r["is_approved"] = gid is not None and int(gid) in approved
        r.setdefault("is_assigned", False)
        r.setdefault("profile_url", None)
        if gid is not None:
            gid = int(gid)
            seen.add(gid)
            r["is_assigned"] = gid in assigned
            info = roster.by_gid.get(gid)
            if info:
                r["profile_url"] = info["profile_url"]
    # Assignment and approval are independent of leaving a comment.
    for gid in sorted((assigned | approved) - seen):
        info = roster.by_gid.get(gid)
        reviewers.append(
            {
                "name": info["name"] if info else f"GitLab#{gid}",
                "note_count": 0,
                "total_words": 0,
                "is_approved": gid in approved,
                "is_meaningful": False,
                "is_assigned": gid in assigned,
                "is_page_student": False,
                "is_teacher": gid in roster.teacher_gitlab_ids,
                "profile_url": info["profile_url"] if info else None,
                "avatar_url": by_gid.get(gid),
            }
        )
    return reviewers


async def _authored_mrs(
    db: AsyncSession, sc: Scope, roster: Roster, student_avatar_url: str | None
) -> tuple[list[dict[str, Any]], dict[tuple[uuid.UUID, str], list[Commit]], _NoteViews]:
    """The MR cards: pipeline, diff, commits, reviewers, threads and activity per MR."""
    mrs = list(
        (
            await db.execute(
                select(MergeRequest, GitLabProject.gitlab_project_path)
                .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
                .where(*sc.on_team(), sc.mr_by_student, *sc.mr_window)
                .order_by(
                    MergeRequest.updated_at.desc().nulls_last(),
                    MergeRequest.created_at.desc().nulls_last(),
                )
                .limit(PAGE_SIZE_DETAIL_ITEMS)
            )
        ).all()
    )
    mr_ids = [mr.id for mr, _path in mrs]
    pipelines = await _mr_pipelines(db, mr_ids) if mr_ids else {}
    diffs = await _diff_views(db, mr_ids, "mr") if mr_ids else {}
    by_branch, commits_by_mr = await _mr_commits(db, sc, roster, mrs)
    participant_gids = {
        int(gid)
        for mr, _ in mrs
        for gid in [
            *(mr.reviewer_gitlab_ids or []),
            *(mr.approved_by_gitlab_ids or []),
            mr.assignee_gitlab_id,
        ]
        if gid is not None
    }
    d = await _mr_discussions(db, sc, roster, mr_ids, participant_gids)
    for person in d.students.values():
        if person.gitlab_user_id:
            roster.by_gid.setdefault(
                int(person.gitlab_user_id),
                {
                    "name": person.full_name or f"@{person.gitlab_username}",
                    "profile_url": roster.profile_by_sid.get(person.id),
                    "student_id": person.id,
                },
            )
    by_gid, by_uname = await _avatars(db, d, sc, student_avatar_url)
    for reviewers in d.reviewers.values():
        for r in reviewers:
            r["avatar_url"] = _resolve_avatar(r.get("_gid"), r.get("_uname"), by_gid, by_uname)
    view = _NoteViews(d, sc, roster, by_gid, by_uname)

    cards = []
    for mr, project_path in mrs:
        branch = (mr.project_id, mr.source_branch or "")
        commits = commits_by_mr.get(mr.id, by_branch.get(branch, []))
        commit_data_missing = mr.commit_shas is None or len(commits) != len(set(mr.commit_shas))
        authors = (
            {}
            if commit_data_missing
            else {
                c.author_id
                or c.author_gitlab_id
                or (c.author_email or c.author_name or "").casefold(): _commit_author(c, sc, roster)
                for c in commits
            }
        )
        views = [view(n) for n in d.notes.get(mr.id, [])]
        _attach_note_code_context(views, diffs.get(mr.id, []))
        threads = _build_threads(views)
        participants = _mr_reviewers(mr, d.reviewers.get(mr.id, []), roster, by_gid)
        assignee = None
        if mr.assignee_gitlab_id:
            gid = int(mr.assignee_gitlab_id)
            info = roster.by_gid.get(gid)
            assignee = {
                "name": info["name"] if info else f"GitLab#{gid}",
                "profile_url": info["profile_url"] if info else None,
                "avatar_url": by_gid.get(gid),
                "is_page_student": mr.assignee_id == sc.student_id,
            }
        events = []
        for note in d.events.get(mr.id, []):
            kind_icon = _classify_mr_event(note.body)
            if kind_icon is None:
                continue
            ev = view(note)
            ev["kind"], ev["icon"] = kind_icon
            ev["summary"] = (note.body or "").strip().splitlines()[0] if note.body else ""
            events.append(ev)
        cards.append(
            {
                "mr": mr,
                "project_path": project_path,
                "pipeline": pipelines.get(mr.id),
                "diffs": diffs.get(mr.id, []),
                "diff_tree": _build_diff_tree(diffs[mr.id]) if mr.id in diffs else None,
                "commit_authors": list(authors.values()),
                "commit_data_missing": commit_data_missing,
                "commit_list_known": mr.commit_shas is not None,
                "threads": threads,
                "thread_count": len(threads),
                "open_thread_count": sum(
                    1 for t in threads if t["is_resolvable"] and not t["is_resolved"]
                ),
                "resolved_thread_count": sum(1 for t in threads if t["is_resolved"]),
                "note_count": len(views),
                # The commits GitLab reports for THIS MR when the sync has them;
                # otherwise (commit_shas NULL on older rows) the branch's.
                "branch_commits": commits,
                "assignee": assignee,
                "reviewers": [p for p in participants if p["is_assigned"]],
                "participants": [p for p in participants if not p["is_assigned"]],
                "has_review_activity": any(
                    p["note_count"] or p["is_approved"] for p in participants
                ),
                "events": events,
            }
        )
    return cards, by_branch, view


async def _reviews_given(
    db: AsyncSession, sc: Scope, roster: Roster, view: _NoteViews
) -> list[dict[str, Any]]:
    """The student's own comments on MRs they did not author, as review threads."""
    peer_author = aliased(Student)
    by_mr: dict[uuid.UUID, dict[str, Any]] = {}
    for note, mr, project_path, author in (
        await db.execute(
            select(MRNote, MergeRequest, GitLabProject.gitlab_project_path, peer_author)
            .join(MergeRequest, MRNote.merge_request_id == MergeRequest.id)
            .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
            .outerjoin(peer_author, MergeRequest.author_id == peer_author.id)
            .where(
                *sc.on_team(),
                sc.mr_note_by_student,
                MRNote.is_system.is_(False),
                ~sc.mr_by_student,
                *sc.mr_window,
                *sc.mr_note_window,
            )
            .order_by(MergeRequest.updated_at.desc().nulls_last(), MRNote.created_at.asc())
        )
    ).all():
        entry = by_mr.get(mr.id)
        if entry is None:
            entry = by_mr[mr.id] = {
                "mr": mr,
                "project_path": project_path,
                "is_approved": sc.student.gitlab_user_id in (mr.approved_by_gitlab_ids or []),
                "author_display": (author.full_name or f"@{author.gitlab_username}")
                if author
                else "Unknown",
                "author_profile_url": roster.profile_by_sid.get(cast(uuid.UUID, author.id))
                if author
                else None,
                "notes": [],
            }
        entry["notes"].append(note)
    if not by_mr:
        return []

    summaries = {
        ra.merge_request_id: ra
        for ra in (
            await db.execute(
                select(ReviewActivity).where(
                    ReviewActivity.reviewer_id == sc.student_id,
                    ReviewActivity.merge_request_id.in_(list(by_mr)),
                )
            )
        ).scalars()
    }
    diffs = await _diff_views(db, list(by_mr), "review")
    reviews = []
    for mr_id, entry in by_mr.items():
        views = [view(n) for n in entry.pop("notes")]
        _attach_note_code_context(views, diffs.get(mr_id, []))
        entry["threads"] = _build_threads(views)
        entry["note_count"] = len(views)
        entry["review"] = summaries.get(mr_id)
        reviews.append(entry)
    return reviews


async def _commits(
    db: AsyncSession, sc: Scope, by_branch: dict[tuple[uuid.UUID, str], list[Commit]]
) -> dict[str, Any]:
    """The student's commit history, its totals and each commit's pipeline status."""
    student = sc.student
    # Attribution, strongest first: the resolved student, their GitLab id, the
    # raw git email (a personal address the roster did not know at sync time),
    # and as a last resort the git author name.
    clauses = [Commit.author_id == sc.student_id]
    if student.gitlab_user_id is not None:
        clauses.append(Commit.author_gitlab_id == student.gitlab_user_id)
    if student.email:
        clauses.append(func.lower(Commit.author_email) == student.email.lower())
    if student.full_name:
        clauses.append(func.lower(Commit.author_name) == student.full_name.lower())
    by_student = or_(*clauses)

    def count(*window: Any) -> Any:
        return (
            select(func.count())
            .select_from(Commit)
            .join(GitLabProject, Commit.project_id == GitLabProject.id)
            .where(*sc.on_team(), by_student, *window)
        )

    all_count = (await db.execute(count())).scalar() or 0
    in_window = (
        (await db.execute(count(*sc.commit_window))).scalar() or 0
        if sc.commit_window
        else all_count
    )

    commits = [
        {"commit": commit, "project_path": path}
        for commit, path in (
            await db.execute(
                select(Commit, GitLabProject.gitlab_project_path)
                .join(GitLabProject, Commit.project_id == GitLabProject.id)
                .where(*sc.on_team(), by_student, *sc.commit_window)
                .order_by(Commit.committed_at.desc().nulls_last())
                .limit(PAGE_SIZE_COMMITS)
            )
        ).all()
    ]

    # The pipeline mark GitLab draws beside each commit, for every sha on the
    # page (history and MR branch lists) - one query.
    pipeline_status: dict[str, str] = {}
    shas = {row["commit"].sha for row in commits if row["commit"].sha}
    for bucket in by_branch.values():
        shas.update(c.sha for c in bucket if c.sha)
    if shas:
        for sha, status in (
            await db.execute(
                select(Pipeline.sha, Pipeline.status)
                .where(Pipeline.sha.in_(shas))
                .order_by(Pipeline.created_at.desc().nulls_last(), Pipeline.id.desc())
            )
        ).all():
            if sha and sha not in pipeline_status:
                pipeline_status[sha] = status

    # Line totals count only the student's own single-parent commits: a merge
    # commit carries the merged-in diff, a root commit is the template import,
    # and a revert undoes work and would count it twice.
    totals = (
        await db.execute(
            select(func.sum(Commit.additions), func.sum(Commit.deletions))
            .join(GitLabProject, Commit.project_id == GitLabProject.id)
            .where(
                *sc.on_team(),
                by_student,
                *sc.commit_window,
                func.array_length(Commit.parent_shas, 1) == 1,
                (Commit.message.is_(None)) | (~Commit.message.ilike('Revert "%')),
            )
        )
    ).one()
    return {
        "commits_authored": commits,
        "commit_pipeline_status": pipeline_status,
        "commits_authored_count": in_window,
        "commits_out_of_scope_count": max(0, all_count - in_window),
        "commits_total_additions": totals[0] or 0,
        "commits_total_deletions": totals[1] or 0,
    }


async def _compliance_history(
    db: AsyncSession, student: Student, course: Course | None
) -> list[dict[str, Any]]:
    """The Compliance Progress rows, inlined so the card paints at its final size."""
    if not course:
        return []
    from app.schemas.compliance import StudentComplianceHistoryResponse
    from app.services.compliance_history import ComplianceHistoryService

    history = ComplianceHistoryService(db)
    return [
        StudentComplianceHistoryResponse.model_validate(item).model_dump()
        for item in await history.get_student_compliance_history(student.id, course.id, 52)
    ]


async def build_profile_context(
    db: AsyncSession,
    *,
    student: Student,
    student_id: uuid.UUID,
    team_id: uuid.UUID,
    course: Course | None,
    auth: dict[str, str],
) -> dict[str, Any]:
    """Every section of the student page, as the content template reads it."""
    sc = Scope.of(student, student_id, team_id, course)
    roster = await _load_roster(db, team_id)
    snapshot = (
        await db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.student_id == student_id, MetricSnapshot.team_id == team_id)
            .order_by(MetricSnapshot.computed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    avatar_url = await _student_avatar(db, student, auth)
    counts = await _activity_counts(db, sc)
    issues = await _issues_involving(db, sc)
    mrs, by_branch, view = await _authored_mrs(db, sc, roster, avatar_url)
    reviews = await _reviews_given(db, sc, roster, view)
    commits = await _commits(db, sc, by_branch)
    cs = course.settings if course else None
    green_pct, yellow_pct = _threshold_pcts(cs)
    return {
        "snapshot": snapshot,
        "checks": await _extended_checks(db, course.id if course else None),
        "issues_involving": issues,
        **counts,
        "mrs_authored": mrs,
        # Issues and MRs link to each other in-page, as they do in GitLab.
        "page_issue_iids": {r["issue"].gitlab_iid for r in issues if r["issue"].gitlab_iid},
        "mr_iid_by_issue_iid": {
            e["mr"].linked_issue_iid: e["mr"].gitlab_iid for e in mrs if e["mr"].linked_issue_iid
        },
        "reviews_given": reviews,
        "reviews_given_count": len(reviews),
        **commits,
        "activity_window_label": sc.window_label,
        "has_any_activity": commits["commits_authored_count"] > 0
        or counts["mrs_authored_count"] > 0
        or counts["issues_authored_count"] > 0
        or counts["issues_assigned_count"] > 0,
        "student_avatar_url": avatar_url,
        "green_pct": green_pct,
        "yellow_pct": yellow_pct,
        "semester_weeks": _semester_weeks_from_settings(cs),
        "history_first_json": {"history": await _compliance_history(db, student, course)},
        "username_map": roster.username_map,
        "student_url_map": roster.student_url_map,
        "mr_required_sections": resolve_patterns(cs).required_sections,
    }

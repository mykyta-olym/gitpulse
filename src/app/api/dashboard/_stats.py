"""Shared contributor & score queries for the course dashboard.

Every endpoint that needs per-team or per-project contributor counts
MUST use these helpers so the numbers stay consistent everywhere
(initial HTML render, /live-data JSON, SSE stream).

Uses a **whitelist** approach: only commits whose author_name or
author_email matches a known student team member are counted.
Template authors, bots, and inherited teachers are excluded
automatically because they are not student members of the team.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit import Commit
from app.models.metric_snapshot import MetricSnapshot
from app.models.project import GitLabProject
from app.models.team_metric_snapshot import TeamMetricSnapshot


async def latest_team_metric_map(
    db: AsyncSession,
    team_ids: list[uuid.UUID],
) -> dict[uuid.UUID, TeamMetricSnapshot]:
    """Return each team's most-recent ``TeamMetricSnapshot``, keyed by team_id.

    One query: a ``max(computed_at)`` subquery grouped by team, joined back to
    the snapshot rows. On the rare tie (two snapshots sharing the exact max
    ``computed_at``) the row returned last wins -- matching the inline query
    this consolidates.
    """
    if not team_ids:
        return {}

    latest_sq = (
        select(
            TeamMetricSnapshot.team_id,
            func.max(TeamMetricSnapshot.computed_at).label("max_computed"),
        )
        .where(TeamMetricSnapshot.team_id.in_(team_ids))
        .group_by(TeamMetricSnapshot.team_id)
        .subquery()
    )
    stmt = select(TeamMetricSnapshot).join(
        latest_sq,
        (TeamMetricSnapshot.team_id == latest_sq.c.team_id)
        & (TeamMetricSnapshot.computed_at == latest_sq.c.max_computed),
    )
    result = await db.execute(stmt)
    return {s.team_id: s for s in result.scalars().all()}


async def latest_student_metric_map(
    db: AsyncSession,
    student_ids: list[uuid.UUID],
    team_id: uuid.UUID,
) -> dict[uuid.UUID, MetricSnapshot]:
    """Return each student's most-recent ``MetricSnapshot`` within one team.

    Keyed by student_id, scoped to ``team_id`` so a student on several teams
    resolves to the snapshot for THIS team. On the rare tie (two snapshots
    sharing the max ``computed_at``) the row returned last wins.
    """
    if not student_ids:
        return {}

    latest_sq = (
        select(
            MetricSnapshot.student_id,
            func.max(MetricSnapshot.computed_at).label("max_at"),
        )
        .where(
            MetricSnapshot.student_id.in_(student_ids),
            MetricSnapshot.team_id == team_id,
        )
        .group_by(MetricSnapshot.student_id)
        .subquery()
    )
    stmt = select(MetricSnapshot).join(
        latest_sq,
        (MetricSnapshot.student_id == latest_sq.c.student_id)
        & (MetricSnapshot.computed_at == latest_sq.c.max_at)
        & (MetricSnapshot.team_id == team_id),
    )
    result = await db.execute(stmt)
    return {s.student_id: s for s in result.scalars().all()}


def latest_team_snapshot_subquery(course_ids: list[uuid.UUID]) -> Any:
    """Subquery of ``(team_id, max_at)``: latest snapshot time per team.

    Scoped to teams whose ``course_id`` is in ``course_ids``. Join a
    ``TeamMetricSnapshot`` back on ``team_id == team_id AND computed_at == max_at``
    to select each team's most-recent snapshot.
    """
    return (
        select(
            TeamMetricSnapshot.team_id,
            func.max(TeamMetricSnapshot.computed_at).label("max_at"),
        )
        .where(TeamMetricSnapshot.course_id.in_(course_ids))
        .group_by(TeamMetricSnapshot.team_id)
        .subquery()
    )


async def student_author_identifiers(
    db: AsyncSession,
    team_ids: list[uuid.UUID],
) -> tuple[set[str], set[str]]:
    """Return (lowercased names, lowercased emails) of student team members.

    Collects identifiers from ``TeamMember`` rows that are NOT teachers
    and NOT mentors, plus their ``Student.full_name`` / ``Student.email``.
    Also subtracts any ``excluded_contributor_names`` from the whitelist.
    """
    names: set[str] = set()
    emails: set[str] = set()

    if not team_ids:
        return names, emails

    from app.models.student import Student
    from app.models.team_member import TeamMember

    s_stmt = (
        select(Student.full_name, Student.email)
        .join(TeamMember, TeamMember.student_id == Student.id)
        .where(
            TeamMember.team_id.in_(team_ids),
            TeamMember.is_teacher.is_(False),
            or_(
                TeamMember.is_mentor.is_(False),
                TeamMember.is_mentor.is_(None),
            ),
        )
    )
    for row in (await db.execute(s_stmt)).all():
        if row.full_name:
            names.add(row.full_name.lower().strip())
        if row.email and row.email.lower().strip() != "private":
            emails.add(row.email.lower().strip())

    # Remove any excluded contributor names from the whitelist
    from app.config import get_settings

    for name in get_settings().excluded_contributor_names:
        if name:
            names.discard(name.lower().strip())

    return names, emails


def _student_whitelist_conditions(team_ids: list[uuid.UUID]) -> list[Any]:
    """The same whitelist :func:`student_author_identifiers` builds - as SQL.

    Built in Python, this filter was shipped back as two `IN` lists: ~900 bind
    parameters for a 459-member course, 20 129 characters of SQL, plus the
    round-trip that fetched the names and emails in the first place. As a
    subquery it is 1 954 characters and one query fewer.

    Honest about the size of that win, because the first version of this comment
    was not. The contributor query was once measured at 2560ms of a 3588ms page
    and this shape was blamed for it. Measured again on an idle host, both forms
    are the same: 15.2ms as a subquery, 16.2ms as a bind list, 0.8ms planning
    either way. The 2560ms reading was taken while a deploy was rebuilding
    container images on the same four cores - that was the actual cause of the
    slow pages, and it is fixed in redeploy.py. This form is kept because a 2KB
    statement and one fewer round-trip are better than a 20KB statement and two,
    not because it made anything ten times faster.

    Every rule the Python version applies is applied here, in the same order:
    members that are neither teachers nor mentors, names and emails lowercased
    and trimmed, the literal "private" email skipped, and the configured
    excluded contributors removed from the NAME half only - an excluded name
    whose email is on the roster still counts, exactly as before.
    """
    from app.config import get_settings
    from app.models.student import Student
    from app.models.team_member import TeamMember

    def _members(column: Any) -> Any:
        return (
            select(column)
            .join(TeamMember, TeamMember.student_id == Student.id)
            .where(
                TeamMember.team_id.in_(team_ids),
                TeamMember.is_teacher.is_(False),
                or_(
                    TeamMember.is_mentor.is_(False),
                    TeamMember.is_mentor.is_(None),
                ),
            )
        )

    names_q = _members(func.lower(func.trim(Student.full_name))).where(
        Student.full_name.is_not(None)
    )
    emails_q = _members(func.lower(func.trim(Student.email))).where(
        Student.email.is_not(None),
        func.lower(func.trim(Student.email)) != "private",
    )

    name_match: Any = func.lower(Commit.author_name).in_(names_q)
    excluded = [n.lower().strip() for n in get_settings().excluded_contributor_names if n]
    if excluded:
        name_match = and_(name_match, func.lower(Commit.author_name).notin_(excluded))
    return [or_(name_match, func.lower(Commit.author_email).in_(emails_q))]


def _student_inclusion_conditions(
    student_names: set[str],
    student_emails: set[str],
) -> list[Any]:
    """Build SQLAlchemy WHERE clauses that include only student commits.

    The set-based form, for callers that already hold the identifiers (a single
    group, where the list is short). The whole-course path uses
    :func:`_student_whitelist_conditions` instead - see the measurement there.
    """
    if not student_names and not student_emails:
        # No known students - exclude everything
        return [Commit.id.is_(None)]

    parts: list[Any] = []
    if student_names:
        parts.append(func.lower(Commit.author_name).in_(student_names))
    if student_emails:
        parts.append(func.lower(Commit.author_email).in_(student_emails))
    return [or_(*parts)]


def _inclusion(
    team_ids: list[uuid.UUID],
    whitelist_team_ids: list[uuid.UUID] | None,
    student_names: set[str] | None,
    student_emails: set[str] | None,
) -> list[Any]:
    """Sets if the caller brought them, SQL otherwise."""
    if student_names is not None and student_emails is not None:
        return _student_inclusion_conditions(student_names, student_emails)
    return _student_whitelist_conditions(whitelist_team_ids or team_ids)


async def team_contributor_counts(
    db: AsyncSession,
    team_ids: list[uuid.UUID],
    *,
    student_names: set[str] | None = None,
    student_emails: set[str] | None = None,
    whitelist_team_ids: list[uuid.UUID] | None = None,
    commit_since: datetime | None = None,
) -> dict[uuid.UUID, int]:
    """Distinct commit-author emails per team (whitelist-filtered).

    When ``commit_since`` is provided, only commits with
    ``committed_at >= commit_since`` are counted -- this restricts the
    contributor count to the **current semester** so prior-semester
    activity does not inflate the headline number.
    """
    if not team_ids:
        return {}

    conditions = [
        GitLabProject.team_id.in_(team_ids),
        Commit.author_email.is_not(None),
        *_inclusion(team_ids, whitelist_team_ids, student_names, student_emails),
    ]
    if commit_since is not None:
        conditions.append(Commit.committed_at >= commit_since)
    stmt = (
        select(
            GitLabProject.team_id,
            func.count(func.distinct(Commit.author_email)).label("cnt"),
        )
        .join(Commit, Commit.project_id == GitLabProject.id)
        .where(*conditions)
        .group_by(GitLabProject.team_id)
    )
    result = await db.execute(stmt)
    return dict(result.all())  # type: ignore[arg-type]


async def total_distinct_contributors(
    db: AsyncSession,
    team_ids: list[uuid.UUID],
    *,
    student_names: set[str] | None = None,
    student_emails: set[str] | None = None,
    whitelist_team_ids: list[uuid.UUID] | None = None,
    commit_since: datetime | None = None,
) -> int:
    """Distinct commit-author emails across all given teams (whitelist-filtered).

    Optionally restricted to ``committed_at >= commit_since`` (current
    semester) to match :func:`team_contributor_counts`.
    """
    if not team_ids:
        return 0

    conditions = [
        GitLabProject.team_id.in_(team_ids),
        Commit.author_email.is_not(None),
        *_inclusion(team_ids, whitelist_team_ids, student_names, student_emails),
    ]
    if commit_since is not None:
        conditions.append(Commit.committed_at >= commit_since)
    stmt = (
        select(func.count(func.distinct(Commit.author_email)))
        .join(GitLabProject, GitLabProject.id == Commit.project_id)
        .where(*conditions)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0

"""Resolving which academic period a page is scoped to, against the database.

:mod:`app.utils.academic_period` names and orders a period without knowing what
is in the database. This is the half that does: which periods hold courses,
which one a page should open on, and which people belong to one.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy import ColumnElement, Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.utils.academic_period import (
    AcademicPeriod,
    calendar_period,
    calendar_periods,
    in_session,
    merge_periods,
    parse_key,
)

#: The value that means "do not narrow by period at all".
ALL_PERIODS = "all"

#: The value for people who belong to no course in any period. Without a view
#: of its own they would be invisible in every period, and an admin looking for
#: the student who just signed in through GitLab - the one case where finding
#: them matters most - would not find them anywhere.
NO_PERIOD = "none"

#: Where a reader's pick is remembered between visits - in localStorage, like
#: the interface language, and mirrored into this cookie so the server can
#: draw the page already scoped instead of drawing the default and jumping.
#: The value is "<picked key>~<calendar term when picked>".
PERIOD_COOKIE = "gp_period"


def requested_period(request: Request) -> str | None:
    """The period a page was asked for: the address first, then the reader's
    remembered pick.

    A remembered pick lapses when the calendar moves to a new term: it was a
    choice about the term that was running then, and a reader coming back in
    the next term means the new one - the stale year is exactly what nobody
    wants to land on. A link that names a period (a shared URL, a card that
    points at its term) always wins and does not overwrite the pick.
    """
    value = (request.query_params.get("period") or "").strip()
    if value:
        return value
    # Preferences > Behavior > "Default period" (set on request.state by the
    # dashboard auth dependencies). Only "remembered" consults the pick.
    default = getattr(request.state, "default_period", "remembered")
    if default == "current":
        return calendar_period().key
    if default == "all":
        return ALL_PERIODS
    if default == "newest":
        return None
    raw = (request.cookies.get(PERIOD_COOKIE) or "").strip()
    key, _, picked_during = raw.partition("~")
    if key and picked_during == calendar_period().key:
        return key
    return None


async def periods_with_courses(db: AsyncSession) -> list[AcademicPeriod]:
    """The distinct periods that actually hold a course, newest first."""
    rows = await db.execute(select(Course.academic_year, Course.semester).distinct())
    found: list[AcademicPeriod] = []
    for academic_year, semester in rows.all():
        try:
            found.append(AcademicPeriod(academic_year=academic_year, semester=semester))
        except ValueError:
            # A course row with a semester outside the vocabulary (hand-edited,
            # or imported before the field was constrained) must not take the
            # whole page down with it.
            continue
    return sorted(found, key=lambda p: p.sort_key, reverse=True)


def periods_of(courses: Iterable[Course]) -> list[AcademicPeriod]:
    """The distinct periods of a set of courses the caller has already loaded.

    For pages whose reader does not see every course - a student sees their
    own, a teacher the ones they teach. Their default and their "has courses"
    marks must come from THAT set: taken from the whole database, a student
    whose only course is 2025/2026 summer would open their dashboard on
    whichever newer term another course happens to be in, and see nothing.
    """
    found: set[AcademicPeriod] = set()
    for course in courses:
        try:
            found.add(AcademicPeriod(course.academic_year, course.semester))
        except ValueError:
            continue
    return sorted(found, key=lambda p: p.sort_key, reverse=True)


async def period_options(
    db: AsyncSession,
    today: date | None = None,
    *,
    present: list[AcademicPeriod] | None = None,
) -> list[AcademicPeriod]:
    """Every period worth offering: the TUKE calendar's, plus any in the data.

    Both terms of every year are listed even when one of them holds nothing, so
    an empty winter is selectable and visibly empty rather than missing.
    ``present`` narrows "the data" to what this reader can see.
    """
    found = present if present is not None else await periods_with_courses(db)
    return merge_periods(calendar_periods(today), found)


async def default_period(
    db: AsyncSession,
    today: date | None = None,
    *,
    present: list[AcademicPeriod] | None = None,
) -> AcademicPeriod:
    """The period a page opens on.

    The newest one that actually holds courses - not the calendar's current
    one. They are often not the same: a deployment running only summer courses
    is in "winter" for half the year by the calendar, and opening every page on
    an empty table would be technically right and useless. The calendar's
    answer is still shown, as the "Current" mark next to whichever option it
    is, so the difference is visible rather than hidden.

    ``present`` makes it the newest period of the courses THIS reader can see;
    see :func:`periods_of` for why that matters.
    """
    found = present if present is not None else await periods_with_courses(db)
    return found[0] if found else calendar_period(today)


async def resolve_period(
    db: AsyncSession,
    requested: str | None,
    today: date | None = None,
    *,
    present: list[AcademicPeriod] | None = None,
    include_none: bool = True,
) -> tuple[str, AcademicPeriod | None, list[AcademicPeriod]]:
    """Turn a query-string value into the scope a page should render.

    Returns ``(selected_key, period, options)`` where ``selected_key`` is one of
    a period key, :data:`ALL_PERIODS` or :data:`NO_PERIOD`, and ``period`` is
    the parsed period or ``None`` for the two special scopes. An unparseable or
    unknown value falls back to the default rather than erroring: the value
    arrives from a URL that anyone can edit.
    """
    options = await period_options(db, today, present=present)
    raw = (requested or "").strip()

    if raw == ALL_PERIODS:
        return ALL_PERIODS, None, options
    # "No period" only exists where it can match something (people, not
    # courses). Asked for elsewhere - a pick remembered from User Management,
    # carried to the Dashboard - it means "no choice", not "show everything
    # under a label that says nothing".
    if raw == NO_PERIOD and include_none:
        return NO_PERIOD, None, options

    parsed = parse_key(raw)
    if parsed is not None:
        # Accept a period the options list does not have rather than silently
        # redirecting: a deep link to an old cohort still has to work, and the
        # option is added so the selector can show what it is showing.
        if parsed not in options:
            options = merge_periods(options, [parsed])
        return parsed.key, parsed, options

    fallback = await default_period(db, today, present=present)
    if fallback not in options:
        options = merge_periods(options, [fallback])
    return fallback.key, fallback, options


def _student_name_match() -> ColumnElement[bool]:
    """How a ``User`` is matched to the ``Student`` row that holds their work.

    By USERNAME, which is what the app already does everywhere it asks this
    question - the User Info modal, the student page, the enrichment pass. Not
    by ``gitlab_user_id``: both tables carry one, but they come from different
    places (OAuth for the user, the GitLab members API for the student) and in
    practice they do not line up, so an id join silently matches nobody.

    Written once here so the table, the row badges and the modal cannot drift
    into three different answers about who belongs where.
    """
    return or_(
        and_(User.gitlab_username.is_not(None), Student.gitlab_username == User.gitlab_username),
        Student.gitlab_username == User.username,
    )


def _belongs_to_period(period: AcademicPeriod) -> ColumnElement[bool]:
    """True when this user reaches a course in ``period`` by either route.

    There are two, and both are real:

    * ``CourseMembership`` - how an owner or a teacher is attached to a course.
      The role column allows ``student`` too, but nothing creates those rows.
    * ``Team -> TeamMember -> Student`` - how a student actually reaches a
      course, because a student is a GitLab person synced into a team, not a
      row in ``course_memberships``. Only ACTIVE team memberships count: a
      student who left the group belongs to the course's past, not its cohort.
    """
    by_membership = (
        select(CourseMembership.id)
        .join(Course, Course.id == CourseMembership.course_id)
        .where(
            CourseMembership.user_id == User.id,
            Course.academic_year == period.academic_year,
            Course.semester == period.semester,
        )
        .exists()
    )
    by_team = (
        select(TeamMember.team_id)
        .join(Student, Student.id == TeamMember.student_id)
        .join(Team, Team.id == TeamMember.team_id)
        .join(Course, Course.id == Team.course_id)
        .where(
            TeamMember.is_active.is_(True),
            _student_name_match(),
            Course.academic_year == period.academic_year,
            Course.semester == period.semester,
        )
        .exists()
    )
    return or_(by_membership, by_team)


def _reaches_courses(course_ids: list[uuid.UUID]) -> ColumnElement[bool]:
    """True when this user reaches one of these courses, by either route.

    :func:`_belongs_to_period` narrowed to a set of courses instead of a whole
    period - for a reader who does not see every course of the period (a
    teacher sees the ones they teach).
    """
    by_membership = (
        select(CourseMembership.id)
        .where(CourseMembership.user_id == User.id, CourseMembership.course_id.in_(course_ids))
        .exists()
    )
    by_team = (
        select(TeamMember.team_id)
        .join(Student, Student.id == TeamMember.student_id)
        .join(Team, Team.id == TeamMember.team_id)
        .where(
            TeamMember.is_active.is_(True),
            _student_name_match(),
            Team.course_id.in_(course_ids),
        )
        .exists()
    )
    return or_(by_membership, by_team)


async def count_students(db: AsyncSession, course_ids: list[uuid.UUID] | None) -> int:
    """Active student accounts - all of them, or those in these courses.

    What the Dashboard's "Students" card counts. It used to count every student
    account in the installation for everybody: a teacher saw the size of the
    whole university under their own two courses, and a Dashboard scoped to one
    term showed a figure from all of them beside cards from that one. Counted
    through the same routes the period scope uses, the card and the User
    Management page it links to agree on the number.
    """
    stmt = select(func.count(User.id)).where(
        User.role == "student", User.is_active.is_(True), User.is_bot.is_(False)
    )
    if course_ids is not None:
        if not course_ids:
            return 0
        stmt = stmt.where(_reaches_courses(course_ids))
    return int((await db.execute(stmt)).scalar() or 0)


def _belongs_to_any_period() -> ColumnElement[bool]:
    """True when this user reaches any course at all, by either route."""
    by_membership = select(CourseMembership.id).where(CourseMembership.user_id == User.id).exists()
    by_team = (
        select(TeamMember.team_id)
        .join(Student, Student.id == TeamMember.student_id)
        .where(TeamMember.is_active.is_(True), _student_name_match())
        .exists()
    )
    return or_(by_membership, by_team)


def scope_students_to_period(
    stmt: Select[tuple[User]], period: AcademicPeriod | None, *, scope: str
) -> Select[tuple[User]]:
    """Narrow a ``User`` query to one period - for STUDENTS only.

    A period is a property of a course, so it can only reach a person through
    the courses they are in. Admins and teachers are not cohort-bound: an admin
    belongs to no course at all, and a teacher who happens to teach nothing
    this term is still the person you open User Management to find. Narrowing
    them would make the page lose the very people who administer it, so only
    rows whose role is ``student`` are filtered.
    """
    if scope == ALL_PERIODS:
        return stmt

    if scope == NO_PERIOD:
        # Students who reach no course at all - the one who signed in through
        # GitLab this morning and has not been synced into a group yet. Without
        # a view of their own they would be invisible in every period, which is
        # exactly when an admin needs to find them.
        return stmt.where(User.role == "student", ~_belongs_to_any_period())

    if period is None:
        return stmt

    return stmt.where(or_(User.role != "student", _belongs_to_period(period)))


async def periods_for_users(
    db: AsyncSession, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[AcademicPeriod]]:
    """Which periods each of these users belongs to, for the row badges.

    Two queries for the whole page rather than two per row: the badge is on
    every student in a table that can hold thousands, and the team route needs
    a join the membership route does not.
    """
    if not user_ids:
        return {}

    found: dict[uuid.UUID, set[AcademicPeriod]] = {}

    def _collect(user_id: uuid.UUID, academic_year: str, semester: str) -> None:
        try:
            period = AcademicPeriod(academic_year=academic_year, semester=semester)
        except ValueError:
            # A course whose semester is outside the vocabulary must not take
            # the whole table's badges down with it.
            return
        found.setdefault(user_id, set()).add(period)

    by_membership = await db.execute(
        select(CourseMembership.user_id, Course.academic_year, Course.semester)
        .join(Course, Course.id == CourseMembership.course_id)
        .where(CourseMembership.user_id.in_(user_ids))
        .distinct()
    )
    for user_id, academic_year, semester in by_membership.all():
        _collect(user_id, academic_year, semester)

    by_team = await db.execute(
        select(User.id, Course.academic_year, Course.semester)
        .join(Student, _student_name_match())
        .join(TeamMember, TeamMember.student_id == Student.id)
        .join(Team, Team.id == TeamMember.team_id)
        .join(Course, Course.id == Team.course_id)
        .where(User.id.in_(user_ids), TeamMember.is_active.is_(True))
        .distinct()
    )
    for user_id, academic_year, semester in by_team.all():
        _collect(user_id, academic_year, semester)

    return {
        uid: sorted(periods, key=lambda p: p.sort_key, reverse=True)
        for uid, periods in found.items()
    }


async def period_scope_context(
    db: AsyncSession,
    requested: str | None,
    *,
    today: date | None = None,
    include_none: bool = True,
    visible_courses: Iterable[Course] | None = None,
) -> dict[str, object]:
    """Everything a page needs to draw the period selector and scope itself.

    The facts are settled here, in Python, where they can be tested; the
    template only puts words around them. ``semester`` is handed over raw so
    the macro can translate it - a label built here would be built in whatever
    language the worker happened to start in.

    ``include_none`` is off for pages that list COURSES rather than people: a
    course always has a period, so "no period" would be an option that can
    never match anything.

    ``visible_courses`` is the set the reader can actually see, for pages that
    do not show everyone everything. Both the default and the "No courses"
    marks are then computed from it - see :func:`periods_of`.
    """
    visible = periods_of(visible_courses) if visible_courses is not None else None
    selected_key, period, options = await resolve_period(
        db, requested, today, present=visible, include_none=include_none
    )
    present = {p.key for p in (visible if visible is not None else await periods_with_courses(db))}
    marker, running = current_marker(today)
    # Did the READER pick this period, or did the page pick it for them? A
    # course created while looking at a term someone chose belongs in that
    # term; a course created on a page that merely opened on last summer (its
    # newest term with data) belongs in the term the calendar is in.
    explicit = selected_key in (ALL_PERIODS, NO_PERIOD) or parse_key(requested) is not None

    return {
        "param": "period",
        "all_key": ALL_PERIODS,
        "none_key": NO_PERIOD,
        "include_none": include_none,
        "explicit": explicit,
        "selected_key": selected_key,
        "selected": None
        if period is None
        else {"academic_year": period.academic_year, "semester": period.semester},
        "current_key": marker.key,
        "current_is_running": running,
        "options": [
            {
                "key": p.key,
                "academic_year": p.academic_year,
                "semester": p.semester,
                "is_current": p.key == marker.key,
                "has_courses": p.key in present,
            }
            for p in options
        ],
    }


def courses_in_scope(courses: Iterable[Course], scope: dict[str, object]) -> list[Course]:
    """The courses a scoped page shows, from a context built by
    :func:`period_scope_context`.

    ONE implementation, because a page and its live refresh must build the same
    list: the dashboard's "needs attention" card is re-fetched on every tab
    focus and sync completion, and a refresh that scoped differently from the
    page load changed the card under the reader - the exact failure the
    attention handler's own comments record twice.
    """
    selected = scope.get("selected")
    if scope.get("selected_key") == ALL_PERIODS or not isinstance(selected, dict):
        return list(courses)
    return [
        c
        for c in courses
        if c.academic_year == selected.get("academic_year")
        and c.semester == selected.get("semester")
    ]


def current_marker(today: date | None = None) -> tuple[AcademicPeriod, bool]:
    """The period to mark in the selector, and whether it has actually started.

    ``(period, True)`` while a semester is running; ``(period, False)`` in the
    gap before one starts, so the selector can say "Upcoming" instead of
    calling a term that begins in three weeks the current one.
    """
    running = in_session(today)
    if running is not None:
        return running, True
    return calendar_period(today), False


__all__ = [
    "ALL_PERIODS",
    "NO_PERIOD",
    "PERIOD_COOKIE",
    "count_students",
    "courses_in_scope",
    "current_marker",
    "default_period",
    "period_options",
    "period_scope_context",
    "periods_for_users",
    "periods_of",
    "periods_with_courses",
    "requested_period",
    "resolve_period",
    "scope_students_to_period",
]

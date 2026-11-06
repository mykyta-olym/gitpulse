"""Build role-filtered 'items that need your attention' for dashboard.

One function per kind of item, each returning the items it found; the builder
at the bottom says who sees which, in the order they are listed before the
severity sort.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select

from app.api.dashboard._access import _staff_course_ids
from app.api.dashboard._helpers import (
    _student_match_condition,
    course_settings_for,
    logger,
)
from app.api.dashboard.home.stats import _count_red_teams_per_course, _red_team_ids
from app.dependencies import DbSession
from app.i18n import translate_text
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.support_ticket import SupportTicket
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.webhook_event import WebhookEvent

Item = dict[str, Any]


def _item(icon: str, severity: str, title: str, detail: str, url: str | None = None) -> Item:
    return {"icon": icon, "severity": severity, "title": title, "detail": detail, "url": url}


@dataclass(frozen=True)
class _Reader:
    """Who is reading, in which language, and the courses on screen."""

    role: str
    locale: str
    auth: dict[str, str]
    db: DbSession
    now: datetime
    active_ids: list[uuid.UUID]
    active_courses: list[Course]

    @property
    def first_cid(self) -> str | None:
        """The first active course, for the items that link to "a course"."""
        return str(self.active_ids[0]) if self.active_ids else None

    def t(self, s: str) -> str:
        return translate_text(self.locale, s)

    def course_with_term(self, course: Any) -> str:
        """A course named WITH its term, for the items that look past the term
        on screen (onboarding, lifecycle): "ZSI" is every year's ZSI, and the
        item is about one of them."""
        code = str(getattr(course, "code", "") or getattr(course, "name", "") or course.id)
        year = getattr(course, "academic_year", None)
        if not year:
            return code
        term = self.t("Winter") if getattr(course, "semester", "") == "winter" else self.t("Summer")
        return f"{code} ({year} · {term})"


def _courses_page_for(courses: list[Any]) -> str:
    """Course Management opened ON these courses: their term (or every
    term, when they span several) and the Archived filter set - not the
    bare list, which opens on whatever term the reader last picked and may
    not hold them at all."""
    keys = {
        f"{getattr(c, 'academic_year', '')}-{getattr(c, 'semester', '')}".replace("/", "-")
        for c in courses
    }
    period = keys.pop() if len(keys) == 1 else "all"
    return f"/dashboard/admin/courses?period={period}&status=archived"


async def _count(db: DbSession, stmt: Any) -> int:
    return (await db.execute(stmt)).scalar() or 0


# -- Onboarding ---------------------------------------------------------------


def _onboarding(r: _Reader, archived: list[Course]) -> list[Item]:
    """The reader has no active course in ANY period."""
    t = r.t
    if r.role == "student":
        return [
            _item(
                "info",
                "info",
                t("Not enrolled yet"),
                t("You are not enrolled in any courses. Your teacher will add you soon."),
            )
        ]
    if r.role not in ("admin", "teacher"):
        return []
    if not archived:
        return [
            _item(
                "plus-circle",
                "info",
                t("Create your first course"),
                t("Get started by creating a new course or importing one from GitLab."),
                "/dashboard/admin/courses",
            )
        ]
    # The account has archived courses (e.g. auto-archived at semester end) -
    # so "create your first course" is misleading and its link dead-ended on
    # the course list. Offer to reactivate / roll one into the new term
    # instead; /dashboard/admin/courses is where archived courses expose their
    # Activate button.
    if len(archived) == 1:
        title = f"{r.course_with_term(archived[0])} — " + t("archived, reactivate for the new term")
    else:
        title = f"{len(archived)} " + t("archived courses, reactivate one for the new term")
    return [
        _item(
            "rotate-ccw",
            "info",
            title,
            t(
                "All your courses are archived. Reactivate one to reconfigure its "
                "semester dates and schedule for the new term, or create a new course."
            ),
            _courses_page_for(archived),
        )
    ]


# -- Staff: GitLab, sync and jobs ---------------------------------------------


def _gitlab_token(r: _Reader) -> list[Item]:
    """Read the SHARED cached health flag - NO live probe here: the dashboard
    must never hit the GitLab API on render (data reaches GitPulse only via
    sync + webhooks). A dead token blocks every sync/import, so surface it
    first with a link to where it is configured."""
    from app.services.gitlab.token_health import cached_status

    if cached_status() != "unauthorized":
        return []
    return [
        _item(
            "alert-circle",
            "danger",
            r.t("GitLab token invalid"),
            r.t(
                "The GitLab API token is invalid or expired (401). Sync, import and "
                "other GitLab actions are blocked until the token is updated."
            ),
            # The token is an env var, not an in-app setting, so link to the
            # docs that explain how to rotate it - not System Settings.
            "/docs/en/gitlab/tokeny/" if r.locale == "en" else "/docs/gitlab/tokeny/",
        )
    ]


def _pending_syncs(r: _Reader, course_sync_info: dict[uuid.UUID, dict[str, int]]) -> list[Item]:
    pending = sum(
        info.get("running", 0) + info.get("queued", 0) for info in course_sync_info.values()
    )
    if pending <= 0:
        return []
    return [
        _item(
            "refresh-cw",
            "warning",
            f"{pending} {r.t('sync jobs pending')}",
            r.t("Some groups are waiting for data synchronization."),
            "/dashboard/admin/system",
        )
    ]


async def _failed_jobs(r: _Reader) -> list[Item]:
    """Background jobs that failed in the last 7 days."""
    failed = await _count(
        r.db,
        select(func.count(BackgroundJob.id)).where(
            BackgroundJob.status == "failed",
            BackgroundJob.enqueued_at >= r.now - timedelta(days=7),
        ),
    )
    if failed <= 0:
        return []
    return [
        _item(
            "x-circle",
            "danger",
            f"{failed} {r.t('failed background jobs')}",
            r.t("Jobs failed in the last 7 days. Check system status for details."),
            "/dashboard/admin/system",
        )
    ]


# -- Staff: the courses on screen ---------------------------------------------


async def _red_teams(r: _Reader, red_teams_count: int | None) -> list[Item]:
    """Groups at a RED traffic light."""
    red_per_course = await _count_red_teams_per_course(r.active_ids, r.db)
    total_red = sum(red_per_course.values())
    # The cached total, when the per-course count came back empty.
    if red_teams_count is not None and total_red == 0 and red_teams_count > 0:
        total_red = red_teams_count
    if total_red <= 0:
        return []

    title_tail = r.t("groups at critical risk")
    courses_with_red = [cid for cid, cnt in red_per_course.items() if cnt > 0]
    if len(courses_with_red) > 1:
        # One item per course.
        names = {c.id: f"{c.code} - {c.name}" for c in r.active_courses}
        return [
            _item(
                "alert-triangle",
                "danger",
                f"{red_per_course[cid]} {title_tail}",
                names.get(cid, str(cid)),
                f"/dashboard/courses/{cid}?sort=status",
            )
            for cid in courses_with_red
        ]

    # Single course (or aggregate) - link directly. When exactly one group is
    # at risk, link straight to THAT group ("redirect exactly to the
    # element"); otherwise to the course sorted so at-risk groups float to the
    # top.
    target_cid = str(courses_with_red[0]) if courses_with_red else r.first_cid
    url = f"/dashboard/courses/{target_cid}?sort=status" if target_cid else None
    if total_red == 1:
        red = await _red_team_ids(r.active_ids, r.db)
        if len(red) == 1:
            url = f"/dashboard/teams/{red[0]}"
    return [
        _item(
            "alert-triangle",
            "danger",
            f"{total_red} {title_tail}",
            r.t("These groups have RED compliance status and need immediate attention."),
            url,
        )
    ]


async def _stale_projects(r: _Reader) -> list[Item]:
    """Projects pending a sync, grouped per course.

    Data freshness is webhook + manual-sync driven (there is no periodic sync
    sweep), so this is a per-course reminder of how many projects have not
    been synced in 7+ days. It is grouped by course and links straight to that
    course (where the sync action lives) instead of a single global "135
    stale" line pointing at the system page.
    """
    rows = await r.db.execute(
        select(Course.id, Course.code, func.count(GitLabProject.id))
        .select_from(GitLabProject)
        .join(Team, GitLabProject.team_id == Team.id)
        .join(Course, Team.course_id == Course.id)
        .where(
            Team.course_id.in_(r.active_ids),
            Team.is_active.is_(True),
            GitLabProject.is_active.is_(True),
            GitLabProject.last_synced_at < r.now - timedelta(days=7),
        )
        .group_by(Course.id, Course.code),
    )
    return [
        _item(
            "clock",
            "info",
            f"{code}: {cnt} {r.t('projects to sync')}",
            r.t("Not synced in 7+ days - open the course to trigger a sync."),
            f"/dashboard/courses/{cid}",
        )
        for cid, code, cnt in rows.all()
        if cnt and cnt > 0
    ]


async def _webhook_warnings(r: _Reader) -> list[Item]:
    """Courses without webhooks, and courses whose webhooks went silent."""
    from app.services.webhook_activity import compute_webhook_activity

    report = await compute_webhook_activity(r.db, r.active_ids, now=r.now)
    codes = {c.id: c.code for c in r.active_courses}

    def one_or_many(
        cids: list[uuid.UUID], icon: str, one_title: str, many_title: str, detail: str
    ) -> list[Item]:
        if not cids:
            return []
        url = f"/dashboard/courses/{cids[0]}/settings"
        if len(cids) > 1:
            return [_item(icon, "warning", f"{len(cids)} {many_title}", detail, url)]
        code = codes.get(cids[0], "")
        prefix = f"{code} - " if code else ""
        return [_item(icon, "warning", one_title, prefix + detail, url)]

    return [
        *one_or_many(
            [cid for cid in r.active_ids if cid not in report.configured],
            "link-2",
            r.t("Webhooks not configured"),
            r.t("courses without webhooks"),
            r.t("Data will not update automatically. Configure webhooks or sync manually."),
        ),
        # Configured but silent (the grace window excluded).
        *one_or_many(
            [cid for cid in r.active_ids if cid in report.silent],
            "alert-triangle",
            r.t("Webhooks may be inactive"),
            r.t("courses with inactive webhooks"),
            r.t("No webhook events received in 48h. Check GitLab webhook configuration."),
        ),
    ]


#: account.problems() code -> (icon, severity, title, detail). The details are
#: the Assistant page's own words; it says the same at its top.
_ASSISTANT_PROBLEMS: dict[str, tuple[str, str, str, str]] = {
    "token_rejected": (
        "alert-circle",
        "danger",
        "Assistant: GitLab refuses the bot token",
        "Until a new token is connected, the assistant does nothing.",
    ),
    "token_expired": (
        "alert-circle",
        "danger",
        "Assistant: the bot token has expired",
        "Until a new token is connected, the assistant does nothing.",
    ),
    "no_bot": (
        "bot",
        "warning",
        "Assistant: no bot is connected",
        "Tools are on, but without a bot account the assistant cannot act. Connect a token first.",
    ),
    "token_expiring": (
        "clock",
        "warning",
        "Assistant: the bot token expires soon",
        "Replace it on the Assistant page before it expires, or the assistant stops.",
    ),
    "run_stale": (
        "alert-triangle",
        "warning",
        "Assistant: the exercise was not prepared",
        "Prepare the exercise again - students who already have their issue are skipped.",
    ),
}
#: How far back an action GitLab refused still needs a look.
_ASSISTANT_REFUSED_WINDOW = timedelta(days=7)


async def _assistant_warnings(r: _Reader) -> list[Item]:
    """What keeps a course's classroom assistant from acting - the answer its
    page gives (account.problems) - and the actions GitLab refused it lately.
    A missing webhook is not repeated here: `_webhook_warnings` says it."""
    from app.config import get_settings
    from app.models.assistant import AssistantTask, CourseAssistant
    from app.services.assistant import account
    from app.services.assistant.tasks import FAILED

    if not get_settings().feature_classroom_assistant:
        return []
    # Only the courses the reader runs: the items lead to the Assistant page,
    # which a teacher who merely sees a course cannot open.
    runs = await _staff_course_ids(r.db, list(r.active_ids), r.auth)
    if not runs:
        return []
    assistants = (
        (await r.db.execute(select(CourseAssistant).where(CourseAssistant.course_id.in_(runs))))
        .scalars()
        .all()
    )
    if not assistants:
        return []
    refused = dict(
        (
            await r.db.execute(
                select(AssistantTask.course_id, func.count())
                .where(
                    AssistantTask.course_id.in_(runs),
                    AssistantTask.state == FAILED,
                    AssistantTask.updated_at >= r.now - _ASSISTANT_REFUSED_WINDOW,
                )
                .group_by(AssistantTask.course_id)
            )
        )
        .tuples()
        .all()
    )
    codes = {c.id: c.code for c in r.active_courses}
    items: list[Item] = []
    for assistant in assistants:
        url = f"/dashboard/courses/{assistant.course_id}/assistant"
        code = codes.get(assistant.course_id, "")
        prefix = f"{code} - " if code else ""
        for problem in account.problems(assistant):
            icon, severity, title, detail = _ASSISTANT_PROBLEMS[problem]
            items.append(_item(icon, severity, r.t(title), prefix + r.t(detail), url))
        count = refused.get(assistant.course_id, 0)
        if count:
            items.append(
                _item(
                    "alert-triangle",
                    "warning",
                    r.t("Assistant: GitLab refused some of its actions"),
                    f"{prefix}{r.t('In the last 7 days:')} {count}. "
                    + r.t("The reason is in the Last action column of the Assistant page."),
                    url,
                )
            )
    return items


async def _deadlines(r: _Reader) -> list[Item]:
    """An MR-creation or merge deadline in the next three days - one per course."""
    lookup_r = await r.db.execute(
        select(Course.id, Course.code, Course.name).where(Course.id.in_(r.active_ids)),
    )
    lookup = {cid: (code or "", name or "") for cid, code, name in lookup_r.all()}
    now = r.now
    items: list[Item] = []
    for cs in (await course_settings_for(r.db, r.active_ids)).values():
        for field, label in (
            ("mr_creation_deadline", "MR creation deadline"),
            ("merge_deadline", "Merge deadline"),
        ):
            due = getattr(cs, field, None)
            if due and due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            if not (due and now < due < now + timedelta(days=3)):
                continue
            code, name = lookup.get(cs.course_id, ("", ""))
            title = f"{r.t(label)} {r.t('approaching')}"
            if code or name:
                title = f"{code or name} — {title}"
            remaining = due - now
            if remaining.days < 1:
                hours = max(int(remaining.total_seconds()) // 3600, 1)
                detail = f"Due in {hours} hour{'s' if hours != 1 else ''}."
            else:
                detail = f"Due in {remaining.days} day{'s' if remaining.days != 1 else ''}."
            items.append(
                _item(
                    "calendar",
                    "warning",
                    title,
                    detail,
                    f"/dashboard/courses/{cs.course_id}/settings",
                )
            )
            break  # one warning per course is enough
    return items


async def _dead_letters(r: _Reader) -> list[Item]:
    """Webhook events that failed processing (admin only)."""
    try:
        dead = await _count(
            r.db,
            select(func.count(WebhookEvent.id)).where(WebhookEvent.dead_letter_at.is_not(None)),
        )
    except Exception:
        logger.debug("webhook_events query skipped")
        return []
    if dead <= 0:
        return []
    return [
        _item(
            "mail",
            "danger",
            f"{dead} {r.t('dead-letter webhooks')}",
            r.t("Webhook events that failed processing. Review in system admin."),
            "/dashboard/admin/events",
        )
    ]


async def _empty_courses(r: _Reader) -> list[Item]:
    """Courses with no groups."""
    try:
        with_teams = (
            select(func.distinct(Team.course_id)).where(
                Team.course_id.in_(r.active_ids),
                Team.is_active.is_(True),
            )
        ).subquery()
        empty = await _count(
            r.db,
            select(func.count(Course.id)).where(
                Course.id.in_(r.active_ids),
                Course.id.notin_(select(with_teams)),
            ),
        )
    except Exception:
        logger.debug("empty courses query skipped")
        return []
    if empty <= 0:
        return []
    return [
        _item(
            "users",
            "info",
            f"{empty} {r.t('courses without groups')}",
            r.t("Import groups from GitLab or create them manually to start tracking."),
            f"/dashboard/courses/{r.first_cid}" if r.first_cid else None,
        )
    ]


async def _empty_teams(r: _Reader) -> list[Item]:
    """Groups with no members."""
    try:
        with_members = (
            select(func.distinct(TeamMember.team_id))
            .join(Team, TeamMember.team_id == Team.id)
            .where(Team.course_id.in_(r.active_ids), Team.is_active.is_(True))
        ).subquery()
        empty = await _count(
            r.db,
            select(func.count(Team.id)).where(
                Team.course_id.in_(r.active_ids),
                Team.is_active.is_(True),
                Team.id.notin_(select(with_members)),
            ),
        )
    except Exception:
        logger.debug("empty teams query skipped")
        return []
    if empty <= 0:
        return []
    return [
        _item(
            "user-minus",
            "warning",
            f"{empty} {r.t('groups without members')}",
            r.t("These groups have no students assigned. Sync from GitLab or add manually."),
            f"/dashboard/courses/{r.first_cid}" if r.first_cid else None,
        )
    ]


async def _never_synced(r: _Reader) -> list[Item]:
    try:
        never = await _count(
            r.db,
            select(func.count(GitLabProject.id))
            .select_from(GitLabProject)
            .join(Team, GitLabProject.team_id == Team.id)
            .where(
                Team.course_id.in_(r.active_ids),
                Team.is_active.is_(True),
                GitLabProject.is_active.is_(True),
                GitLabProject.last_synced_at.is_(None),
            ),
        )
    except Exception:
        logger.debug("never synced query skipped")
        return []
    if never <= 0:
        return []
    return [
        _item(
            "upload",
            "info",
            f"{never} {r.t('projects never synced')}",
            r.t("These projects have never been synced. Trigger a sync to pull data."),
            "/dashboard/admin/system",
        )
    ]


async def _support_tickets(r: _Reader) -> list[Item]:
    """Open tickets assigned to the reader, unassigned, and high-priority."""
    username = r.auth.get("gitlab_username") or r.auth.get("user", "")
    try:
        # Three panels, one set of open tickets, read once and split here. 200
        # open tickets across a user's active courses is far beyond anything
        # the pilot produces; each panel still counts at most five.
        open_tickets = (
            await r.db.execute(
                select(
                    SupportTicket.id,
                    SupportTicket.assigned_to,
                    SupportTicket.priority,
                    SupportTicket.course_id,
                    SupportTicket.status,
                )
                .where(
                    SupportTicket.status.in_(["open", "in_progress"]),
                    SupportTicket.course_id.in_(r.active_ids),
                )
                .limit(200),
            )
        ).all()
    except Exception:
        logger.debug("support ticket attention query skipped")
        return []

    def _tickets_url(tickets: list[Any]) -> str:
        """Where a count of tickets opens: the one ticket; the list of
        the one course they are in, with its Status filter set when they
        are all simply open; or the overview across every term when they
        span courses. The overview has no ticket status - it lists
        courses - so the old `?status=open` there filtered nothing."""
        if len(tickets) == 1:
            return f"/dashboard/support/ticket/{tickets[0].id}"
        courses = {t.course_id for t in tickets}
        if len(courses) == 1:
            url = f"/dashboard/support/tickets?course_id={next(iter(courses))}"
            if all(t.status == "open" for t in tickets):
                url += "&status=open"
            return url
        return "/dashboard/support/tickets?period=all"

    panels = (
        (
            [t for t in open_tickets if t.assigned_to == username],
            "inbox",
            "warning",
            r.t("support tickets assigned to you"),
            r.t("You have open support tickets awaiting your response."),
        ),
        (
            [t for t in open_tickets if t.assigned_to is None],
            "life-buoy",
            "info",
            r.t("unassigned support tickets"),
            r.t("Support tickets waiting for someone to take ownership."),
        ),
        (
            [t for t in open_tickets if t.priority in ("critical", "high")],
            "alert-triangle",
            "danger",
            r.t("high-priority support tickets"),
            r.t("Critical or high-priority tickets need urgent attention."),
        ),
    )
    return [
        _item(icon, severity, f"{min(len(ts), 5)} {title}", detail, _tickets_url(ts))
        for ts, icon, severity, title, detail in panels
        if ts
    ]


# -- Staff: course lifecycle, across every period -----------------------------


def _lifecycle(
    r: _Reader,
    life_active: list[Course],
    life_archived: list[Course],
    settings_map: dict[uuid.UUID, CourseSettings],
) -> list[Item]:
    """Auto-archive, reactivation, deletion.

    A: semester ended, course still active and auto-archive WILL run - a
       heads-up. B: the same with skip_auto_archive set - archive manually.
    C: new academic year, a course archived from a previous one - transfer it.
    D: archived 2+ years ago - delete it. E: archived 1-2 years - a reminder.
    """
    from app.config import get_settings
    from app.utils.academic_period import AcademicPeriod, calendar_period
    from app.utils.semester import get_effective_semester_end, is_semester_over

    t = r.t
    s = get_settings()
    grace = int(getattr(s, "semester_grace_days", 14) or 14)
    weeks = int(getattr(s, "semester_default_length_weeks", 14) or 14)
    auto_enabled = bool(getattr(s, "semester_auto_archive_enabled", True))
    multi_tenant = bool(getattr(s, "feature_multi_tenant", False))
    today = r.now.date()
    # The term the calendar says is running (or about to) - the same answer
    # the top bar and the period selector give.
    current_ay = calendar_period(today).academic_year

    items: list[Item] = []
    cap = 3  # lifecycle items surfaced, so the widget does not overflow
    added = 0

    for c in life_active:
        if added >= cap:
            break
        cs = settings_map.get(c.id)
        if cs is None or not is_semester_over(cs, grace, weeks, today=today):
            continue
        tag = r.course_with_term(c)
        end = get_effective_semester_end(cs, weeks)
        end_str = end.isoformat() if end else t("recently")
        url = f"/dashboard/courses/{c.id}/settings#danger-zone"
        if getattr(cs, "skip_auto_archive", False):
            items.append(
                _item(
                    "archive",
                    "warning",
                    f"{tag} — " + t("academic year ended, archive recommended"),
                    t(
                        "Semester ended on {date}. Auto-archive is turned off for "
                        "this course - archive it manually from the course settings "
                        "to free up resources."
                    ).replace("{date}", end_str),
                    url,
                )
            )
        elif auto_enabled:
            items.append(
                _item(
                    "archive",
                    "info",
                    f"{tag} — " + t("academic year ended, auto-archiving"),
                    t(
                        "Semester ended on {date}. This course is being "
                        "auto-archived to free up resources; you can also archive it "
                        "now from the course settings."
                    ).replace("{date}", end_str),
                    url,
                )
            )
        added += 1

    two_years = r.now - timedelta(days=730)
    one_year = r.now - timedelta(days=365)
    recent = r.now - timedelta(days=180)
    delete_n = stale_n = reactivate_n = 0

    for c in life_archived:
        if added >= cap * 3:
            break
        archived_at = getattr(c, "archived_at", None)
        if archived_at is None:
            continue
        if archived_at.tzinfo is None:
            archived_at = archived_at.replace(tzinfo=UTC)
        tag = r.course_with_term(c)
        danger_zone = f"/dashboard/courses/{c.id}/settings#danger-zone"

        if archived_at < two_years and delete_n < 2:
            items.append(
                _item(
                    "trash-2",
                    "info",
                    f"{tag} — " + t("archived over 2 years ago"),
                    t(
                        "Consider deleting this course to free up storage. All "
                        "snapshots and metrics will be removed."
                    ),
                    danger_zone,
                )
            )
            delete_n += 1
            added += 1
            continue

        if two_years <= archived_at < one_year and stale_n < 1:
            items.append(
                _item(
                    "archive",
                    "info",
                    f"{tag} — " + t("archived for more than a year"),
                    t(
                        "Review whether you still need this course. It will be eligible "
                        "for deletion suggestions after 2 years."
                    ),
                    danger_zone,
                )
            )
            stale_n += 1
            added += 1
            continue

        if (
            archived_at >= recent
            and c.academic_year
            and c.academic_year != current_ay
            and reactivate_n < 2
        ):
            # The same term one year on - where a yearly course runs next, and
            # what the Transfer dialog pre-fills. Reactivating the old course
            # instead would keep its old period: the pages would file this
            # year's students under last year.
            try:
                nxt = AcademicPeriod(c.academic_year, c.semester).next_year()
                next_label = f"{nxt.academic_year} · " + (
                    t("Winter") if nxt.semester == "winter" else t("Summer")
                )
            except ValueError:
                next_label = current_ay
            if multi_tenant:
                detail = t(
                    "Transfer this course to {period}: its settings, checks and "
                    "groups carry over, the dates follow the new term, and last "
                    "year's history stays where it is."
                ).replace("{period}", next_label)
                url = f"/dashboard/courses/{c.id}/settings#transfer"
            else:
                detail = t(
                    "Create this course for {period}: a course belongs to one "
                    "academic period, so the new term gets a course of its own."
                ).replace("{period}", next_label)
                url = _courses_page_for([c])
            items.append(
                _item(
                    "rotate-ccw",
                    "info",
                    f"{tag} — " + t("new academic year started"),
                    detail,
                    url,
                )
            )
            reactivate_n += 1
            added += 1
    return items


# -- Students -----------------------------------------------------------------


async def _is_course_staff(r: _Reader) -> bool:
    """An owner or teacher of one of the courses (via CourseMembership) needs
    no group, so the group and role warnings are not theirs."""
    from app.models.course_membership import CourseMembership

    gitlab_username = r.auth.get("gitlab_username", "")
    username = r.auth.get("user", "")
    conds = []
    if gitlab_username:
        conds.append(User.gitlab_username == gitlab_username)
    if username and username != gitlab_username:
        conds.append(User.username == username)
    if not conds:
        return False
    try:
        uid = (await r.db.execute(select(User.id).where(or_(*conds)).limit(1))).scalar_one_or_none()
        if not uid:
            return False
        membership = await r.db.execute(
            select(CourseMembership.id)
            .where(
                CourseMembership.user_id == uid,
                CourseMembership.course_id.in_(r.active_ids),
                CourseMembership.role.in_(("owner", "teacher")),
            )
            .limit(1)
        )
        return membership.scalar_one_or_none() is not None
    except Exception:
        logger.debug("course_staff_check skipped")
        return False


async def _student_groups(r: _Reader) -> list[Item]:
    """Not in any group; or in groups with a GitLab role below Developer,
    which cannot push code or open merge requests."""
    from app.compliance.roles import ACCESS_DEVELOPER

    try:
        student = (
            await r.db.execute(select(Student).where(_student_match_condition(r.auth)))
        ).scalar_one_or_none()
    except Exception:
        logger.debug("student team check skipped")
        return []
    if not student:
        return []

    in_scope = (
        TeamMember.student_id == student.id,
        Team.course_id.in_(r.active_ids),
        Team.is_active.is_(True),
    )
    items: list[Item] = []
    try:
        groups = await _count(
            r.db,
            select(func.count(TeamMember.team_id))
            .join(Team, TeamMember.team_id == Team.id)
            .where(*in_scope),
        )
        if groups == 0:
            items.append(
                _item(
                    "users",
                    "info",
                    r.t("Not assigned to any group"),
                    r.t(
                        "You are enrolled but not in a group yet. "
                        "Your teacher will assign you soon."
                    ),
                )
            )
    except Exception:
        logger.debug("student team check skipped")

    try:
        memberships = await r.db.execute(
            select(TeamMember.gitlab_access_level, TeamMember.gitlab_access_role, Team.name)
            .join(Team, TeamMember.team_id == Team.id)
            .where(*in_scope, TeamMember.is_active.is_(True)),
        )
        low = [
            (m.name, m.gitlab_access_role or "unknown")
            for m in memberships.all()
            if m.gitlab_access_level is not None and m.gitlab_access_level < ACCESS_DEVELOPER
        ]
    except Exception:
        logger.debug("gitlab role check skipped", exc_info=True)
        return items
    if low:
        extra = len(low) - 3
        items.append(
            _item(
                "alert-circle",
                "warning",
                r.t("Insufficient GitLab role"),
                r.t(
                    "Your role ({role}) in "
                    "{groups}{suffix} does not "
                    "allow pushing code or "
                    "creating merge requests. "
                    "Ask your teacher to "
                    "upgrade your role to "
                    "Developer or higher."
                ).format(
                    role=", ".join(sorted({role for _, role in low})),
                    groups=", ".join(g for g, _ in low[:3]),
                    suffix=f" (+{extra})" if extra > 0 else "",
                ),
            )
        )
    return items


async def _failing_checks(r: _Reader) -> list[Item]:
    """The student's bottlenecks, from the latest snapshot of each group."""
    try:
        latest = (
            select(
                MetricSnapshot.team_id,
                func.max(MetricSnapshot.computed_at).label("max_at"),
            )
            .join(Student, MetricSnapshot.student_id == Student.id)
            .where(
                MetricSnapshot.course_id.in_(r.active_ids),
                _student_match_condition(r.auth),
            )
            .group_by(MetricSnapshot.team_id)
            .subquery()
        )
        rows = await r.db.execute(
            select(MetricSnapshot.bottlenecks)
            .join(Student, MetricSnapshot.student_id == Student.id)
            .join(
                latest,
                (MetricSnapshot.team_id == latest.c.team_id)
                & (MetricSnapshot.computed_at == latest.c.max_at),
            )
            .where(
                MetricSnapshot.course_id.in_(r.active_ids),
                _student_match_condition(r.auth),
            ),
        )
        # Snapshots computed before 2026.11.2.post4 listed a switched-off check
        # as a bottleneck; a check the course disabled is not one the student failed.
        failing = sorted(
            {
                b
                for (bottlenecks,) in rows.all()
                if bottlenecks
                for b in bottlenecks
                if b != "Check disabled"
            }
        )
    except Exception:
        logger.debug("bottleneck query skipped")
        return []
    if not failing:
        return []
    # The engine's detail texts are English; the catalogue carries a pattern
    # for each of them, so a Slovak reader gets Slovak here.
    missing = ", ".join(r.t(b) for b in failing[:5])
    suffix = "..." if len(failing) > 5 else ""
    return [
        _item(
            "alert-triangle",
            "warning",
            f"{len(failing)} {r.t('compliance checks failing')}",
            f"{r.t('Missing')}: {missing}{suffix}",
            f"/dashboard/courses/{r.first_cid}" if r.first_cid else None,
        )
    ]


async def _open_mrs(r: _Reader) -> list[Item]:
    """The student's MRs still open.

    `outerjoin` on CourseSettings + a null-safe predicate keeps courses that
    have not configured a semester yet (they fall back to "all time"); for
    courses with a start date, pre-semester MRs still "opened" on GitLab are
    never counted.
    """
    open_mrs = await _count(
        r.db,
        select(func.count(MergeRequest.id))
        .select_from(MergeRequest)
        .join(Student, MergeRequest.author_id == Student.id)
        .join(GitLabProject, MergeRequest.project_id == GitLabProject.id)
        .join(Team, GitLabProject.team_id == Team.id)
        .outerjoin(CourseSettings, CourseSettings.course_id == Team.course_id)
        .where(
            MergeRequest.state == "opened",
            Team.course_id.in_(r.active_ids),
            Team.is_active.is_(True),
            _student_match_condition(r.auth),
            or_(
                CourseSettings.semester_start_date.is_(None),
                MergeRequest.created_at >= CourseSettings.semester_start_date,
            ),
        ),
    )
    if open_mrs <= 0:
        return []
    return [
        _item(
            "git-pull-request",
            "info",
            f"{open_mrs} {r.t('open merge requests')}",
            r.t("Your MRs are awaiting review or need to be merged."),
            f"/dashboard/courses/{r.first_cid}/activity" if r.first_cid else None,
        )
    ]


async def _failed_pipelines(r: _Reader) -> list[Item]:
    """Failed pipelines on the student's projects in the last 7 days."""
    try:
        failed = await _count(
            r.db,
            select(func.count(Pipeline.id))
            .select_from(Pipeline)
            .join(GitLabProject, Pipeline.project_id == GitLabProject.id)
            .join(Team, GitLabProject.team_id == Team.id)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .join(Student, TeamMember.student_id == Student.id)
            .outerjoin(CourseSettings, CourseSettings.course_id == Team.course_id)
            .where(
                Pipeline.status == "failed",
                Team.course_id.in_(r.active_ids),
                Team.is_active.is_(True),
                _student_match_condition(r.auth),
                Pipeline.created_at >= r.now - timedelta(days=7),
                or_(
                    CourseSettings.semester_start_date.is_(None),
                    Pipeline.created_at >= CourseSettings.semester_start_date,
                ),
            ),
        )
    except Exception:
        logger.debug("pipeline query skipped")
        return []
    if failed <= 0:
        return []
    return [
        _item(
            "x-circle",
            "danger",
            f"{failed} {r.t('failed pipelines')}",
            r.t("CI/CD pipelines failed in the last 7 days."),
            f"/dashboard/courses/{r.first_cid}/activity" if r.first_cid else None,
        )
    ]


# -- The builder --------------------------------------------------------------

_SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}


async def _build_attention_items(
    role: str,
    active_ids: list[uuid.UUID],
    course_sync_info: dict[uuid.UUID, dict[str, int]],
    db: DbSession,
    _auth: dict[str, str],
    locale: str = "sk",
    *,
    red_teams_count: int | None = None,
    active_courses: list[Course] | None = None,
    archived_courses: list[Course] | None = None,
    lifecycle_courses: list[Course] | None = None,
) -> list[dict[str, Any]]:
    """Build 'items that need your attention' based on role.

    ``active_ids`` / ``active_courses`` / ``archived_courses`` are the courses of
    the academic period on screen. ``lifecycle_courses`` is every course the
    reader can see, in ANY period, and drives the two kinds of item that are
    about the reader's courses as a whole rather than about the term on screen:
    onboarding ("create your first course") and lifecycle housekeeping ("last
    summer's course is over - archive it", "transfer it to the new year").
    Scoped to the period on screen, those would vanish exactly when they matter:
    the course whose semester ended is, by definition, not in the newest term
    the dashboard opens on. ``None`` falls back to the scoped lists.
    """
    r = _Reader(
        role=role,
        locale=locale,
        auth=_auth,
        db=db,
        now=datetime.now(UTC),
        active_ids=active_ids,
        active_courses=active_courses or [],
    )
    life = (
        lifecycle_courses
        if lifecycle_courses is not None
        else [*(active_courses or []), *(archived_courses or [])]
    )
    life_active = [c for c in life if c.is_active]
    life_archived = [c for c in life if not c.is_active]

    # Onboarding only when the reader has no active course in ANY period. An
    # empty term with courses in another is not "create your first course" or
    # "not enrolled yet" - the course grid says the term is empty and offers
    # the period selector; saying the reader has nothing at all would be false.
    if not active_ids and not life_active:
        return _onboarding(r, life_archived)

    staff = role in ("admin", "teacher")
    items: list[Item] = []
    if staff:
        items += _gitlab_token(r)
        items += _pending_syncs(r, course_sync_info)
        items += await _failed_jobs(r)
    if staff and active_ids:
        items += await _red_teams(r, red_teams_count)
        items += await _stale_projects(r)
        items += await _webhook_warnings(r)
        items += await _assistant_warnings(r)
        items += await _deadlines(r)
    if role == "admin":
        items += await _dead_letters(r)
    if staff and active_ids:
        items += await _empty_courses(r)
        items += await _empty_teams(r)
        items += await _never_synced(r)
    if staff:
        try:
            settings_map = await course_settings_for(db, [c.id for c in life_active])
            items += _lifecycle(r, life_active, life_archived, settings_map)
        except Exception:
            logger.debug("course lifecycle attention items skipped", exc_info=True)
    if role == "student" and active_ids:
        if not await _is_course_staff(r):
            items += await _student_groups(r)
        items += await _failing_checks(r)
        items += await _open_mrs(r)
        items += await _failed_pipelines(r)
    if staff and active_ids:
        items += await _support_tickets(r)

    # Most critical first; the sort is stable, so each severity keeps the
    # order above.
    items.sort(key=lambda x: _SEVERITY_ORDER.get(x.get("severity", "info"), 9))
    return items

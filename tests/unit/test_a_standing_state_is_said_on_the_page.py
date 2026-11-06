"""Events warnings are deduplicated; Support shares one course table.

A standing warning is raised once while visible. User-triggered repeats count
occurrences on the same toast. Archived courses do not receive webhook warnings.
Support and ticket overview share course periods, status and ticket filters."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from starlette.requests import Request

from app.api.dashboard._helpers import _templates
from app.i18n import get_template_i18n_context
from app.models.course import Course

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src/app"
TEMPLATES = SRC / "templates"
JS = TEMPLATES / "static/js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _request(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            # English, so the checks below read the source strings
            "headers": [(b"cookie", b"gp_lang=en")],
            "root_path": "",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 1),
            "app": None,
        }
    )


def _course(code: str, year: str, semester: str, *, active: bool) -> Course:
    course = Course(
        id=uuid.uuid4(), code=code, name=f"{code} course", academic_year=year, semester=semester
    )
    course.is_active = active
    return course


def _render(template: str, path: str, **ctx: Any) -> str:
    request = _request(path)
    context: dict[str, Any] = {
        "request": request,
        "csrf_token": "test-csrf",
        "csp_nonce": "test-nonce",
        "is_admin": True,
        "is_teacher": False,
        **get_template_i18n_context(request),
        **ctx,
    }
    return _templates(request).env.get_template(template).render(**context)


# -- Events: the webhook warning is a toast, raised once -----------------------


def _events(**ctx: Any) -> str:
    base: dict[str, Any] = {
        "webhooks_configured": False,
        "silent_courses": [],
        "recent_events_json": {"events": [], "total": 0},
        "dlq_json": {"items": [], "total": 0},
    }
    base.update(ctx)
    return _render("admin_events.html", "/dashboard/admin/events", **base)


def test_the_events_page_raises_its_warning_as_a_toast_once() -> None:
    page = _read(JS / "pages/admin-events.js")
    assert "{ once: true }" in page.split("_startupWarning.message", 2)[2].split("\n", 1)[0]
    # ...and nothing else says it a second time on the page
    assert "alert_block" not in _read(TEMPLATES / "admin_events.html")


def test_no_webhook_at_all_is_the_warning() -> None:
    html = _events(webhooks_configured=False)
    assert '"startupWarning": {"message": "No webhooks configured. Events reach' in html


def test_each_silent_course_is_named_with_its_term() -> None:
    course = _course("ZSI", "2025/2026", "summer", active=True)
    html = _events(webhooks_configured=True, silent_courses=[course])
    assert "received no event from GitLab in 48 hours" in html
    assert "ZSI (2025/2026 \\u00b7 Summer)" in html or "ZSI (2025/2026 \u00b7 Summer)" in html


def test_nothing_is_raised_when_the_webhooks_are_fine() -> None:
    html = _events(webhooks_configured=True, silent_courses=[])
    assert '"startupWarning": null' in html


def test_the_webhook_report_counts_active_courses_only() -> None:
    route = _read(SRC / "api/dashboard/admin/events.py")
    assert "Course.is_active.is_(True)" in route
    assert "compute_webhook_activity(db, [c.id for c in active_courses])" in route


def test_a_page_raised_toast_is_not_said_again_while_it_is_up() -> None:
    base = _read(JS / "_parts/core/09-toasts.js")
    body = base.split("function showToast(", 1)[1].split("\nfunction ", 1)[0]
    assert body.count("else if (!_opts.once) _toastAgain(_liveSame, duration);") == 2
    assert body.count("if (_opts._fromRestore) _dequeueFlash(_opts._uid);") == 2


# -- Toasts: one copy while it is up -----------------------------------------


def test_a_toast_still_on_screen_is_not_raised_again() -> None:
    base = _read(JS / "_parts/core/09-toasts.js")
    body = base.split("function showToast(", 1)[1].split("\nfunction ", 1)[0]
    dedup = body.split("_sameAlreadyUp", 1)[1]
    # compared by type AND message, against live toasts and the queue
    assert "dataset.toastType === normalizedType" in body
    assert "dataset.toastMessage === String(message || '')" in body
    assert '.toast:not([data-removing="1"])' in dedup
    assert "_toastState.queue.some(" in dedup
    # the dataset it compares is the one every toast is stamped with
    assert "toast.dataset.toastMessage = String(message || '');" in body
    assert "toast.dataset.toastType = normalizedType;" in body


# -- Support tickets: a table of courses -------------------------------------


def _tickets(courses: list[Course], stats: dict[str, dict[str, Any]]) -> str:
    return _render(
        "support_tickets.html",
        "/dashboard/support/tickets",
        selected_course=None,
        user_courses=courses,
        ticket_stats=stats,
    )


def test_the_tickets_overview_is_one_table_active_courses_first() -> None:
    archived = _course("ZSI", "2024/2025", "summer", active=False)
    active = _course("ZSI", "2025/2026", "summer", active=True)
    html = _tickets(
        [archived, active],
        {
            str(archived.id): {"total": 4, "open": 1, "last": datetime(2025, 6, 1, tzinfo=UTC)},
            str(active.id): {"total": 2, "open": 0, "last": datetime(2026, 3, 2, tzinfo=UTC)},
        },
    )
    assert 'id="ticketCoursesTable"' in html
    assert html.count("<table") == 1
    # no disclosure - archived courses are rows, marked Archived
    assert "x-collapse" not in html.split('id="ticketCoursesTable"', 1)[1].split("</table>", 1)[0]
    assert html.index(f"course_id={active.id}") < html.index(f"course_id={archived.id}")
    assert "Archived" in html
    # each row names its term, and the open count is a badge
    assert html.count("gl-period-badge") >= 2
    assert "badge-warning" in html


def test_a_course_with_no_tickets_reads_zero_not_blank() -> None:
    course = _course("ZSI", "2025/2026", "summer", active=True)
    html = _tickets([course], {})
    row = html.split(f"course_id={course.id}", 1)[1].split("</tr>", 1)[0]
    assert 'data-sort-value="0"' in row


def test_the_route_counts_tickets_per_course_in_one_query() -> None:
    route = _read(SRC / "api/dashboard/support.py")
    block = route.split("ticket_stats: dict[str, dict[str, Any]] = {}", 1)[1]
    block = block.split("people_by_name", 1)[0]
    assert "group_by(SupportTicket.course_id)" in block
    assert '("open", "in_progress")' in block
    assert "func.max(SupportTicket.submitted_at)" in block
    assert '"ticket_stats": ticket_stats' in route


# -- The disclosure animation ------------------------------------------------


def test_a_collapsible_card_animates_a_box_without_padding() -> None:
    """x-collapse measured the padded .card-body and stalled at the height of
    its padding before snapping shut. It now animates a bare wrapper."""
    cards = _read(TEMPLATES / "components/cards.html")
    assert '<div class="card-collapse-region" x-show="open" x-collapse' in cards
    assert '<div class="card-body {{ body_class }}" x-show' not in cards
    css = _read(TEMPLATES / "static/css/cards.css")
    assert ".card > .card-collapse-region" in css
    assert ".card-collapse-region > .card-body" in css


def test_the_weekly_deadlines_disclosure_animates_a_bare_wrapper() -> None:
    part = _read(TEMPLATES / "partials/course_settings/_weekly_deadlines.html")
    assert '<div x-show="open" x-collapse><div class="mt-2">' in part


def test_the_tickets_overview_lays_out_like_the_tickets_list() -> None:
    """A fixed layout split the columns evenly on a phone, where the colgroup
    is hidden, and the period badge ran into the Status cell."""
    css = _read(TEMPLATES / "static/css/pages/support.css")
    assert ".ticket-courses-table { table-layout: auto; }" in css
    assert ".ticket-courses-table { width: 100%; table-layout: fixed; }" not in css


def test_an_assigned_ticket_says_so_once() -> None:
    """The assignment banner says it for as long as it is true; a toast
    repeated it the moment the page opened."""
    detail = _read(JS / "pages/support-ticket-detail.js")
    assert "gh-ticket-assigned-toast-" not in detail
    assert "Please review and respond.')" not in detail
    content = _read(TEMPLATES / "partials/support/_ticket_detail_content.html")
    assert "call alert(variant='info', title=t('This ticket is assigned to you.'))" in content
    assert "'assignedBy'" not in content


def test_the_toast_already_up_answers_when_raised_again() -> None:
    """Not stacked a second time - the one on screen knocks, rings and starts
    its countdown over, on both duplicate paths (the burst window and the
    still-on-screen guard)."""
    base = _read(JS / "_parts/core/09-toasts.js")
    body = base.split("function showToast(", 1)[1].split("\nfunction ", 1)[0]
    assert body.count("_toastAgain(_liveSame, duration);") == 2
    again = base.split("function _toastAgain(", 1)[1].split("\nfunction ", 1)[0]
    assert "GP.motion.toastAgain(toast)" in again
    assert "GP.motion.toastCountdown(bar, ttl);" in again
    assert "_startToastTimer(toast, ttl);" in again
    # the navigation-restore queue gets the new start too
    assert "p.createdAt = now; p.duration = ttl;" in again

    motion = _read(JS / "motion.js")
    fn = motion.split("function toastAgain(", 1)[1].split("\n  }\n", 1)[0]
    assert "--_toast-accent" in fn, "the ring is in the toast's own colour"
    assert "if (!REDUCED) {" in fn, "no travel under reduced motion"
    assert "G.isTweening(toast)" in fn, "an entering toast is left alone"
    assert "toastAgain: toastAgain," in motion
    countdown = motion.split("function toastCountdown(", 1)[1].split("\n  }\n", 1)[0]
    assert "bar._gpCountdown.kill()" in countdown


def test_a_repeated_toast_is_said_again_and_counted() -> None:
    """An 8px knock read as "the toast did not come". The toast replays its
    entrance and counts: x2, x3."""
    base = _read(JS / "_parts/core/09-toasts.js")
    again = base.split("function _toastAgain(", 1)[1].split("\nfunction ", 1)[0]
    assert "toast.dataset.toastRepeat = String(times);" in again
    assert "chip.className = 'toast-repeat';" in again
    motion = _read(JS / "motion.js")
    fn = motion.split("function toastAgain(", 1)[1].split("\n  }\n", 1)[0]
    assert "{ opacity: 0.2, x: -12 }" in fn, "the entrance every toast plays"
    assert "x: 8" not in fn, "the knock is back"
    css = _read(TEMPLATES / "static/css/toasts.css")
    assert ".toast-repeat {" in css


def test_one_press_is_never_counted_twice() -> None:
    """One click read "x2": the action's own answer and an echo of it (the
    server's event, a second listener) raised the same toast, and every raise
    counted. Only a new press - a pointer going down, Enter or Space - does."""
    base = _read(JS / "_parts/core/09-toasts.js")
    again = base.split("function _toastAgain(", 1)[1].split("\nfunction ", 1)[0]
    guard = "if (Number(toast.dataset.toastPress) === _pressCount) return;"
    assert guard in again, "an echo of the same press is counted as a repeat"
    assert again.index(guard) < again.index("toast.dataset.toastRepeat"), "counted before the guard"
    body = base.split("function showToast(", 1)[1].split("\nfunction ", 1)[0]
    assert "toast.dataset.toastPress = String(_pressCount);" in body
    assert "document.addEventListener('pointerdown'" in base
    assert "e.key === 'Enter' || e.key === ' '" in base


def test_the_tickets_overview_filters_by_period_and_status() -> None:
    table = _read(TEMPLATES / "partials/support/_course_table.html")
    assert "period_selector(period_scope)" in table
    assert "'filter-dropdowns': 'status:#' ~ table_id ~ 'Status@data-status'" in table
    assert "data-status=\"{{ 'active' if course.is_active else 'archived' }}\"" in table
    assert "t('No courses in {period}.'" in table
    route = _read(SRC / "api/dashboard/support.py")
    assert "ticket_courses = courses_in_scope(user_courses, period_scope)" in route
    assert "include_none=False, visible_courses=user_courses" in route


def test_the_status_filter_keeps_only_archived_rows() -> None:
    archived = _course("ZSI", "2024/2025", "summer", active=False)
    active = _course("ZSI", "2025/2026", "summer", active=True)
    html = _tickets([active, archived], {})
    assert 'data-status="archived"' in html
    assert 'data-status="active"' in html
    assert 'id="ticketCoursesTableStatus"' in html


def test_the_course_table_keeps_its_action_on_a_phone() -> None:
    """With "New request" spelled out the action column was too wide to stay
    pinned (table-scroll.js), and the button scrolled out of reach."""
    table = _read(TEMPLATES / "partials/support/_course_table.html")
    assert "btn_link_icon_only('plus', _href" in table
    assert "btn_link_icon_only('eye', _href" in table
    assert "btn_link_icon(" not in table

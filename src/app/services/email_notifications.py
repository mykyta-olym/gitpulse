"""Email notification service for GitPulse.

Production-grade email delivery with:
- Persistent delivery log (email_log table) for tracking & auditability
- Idempotency keys to prevent duplicate sends
- Automatic retry with exponential backoff (max 3 attempts)
- Async delivery via RQ worker queue
- Inline fallback when RQ is unavailable

Sends email notifications for:
- Welcome email on first login (role-specific content)
- Support tickets (created, assigned, status change, comment)
- User management (role change, account reactivation)
- Course management (teacher assignment, course archival/reactivation)

Uses SMTP configured via settings.  Feature-flagged by FEATURE_EMAIL_NOTIFICATIONS.
All ``enqueue_*`` / ``notify_*`` functions are safe to call even when email is
disabled - they silently return ``None`` / ``False``.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import logging
import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


# --- Configuration helpers ------------------------------------------------


def _get_settings() -> Any:
    from app.config import get_settings

    return get_settings()


def _base_url() -> str:
    return str(_get_settings().app_base_url).rstrip("/")


def _build_ticket_url(ticket_id: int) -> str:
    return f"{_base_url()}/dashboard/support/ticket/{ticket_id}"


def _idempotency_key(category: str, *parts: Any) -> str:
    """Deterministic 64-char key for deduplication."""
    raw = f"{category}:" + ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()


# --- Shared HTML email template ------------------------------------------
#
# Chrome is GitLab's own transactional mail, matched to
#   app/views/layouts/_mailer.html.haml         (table#body > line/header/wrapper/footer)
#   app/assets/stylesheets/mailers/mailer.scss  (palette, type, spacing)
#   app/assets/stylesheets/mailers/mailer_client_specific.scss  (media query, hacks)
# and to how GitLab's own mail actually RENDERS: a purple rule, a centred mark,
# a white card of centred text, a prominent purple button, then a footer of
# small grey print. Only the mark is ours.
#
# Why the rules are inlined: mail clients drop <link> stylesheets and Gmail
# strips most of <head>. GitLab runs premailer to inline that sheet at delivery
# time; we write the already-inlined form. The <style> block carries only what
# cannot be inlined - media queries and client hacks - which is exactly what
# GitLab marks 'data-premailer: ignore'.

_MAILER_FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"

# mailer.scss variables, verbatim.
_M_TEXT = "#333333"  # $mailer-text-color
_M_BG = "#fafafa"  # $mailer-bg-color
_M_LINK = "#3777b0"  # $mailer-link-color
_M_CARD_BG = "#ffffff"  # $mailer-wrapper-cell-bg-color
_M_CARD_BORDER = "#ededed"  # $mailer-wrapper-cell-border-color
_M_CHROME = "#5c5c5c"  # $mailer-header-footer-text-color
_M_MUTED = "#89888d"  # $gray-400, used by .gitlab-info-text
_M_WIDTH = 640  # $full-width
# $mailer-line-cell-bg-color. GitLab's purple, not ours: the brief was that
# only the mark and the data are ours, and every other surface is theirs.
_M_ACCENT = "#6b4fbb"
# $purple, used by .invite-btn-join for the one prominent action.
_M_BTN = "#6b4fbb"

_HEADER_HTML = (
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
    ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
    '<html lang="en"><head>\n'
    '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta http-equiv="X-UA-Compatible" content="IE=edge">\n'
    "<style>\n"
    # --- client-specific rules (mailer_client_specific.scss) ---
    "  body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }\n"
    "  table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }\n"
    "  img { -ms-interpolation-mode: bicubic; }\n"
    "  a[x-apple-data-detectors] { color: inherit !important; text-decoration: none !important;\n"
    "    font-size: inherit !important; font-family: inherit !important;\n"
    "    font-weight: inherit !important; line-height: inherit !important; }\n"
    "  div[style*='margin: 16px 0'] { margin: 0 !important; }\n"
    "  @media only screen and (max-width: 639px) {\n"
    "    body, #body { min-width: 320px !important; }\n"
    "    table.wrapper { width: 100% !important; min-width: 320px !important; }\n"
    "    table.wrapper td.wrapper-cell { border-left: 0 !important; border-right: 0 !important;\n"
    "      border-radius: 0 !important; padding-left: 16px !important;\n"
    "      padding-right: 16px !important; }\n"
    "    .gp-meta td { display: block !important; width: auto !important;\n"
    "      padding: 4px 0 !important; border-top: 0 !important; text-align: left !important; }\n"
    "    .gp-meta tr { display: block !important; padding: 8px 0 !important;\n"
    "      border-top: 1px solid " + _M_CARD_BORDER + " !important; }\n"
    "    .gp-meta tr:first-child { border-top: 0 !important; }\n"
    "  }\n"
    "</style>\n"
    "</head>\n"
    f'<body style="margin:0;padding:0;background-color:{_M_BG};text-align:center;'
    f'width:100%;height:100%;font-family:{_MAILER_FONT};">\n'
    f'<table id="body" border="0" cellpadding="0" cellspacing="0"'
    f' style="background-color:{_M_BG};margin:0;padding:0;text-align:center;width:100%;">\n'
    "<tbody>\n"
    # tr.line - the 4px rule GitLab puts above every message
    f'<tr class="line"><td style="background-color:{_M_ACCENT};height:4px;'
    'font-size:4px;line-height:4px;">&nbsp;</td></tr>\n'
    # tr.header - the mark, centred, on the page background (not on the card)
    f'<tr class="header"><td style="padding:25px 0;font-size:13px;line-height:1.6;'
    f'color:{_M_CHROME};font-family:{_MAILER_FONT};text-align:center;">\n'
    '<img src="{logo_url}" width="40" height="40" alt="GitPulse"'
    ' style="display:block;margin:0 auto;width:40px;height:40px;border:0;">\n'
    "</td></tr>\n"
    "<tr><td>\n"
    f'<table class="wrapper" border="0" cellpadding="0" cellspacing="0"'
    f' style="width:{_M_WIDTH}px;margin:0 auto;border-collapse:separate;border-spacing:0;">\n'
    "<tbody><tr>\n"
    f'<td class="wrapper-cell" style="background-color:{_M_CARD_BG};text-align:center;'
    f"padding:32px 40px;border:1px solid {_M_CARD_BORDER};border-radius:4px;"
    f'font-family:{_MAILER_FONT};">\n'
    f'<table class="content" border="0" cellpadding="0" cellspacing="0"'
    ' style="width:100%;border-collapse:separate;border-spacing:0;">\n'
    "<tbody><tr>\n"
    # td.text-content: 15px / 1.4 / centred, exactly as mailer.scss declares it
    f'<td class="text-content" style="font-family:{_MAILER_FONT};color:{_M_TEXT};'
    'font-size:15px;font-weight:400;line-height:1.4;padding:0;text-align:center;">\n'
)

_FOOTER_HTML = (
    "</td>\n</tr></tbody></table>\n"  # close table.content
    "</td>\n</tr></tbody></table>\n"  # close table.wrapper
    "</td></tr>\n"
    # tr.footer - the mark again, then the small grey print. GitLab repeats the
    # logo here and follows it with the reason the message was sent.
    f'<tr class="footer"><td style="padding:25px 0 8px;font-family:{_MAILER_FONT};'
    'text-align:center;">\n'
    '<img src="{logo_url}" width="28" height="28" alt=""'
    ' style="display:block;margin:0 auto 12px;width:28px;height:28px;border:0;">\n'
    f'<div style="font-size:13px;line-height:1.6;color:{_M_CHROME};">\n'
    f'<a href="{{base_url}}/dashboard" style="color:{_M_LINK};text-decoration:none;">'
    "Dashboard</a>\n"
    f'<span style="color:{_M_CARD_BORDER};margin:0 6px;">|</span>\n'
    f'<a href="{{base_url}}/docs/" style="color:{_M_LINK};text-decoration:none;">'
    "Documentation</a>\n"
    f'<span style="color:{_M_CARD_BORDER};margin:0 6px;">|</span>\n'
    f'<a href="{{base_url}}/dashboard/support" style="color:{_M_LINK};'
    'text-decoration:none;">Support</a>\n'
    "</div>\n"
    "</td></tr>\n"
    # .gitlab-info-text metrics: 24px 0 / 12px / $gray-400, centred
    f'<tr><td class="footer-message" style="padding:8px 0 24px;'
    f'font-family:{_MAILER_FONT};">\n'
    f'<div style="max-width:{_M_WIDTH}px;margin:0 auto;text-align:center;'
    f'color:{_M_MUTED};font-size:12px;line-height:1.6;">\n'
    "GitPulse &middot; Department of Computers and Informatics, FEI TUKE<br>\n"
    "You are receiving this email because of your GitPulse account. "
    f'<a href="{{base_url}}/dashboard/preferences" style="color:{_M_MUTED};'
    'text-decoration:underline;">Manage notifications</a>\n'
    "</div>\n</td></tr>\n"
    "</tbody></table>\n"
    "</body></html>"
)


def _build_html(
    *,
    heading: str,
    body_lines: list[str],
    action_url: str | None = None,
    action_label: str = "View Details",
    meta_rows: list[tuple[str, str]] | None = None,
) -> str:
    """Build a consistent HTML email from parts."""
    base = _base_url()
    logo_url = html.escape(f"{base}/static/img/email-logo.png")
    # .replace (not .format): the <style> block contains literal CSS braces.
    parts: list[str] = [_HEADER_HTML.replace("{logo_url}", logo_url)]

    # 20px is the title size mailer.scss pins when it caps user-generated
    # headings ("never outrank the email's own 20px title").
    parts.append(
        f'<h1 style="color:{_M_TEXT};margin:0 0 16px;font-size:20px;font-weight:600;'
        f'line-height:1.4;font-family:{_MAILER_FONT};">{html.escape(heading)}</h1>\n'
    )

    for line in body_lines:
        parts.append(
            f'<p style="color:{_M_TEXT};line-height:1.5;margin:0 0 12px;font-size:15px;'
            f"word-break:break-word;overflow-wrap:anywhere;"
            f'font-family:{_MAILER_FONT};">{line}</p>\n'
        )

    # The action comes BEFORE the detail table, the way GitLab leads with the
    # one thing it wants pressed and leaves the particulars underneath.
    if action_url:
        parts.append(
            '<table border="0" cellpadding="0" cellspacing="0"'
            ' style="margin:24px auto 0;"><tbody><tr><td'
            f' style="background-color:{_M_BTN};border-radius:4px;">\n'
            f'<a href="{html.escape(action_url)}" style="display:inline-block;'
            f"padding:12px 24px;color:#ffffff;text-decoration:none;font-size:15px;"
            f'font-weight:600;line-height:1.2;font-family:{_MAILER_FONT};">'
            f"{html.escape(action_label)}</a>\n"
            "</td></tr></tbody></table>\n"
        )

    if meta_rows:
        parts.append(
            f'<table class="gp-meta" style="font-size:14px;color:{_M_TEXT};'
            "border-collapse:collapse;margin:28px 0 0;width:100%;"
            f"border:1px solid {_M_CARD_BORDER};border-radius:4px;"
            f'font-family:{_MAILER_FONT};text-align:left;">\n'
        )
        for i, (label, value) in enumerate(meta_rows):
            _border = f"border-top:1px solid {_M_CARD_BORDER};" if i else ""
            parts.append(
                f'<tr><td style="padding:10px 14px;vertical-align:top;'
                f'color:{_M_CHROME};width:140px;{_border}">'
                f"<strong>{html.escape(label)}</strong></td>"
                f'<td style="padding:10px 14px;word-break:break-word;'
                f'overflow-wrap:anywhere;{_border}">'
                f"{html.escape(value)}</td></tr>\n"
            )
        parts.append("</table>\n")

    parts.append(_FOOTER_HTML.replace("{logo_url}", logo_url).format(base_url=html.escape(base)))
    return "".join(parts)


# --- Core SMTP delivery --------------------------------------------------


def smtp_send(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """Send an email via SMTP.  Raises on failure (caller handles retry)."""
    settings = _get_settings()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=settings.smtp_from_email.split("@")[-1])
    msg["X-Mailer"] = "GitPulse/1.0"
    msg["List-Unsubscribe"] = f"<{_base_url()}/dashboard/preferences>"

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        server.ehlo()
        if settings.smtp_use_tls:
            resp_code, _ = server.starttls()
            if resp_code != 220:
                raise smtplib.SMTPException(f"STARTTLS failed with code {resp_code}")
            server.ehlo()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, [to_email], msg.as_string())

    logger.info("email_sent to=%s subject=%s", to_email, subject)


# --- Queue-based delivery ------------------------------------------------


# category -> the User column that opts out of it. "welcome" is deliberately
# absent: it is the one-off mail explaining the account, sent before the reader
# has ever seen the preferences page, and "general" is operational.
NOTIFICATION_OPT_OUTS: dict[str, str] = {
    "ticket": "notify_tickets",
    # Staff-facing queue mail is a SEPARATE category from your own tickets.
    # They shared one flag, so an admin who muted ticket updates also stopped
    # seeing that a new ticket had arrived with nobody on it - silencing an
    # operational duty along with a personal preference.
    "ticket_queue": "notify_ticket_queue",
    "course": "notify_courses",
    "user": "notify_account",
}


async def _recipient_opted_out(
    to_email: str, category: str, session_factory: async_sessionmaker[AsyncSession]
) -> bool:
    """True when the recipient has switched this category off.

    Enforced HERE rather than at each call site, and on the server rather than
    in the form: every notification funnels through enqueue_email, so this is
    the one place that cannot be bypassed by a caller that forgets to check.

    Fails OPEN - an unknown address, or a database that cannot be reached, must
    not silently swallow mail. A missed ticket notification is worse than an
    unwanted one.
    """
    column = NOTIFICATION_OPT_OUTS.get(category)
    if not column or not to_email:
        return False
    try:
        from sqlalchemy import select

        from app.models.user import User

        async with session_factory() as session:
            result = await session.execute(
                select(getattr(User, column)).where(User.email == to_email)
            )
            wants = result.scalar_one_or_none()
    except Exception:
        logger.debug("notification_opt_out_lookup_failed", exc_info=True)
        return False
    # None = no account with that address (an external recipient): send.
    return wants is False


def enqueue_email(
    *,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    category: str = "general",
    idempotency_key: str | None = None,
    context: dict[str, Any] | None = None,
) -> int | None:
    """Persist an email to email_log and enqueue for async delivery.

    Returns the email_log.id on success, None if feature is disabled or
    the email was already enqueued (idempotency duplicate).
    """

    settings = _get_settings()
    if not settings.feature_email_notifications:
        return None
    if not settings.smtp_host:
        logger.debug("SMTP not configured, skipping email")
        return None

    if not idempotency_key:
        idempotency_key = _idempotency_key(category, to_email, subject, uuid.uuid4().hex[:8])

    async def _persist_with_local_engine() -> int | None:
        """Keep preferences and persistence on one loop-owned engine."""
        from app.models.email_log import EmailLog

        local_engine = create_async_engine(
            str(settings.database_url),
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
        )
        local_factory = async_sessionmaker(local_engine, expire_on_commit=False)
        try:
            if await _recipient_opted_out(to_email, category, local_factory):
                logger.debug("email_opted_out to=%s category=%s", to_email, category)
                return None
            async with local_factory() as session:
                existing = await session.execute(
                    select(EmailLog.id).where(EmailLog.idempotency_key == idempotency_key)
                )
                if existing.scalar_one_or_none() is not None:
                    logger.debug("email_duplicate idem_key=%s", idempotency_key)
                    return None

                log = EmailLog(
                    idempotency_key=idempotency_key,
                    to_email=to_email,
                    subject=subject,
                    category=category,
                    status="pending",
                    html_body=html_body,
                    text_body=text_body,
                    next_retry_at=datetime.now(UTC),
                    context_json=json.dumps(context) if context else None,
                )
                session.add(log)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    logger.debug("email_duplicate_race idem_key=%s", idempotency_key)
                    return None
                await session.refresh(log)
                return log.id
        finally:
            await local_engine.dispose()

    def persist() -> int | None:
        return asyncio.run(_persist_with_local_engine())

    # A synchronous worker owns its loop. Legacy async callers use a separate
    # thread; request handlers should offload the whole notification with to_thread.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        log_id = persist()
    else:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            log_id = pool.submit(persist).result(timeout=15)

    if log_id is None:
        return None

    # Try to enqueue RQ job for immediate delivery
    try:
        from redis import Redis
        from rq import Queue

        conn = Redis.from_url(str(settings.redis_url))
        q = Queue("default", connection=conn)
        q.enqueue(
            "app.services.email_notifications.deliver_email",
            log_id,
            job_timeout=30,
        )
        logger.debug("email_enqueued log_id=%d", log_id)
    except Exception:
        logger.warning(
            "email_rq_enqueue_failed log_id=%d - sweep will pick it up",
            log_id,
            exc_info=True,
        )

    return log_id


# --- RQ worker delivery function -----------------------------------------


def deliver_email(email_log_id: int) -> None:
    """RQ-callable: deliver a single email_log entry via SMTP.

    On failure, schedules exponential-backoff retry (2^attempts minutes).
    After max_attempts, marks as 'failed'.
    """

    async def _deliver() -> None:

        from app.workers.bootstrap import worker_session

        async with worker_session() as (session, _settings):
            from app.models.email_log import EmailLog

            log = await session.get(EmailLog, email_log_id)
            if not log:
                logger.warning("email_log_not_found id=%d", email_log_id)
                return

            if log.status == "sent":
                return  # Already delivered

            if log.status == "failed":
                return  # Permanently failed

            # When a delivery attempt fails but retries remain, the job
            # re-enqueues ITSELF with a backoff delay (set below) instead of
            # waiting for a periodic sweep - the scheduler no longer runs one.
            retry_after_seconds: float | None = None

            log.attempts += 1
            try:
                smtp_send(log.to_email, log.subject, log.html_body, log.text_body)
                log.status = "sent"
                log.sent_at = datetime.now(UTC)
                log.last_error = None
                log.next_retry_at = None
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"[:500]
                log.last_error = error_msg
                if log.attempts >= log.max_attempts:
                    log.status = "failed"
                    log.next_retry_at = None
                    logger.error(
                        "email_permanently_failed id=%d to=%s attempts=%d err=%s",
                        email_log_id,
                        log.to_email,
                        log.attempts,
                        error_msg,
                    )
                else:
                    log.status = "retry"
                    backoff = timedelta(minutes=2**log.attempts)
                    next_retry_at = datetime.now(UTC) + backoff
                    log.next_retry_at = next_retry_at
                    retry_after_seconds = backoff.total_seconds()
                    logger.warning(
                        "email_delivery_failed id=%d to=%s attempt=%d/%d next_retry=%s err=%s",
                        email_log_id,
                        log.to_email,
                        log.attempts,
                        log.max_attempts,
                        next_retry_at.isoformat(),
                        error_msg,
                    )

            await session.commit()

            # On a retryable failure the delivery job re-enqueues ITSELF with a
            # backoff delay. RQ's own delayed-job support handles the wait - the
            # workers run with ``with_scheduler=True`` (see app.workers.main), so
            # ``Queue.enqueue_in`` is picked up without any separate service.
            if retry_after_seconds is not None:
                try:
                    from redis import Redis
                    from rq import Queue

                    conn = Redis.from_url(str(_settings.redis_url))
                    Queue("default", connection=conn).enqueue_in(
                        timedelta(seconds=retry_after_seconds),
                        "app.services.email_notifications.deliver_email",
                        email_log_id,
                        job_timeout=30,
                    )
                    logger.debug(
                        "email_retry_rescheduled id=%d in=%.0fs",
                        email_log_id,
                        retry_after_seconds,
                    )
                except Exception:
                    logger.warning(
                        "email_retry_reschedule_failed id=%d - left as 'retry' for manual run",
                        email_log_id,
                        exc_info=True,
                    )

    asyncio.run(_deliver())


# --- Notification builders ------------------------------------------------
# Each notify_* function builds the email content and calls enqueue_email().
# They return the email_log ID (int) on success, or None.
# All emails go through the queue for reliability.


def notify_ticket_created(
    ticket_id: int,
    title: str,
    category: str,
    to_email: str | None = None,
) -> int | None:
    """Email when a support ticket is created."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    subject = f"[GitPulse] Ticket #{ticket_id} \u2014 {title}"

    text_body = (
        f"Your request (Ticket #{ticket_id}) has been received.\n\n"
        f"Category: {category}\nSubject: {title}\n\n"
        f"View ticket: {url}\n\n\u2014 GitPulse Support"
    )

    html_body = _build_html(
        heading=f"Ticket #{ticket_id} received",
        body_lines=[
            f"Your request <strong>#{ticket_id}</strong> has been received and"
            " will be reviewed by our team.",
        ],
        action_url=url,
        action_label=f"View Ticket #{ticket_id}",
        meta_rows=[("Subject", title), ("Category", category)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket",
        idempotency_key=_idempotency_key("ticket_created", ticket_id, to_email),
        context={"ticket_id": ticket_id},
    )


def notify_ticket_new_to_staff(
    ticket_id: int,
    title: str,
    category: str,
    submitted_by: str,
    course_code: str,
    to_email: str,
) -> int | None:
    """Email course staff when a new support ticket arrives (one per recipient)."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    subject = f"[GitPulse] New ticket #{ticket_id} ({course_code}) \u2014 {title}"

    text_body = (
        f"A new support ticket has been submitted.\n\n"
        f"Course: {course_code}\nCategory: {category}\n"
        f"From: {submitted_by}\nSubject: {title}\n\n"
        f"Triage: {url}\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading=f"New ticket #{ticket_id}",
        body_lines=[
            f"<strong>{html.escape(submitted_by)}</strong> submitted a new ticket"
            f" in <strong>{html.escape(course_code)}</strong>.",
            "Please review and assign it.",
        ],
        action_url=url,
        action_label=f"Open Ticket #{ticket_id}",
        meta_rows=[
            ("Course", course_code),
            ("Subject", title),
            ("Category", category),
            ("Submitted by", submitted_by),
        ],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket_queue",
        idempotency_key=_idempotency_key("ticket_new_staff", ticket_id, to_email),
        context={"ticket_id": ticket_id},
    )


def notify_ticket_comment(
    ticket_id: int,
    title: str,
    author: str,
    comment_content: str,
    to_email: str | None = None,
) -> int | None:
    """Email when a comment is added to a ticket."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    subject = f"[GitPulse] Ticket #{ticket_id} \u2014 {title}"

    preview = comment_content[:500]
    if len(comment_content) > 500:
        preview += "\u2026"

    text_body = (
        f"Your request (Ticket #{ticket_id}) has been updated.\n\n"
        f"{author} commented:\n{preview}\n\n"
        f"View ticket: {url}\n\n\u2014 GitPulse Support"
    )

    html_body = _build_html(
        heading=f"Ticket #{ticket_id} updated",
        body_lines=[
            f"<strong>{html.escape(author)}</strong> commented:",
            f'<span style="white-space:pre-wrap">{html.escape(preview)}</span>',
        ],
        action_url=url,
        action_label=f"View Ticket #{ticket_id}",
        meta_rows=[("Subject", title)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket",
        idempotency_key=_idempotency_key("ticket_comment", ticket_id, author, preview[:64]),
        context={"ticket_id": ticket_id},
    )


def notify_ticket_assignment(
    ticket_id: int,
    title: str,
    assigned_by: str,
    to_email: str | None = None,
) -> int | None:
    """Email when a ticket is assigned to someone."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    subject = f"[GitPulse] Ticket #{ticket_id} assigned to you"

    text_body = (
        f"You have been assigned to Ticket #{ticket_id}.\n\n"
        f"Assigned by: {assigned_by}\nSubject: {title}\n\n"
        f"View ticket: {url}\n\n\u2014 GitPulse Support"
    )

    html_body = _build_html(
        heading=f"Ticket #{ticket_id} assigned to you",
        body_lines=[
            f"You have been assigned to <strong>Ticket #{ticket_id}</strong>"
            f" by <strong>{html.escape(assigned_by)}</strong>.",
            "Please review the ticket and respond.",
        ],
        action_url=url,
        action_label=f"View Ticket #{ticket_id}",
        meta_rows=[("Subject", title), ("Assigned by", assigned_by)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket",
        idempotency_key=_idempotency_key("ticket_assign", ticket_id, to_email),
        context={"ticket_id": ticket_id},
    )


def notify_ticket_status_change(
    ticket_id: int,
    title: str,
    new_status: str,
    to_email: str | None = None,
) -> int | None:
    """Email when ticket status changes."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    status_display = new_status.replace("_", " ").title()
    subject = f"[GitPulse] Ticket #{ticket_id} \u2014 {status_display}"

    text_body = (
        f"Ticket #{ticket_id} status changed to: {status_display}\n\n"
        f"Subject: {title}\n\n"
        f"View ticket: {url}\n\n\u2014 GitPulse Support"
    )

    html_body = _build_html(
        heading=f"Ticket #{ticket_id} \u2014 {status_display}",
        body_lines=[
            f"The status of <strong>Ticket #{ticket_id}</strong> has been"
            f" updated to <strong>{html.escape(status_display)}</strong>.",
        ],
        action_url=url,
        action_label=f"View Ticket #{ticket_id}",
        meta_rows=[("Subject", title), ("New Status", status_display)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket",
        idempotency_key=_idempotency_key("ticket_status", ticket_id, new_status),
        context={"ticket_id": ticket_id},
    )


def notify_ticket_priority_change(
    ticket_id: int,
    title: str,
    new_priority: str,
    to_email: str | None = None,
) -> int | None:
    """Email when ticket priority changes (parallel to status-change emails)."""
    if not to_email:
        return None

    url = _build_ticket_url(ticket_id)
    prio_display = new_priority.replace("_", " ").title()
    subject = f"[GitPulse] Ticket #{ticket_id} — {prio_display} priority"

    text_body = (
        f"Ticket #{ticket_id} priority changed to: {prio_display}\n\n"
        f"Subject: {title}\n\n"
        f"View ticket: {url}\n\n— GitPulse Support"
    )

    html_body = _build_html(
        heading=f"Ticket #{ticket_id} — {prio_display} priority",
        body_lines=[
            f"The priority of <strong>Ticket #{ticket_id}</strong> has been"
            f" updated to <strong>{html.escape(prio_display)}</strong>.",
        ],
        action_url=url,
        action_label=f"View Ticket #{ticket_id}",
        meta_rows=[("Subject", title), ("New Priority", prio_display)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="ticket",
        idempotency_key=_idempotency_key("ticket_priority", ticket_id, new_priority),
        context={"ticket_id": ticket_id},
    )


# --- User management notifications --------------------------------------


def notify_role_change(
    username: str,
    old_role: str,
    new_role: str,
    changed_by: str,
    to_email: str | None = None,
) -> int | None:
    """Notify a user that their role has changed."""
    if not to_email:
        return None

    url = f"{_base_url()}/dashboard"
    subject = f"[GitPulse] Your role has been changed to {new_role}"

    text_body = (
        f"Hi {username},\n\nYour role has been changed from "
        f"{old_role} to {new_role} by {changed_by}.\n\n"
        f"Open dashboard: {url}\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading="Role changed",
        body_lines=[
            f"Hi <strong>{html.escape(username)}</strong>,",
            f"Your role has been changed from <strong>{html.escape(old_role)}</strong>"
            f" to <strong>{html.escape(new_role)}</strong>"
            f" by <strong>{html.escape(changed_by)}</strong>.",
        ],
        action_url=url,
        action_label="Open Dashboard",
        meta_rows=[("Previous role", old_role), ("New role", new_role), ("Changed by", changed_by)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="user",
        idempotency_key=_idempotency_key("role_change", username, old_role, new_role),
        context={"username": username},
    )


def notify_account_reactivated(
    username: str,
    reactivated_by: str,
    to_email: str | None = None,
) -> int | None:
    """Notify a user that their account has been reactivated."""
    if not to_email:
        return None

    url = f"{_base_url()}/dashboard"
    subject = "[GitPulse] Your account has been reactivated"

    text_body = (
        f"Hi {username},\n\nYour GitPulse account has been reactivated "
        f"by {reactivated_by}. You can now log in again.\n\n"
        f"Open dashboard: {url}\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading="Account reactivated",
        body_lines=[
            f"Hi <strong>{html.escape(username)}</strong>,",
            "Your GitPulse account has been <strong>reactivated</strong>"
            f" by <strong>{html.escape(reactivated_by)}</strong>.",
            "You can now log in again.",
        ],
        action_url=url,
        action_label="Open Dashboard",
        meta_rows=[("Reactivated by", reactivated_by)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="user",
        idempotency_key=_idempotency_key("account_reactivated", username),
        context={"username": username},
    )


# --- Course management notifications ------------------------------------


def notify_teacher_assigned_to_course(
    teacher_username: str,
    course_code: str,
    course_name: str,
    assigned_by: str,
    course_id: uuid.UUID | int | None = None,
    to_email: str | None = None,
) -> int | None:
    """Notify a teacher they have been assigned to a course."""
    if not to_email:
        return None

    url = f"{_base_url()}/dashboard/course/{course_id}" if course_id else f"{_base_url()}/dashboard"
    subject = f"[GitPulse] You have been assigned to {course_code}"

    text_body = (
        f"Hi {teacher_username},\n\nYou have been assigned as teacher to "
        f"{course_code} \u2014 {course_name} by {assigned_by}.\n\n"
        f"View course: {url}\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading=f"Assigned to {course_code}",
        body_lines=[
            f"Hi <strong>{html.escape(teacher_username)}</strong>,",
            f"You have been assigned as teacher to"
            f" <strong>{html.escape(course_code)} \u2014 {html.escape(course_name)}</strong>"
            f" by <strong>{html.escape(assigned_by)}</strong>.",
        ],
        action_url=url,
        action_label="View Course",
        meta_rows=[("Course", f"{course_code} \u2014 {course_name}"), ("Assigned by", assigned_by)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="course",
        idempotency_key=_idempotency_key("teacher_assigned", teacher_username, course_code),
        context={"course_code": course_code},
    )


def notify_course_archived(
    course_code: str,
    course_name: str,
    archived_by: str,
    to_email: str | None = None,
) -> int | None:
    """Notify course staff that a course has been archived."""
    if not to_email:
        return None

    subject = f"[GitPulse] Course {course_code} has been archived"

    text_body = (
        f"Course {course_code} \u2014 {course_name} has been archived "
        f"by {archived_by}.\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading=f"Course {course_code} archived",
        body_lines=[
            f"<strong>{html.escape(course_code)} \u2014 {html.escape(course_name)}</strong>"
            f" has been archived by <strong>{html.escape(archived_by)}</strong>.",
            "The course is no longer active. Contact an admin to reactivate.",
        ],
        meta_rows=[("Course", f"{course_code} \u2014 {course_name}"), ("Archived by", archived_by)],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="course",
        idempotency_key=_idempotency_key("course_archived", course_code, to_email),
        context={"course_code": course_code},
    )


def notify_course_reactivated(
    course_code: str,
    course_name: str,
    reactivated_by: str,
    course_id: uuid.UUID | int | None = None,
    to_email: str | None = None,
) -> int | None:
    """Notify course staff that a course has been reactivated."""
    if not to_email:
        return None

    url = f"{_base_url()}/dashboard/course/{course_id}" if course_id else f"{_base_url()}/dashboard"
    subject = f"[GitPulse] Course {course_code} has been reactivated"

    text_body = (
        f"Course {course_code} \u2014 {course_name} has been reactivated "
        f"by {reactivated_by}.\n\nView course: {url}\n\n\u2014 GitPulse"
    )

    html_body = _build_html(
        heading=f"Course {course_code} reactivated",
        body_lines=[
            f"<strong>{html.escape(course_code)} \u2014 {html.escape(course_name)}</strong>"
            f" has been reactivated by <strong>{html.escape(reactivated_by)}</strong>.",
        ],
        action_url=url,
        action_label="View Course",
        meta_rows=[
            ("Course", f"{course_code} \u2014 {course_name}"),
            ("Reactivated by", reactivated_by),
        ],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="course",
        idempotency_key=_idempotency_key("course_reactivated", course_code, to_email),
        context={"course_code": course_code},
    )


# --- Welcome email (first login) ----------------------------------------

# Role-specific guidance shown to new users on first login.
_WELCOME_ROLE_CONTENT: dict[str, dict[str, Any]] = {
    "student": {
        "greeting": "Welcome to GitPulse!",
        "intro": (
            "Your student account is ready. GitPulse tracks your DevOps"
            " progress, CI/CD pipeline results, and project submissions"
            " automatically."
        ),
        "bullets": [
            "<strong>Dashboard</strong> \u2014 view your grades,"
            " CI results, and feedback in one place",
            "<strong>GitLab Integration</strong> \u2014 your repositories are synced automatically",
            "<strong>Support</strong> \u2014 open a ticket if you need help from your teacher",
            "<strong>Deadlines</strong> \u2014 check the course page for submission deadlines",
        ],
        "cta_label": "Open Dashboard",
        "cta_path": "/dashboard",
    },
    "teacher": {
        "greeting": "Welcome to GitPulse!",
        "intro": (
            "Your teacher account is ready. GitPulse helps you manage"
            " courses, monitor student CI/CD pipelines, run automated"
            " checks, and provide structured feedback."
        ),
        "bullets": [
            "<strong>Courses</strong> \u2014 manage your courses and student rosters",
            "<strong>Checks</strong> \u2014 configure automated CI checks and grading settings",
            "<strong>Analytics</strong> \u2014 view course statistics and progress summaries",
            "<strong>Students</strong> \u2014 view individual"
            " student pipelines, commits, and feedback",
            "<strong>Support</strong> \u2014 respond to student tickets from the dashboard",
        ],
        "cta_label": "Go to Dashboard",
        "cta_path": "/dashboard/",
    },
    "admin": {
        "greeting": "Welcome to GitPulse!",
        "intro": (
            "Your admin account is ready. You have full access to the"
            " platform \u2014 user management, course configuration,"
            " system monitoring, and all teacher tools."
        ),
        "bullets": [
            "<strong>Users</strong> \u2014 manage roles, activate/deactivate accounts",
            "<strong>Courses</strong> \u2014 create and configure courses, import rosters",
            "<strong>System</strong> \u2014 monitor workers, queues, and scheduled jobs",
            "<strong>Analytics</strong> \u2014 view platform-wide analytics and exports",
            "<strong>Security</strong> \u2014 review audit logs and access control settings",
        ],
        "cta_label": "Admin Panel",
        "cta_path": "/dashboard/admin/users",
    },
}


def notify_welcome(
    username: str,
    role: str,
    to_email: str | None = None,
    full_name: str | None = None,
) -> int | None:
    """Send a role-specific welcome email on first login."""
    if not to_email:
        return None

    display_name = full_name or username
    content = _WELCOME_ROLE_CONTENT.get(role, _WELCOME_ROLE_CONTENT["student"])
    base = _base_url()
    cta_url = f"{base}{content['cta_path']}"

    subject = f"[GitPulse] {content['greeting']}"

    # Plain text
    bullet_text = "\n".join(
        f"  \u2022 {b.replace('<strong>', '').replace('</strong>', '')}" for b in content["bullets"]
    )
    text_body = (
        f"Hi {display_name},\n\n"
        f"{content['intro']}\n\n"
        f"Here\u2019s what you can do:\n{bullet_text}\n\n"
        f"{content['cta_label']}: {cta_url}\n\n"
        f"If you have any questions, open a support ticket from the dashboard.\n\n"
        f"\u2014 The GitPulse Team"
    )

    # HTML
    bullet_html = "".join(
        f'<li style="margin:8px 0;color:{_M_TEXT};line-height:1.6;'
        f'font-family:{_MAILER_FONT};">{b}</li>\n'
        for b in content["bullets"]
    )
    html_body = _build_html(
        heading=content["greeting"],
        body_lines=[
            f"Hi <strong>{html.escape(display_name)}</strong>,",
            content["intro"],
            "Here\u2019s what you can do:",
            f'<ul style="padding-left:20px;margin:12px 0;">{bullet_html}</ul>',
            'If you have any questions, open a <a href="'
            f'{html.escape(base)}/dashboard/support" style="color:{_M_LINK};text-decoration:underline;">'
            "support ticket</a> from the dashboard.",
        ],
        action_url=cta_url,
        action_label=content["cta_label"],
        meta_rows=[("Username", username), ("Role", role.title())],
    )

    return enqueue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        category="welcome",
        idempotency_key=_idempotency_key("welcome", username),
        context={"username": username, "role": role},
    )

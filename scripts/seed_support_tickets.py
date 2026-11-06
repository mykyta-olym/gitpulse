"""Seed diverse, rich support tickets and threaded comments for development and testing.

Usage:
    python scripts/seed_support_tickets.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import get_settings
from app.db.session import get_async_session, init_engine
from app.models.course import Course
from app.models.support_comment import SupportComment
from app.models.support_ticket import SupportTicket
from app.models.user import User

SAMPLE_TICKETS = [
    {
        "title": "CI/CD Pipeline runner timeout on R04 test evaluation",
        "category": "ci_cd",
        "priority": "high",
        "status": "in_progress",
        "feedback_type": "bug",
        "rating": 2,
        "free_text": (
            "When running compliance check R04 (Unit Tests) on repository `zsi-team-04/assignment-1`,\n"
            "the runner consistently times out after 10 minutes. The pytest process hangs on database fixture teardown.\n\n"
            "Steps to reproduce:\n"
            "1. Trigger sync from course dashboard\n"
            "2. Observe pipeline run #48231\n"
            "3. Job fails with `Job timeout exceeded`"
        ),
        "improvement_suggestions": "Add configurable runner timeout per check in course settings.",
        "assigned_to": "ac080vs",
        "comments": [
            (
                "ac080vs",
                "I inspected the runner logs. Looks like the PostgreSQL service container wasn't terminating gracefully. Investigating timeout flag.",
                True,
            ),
            (
                "ac080vs",
                "We updated the test harness script to use `pytest -x --timeout=30`. Testing with student repository now.",
                False,
            ),
        ],
    },
    {
        "title": "Merge request review comments not synchronizing to student score",
        "category": "code_reviews",
        "priority": "critical",
        "status": "open",
        "feedback_type": "bug",
        "rating": 1,
        "free_text": (
            "Our team submitted 3 merge requests with in-depth peer reviews in GitLab.\n"
            "However, GitPulse still shows 0% for R08 (Peer Review Participation) for all team members.\n\n"
            "GitLab project: `zsi-2026/team-alpha`\nMRs: !12, !14, !15."
        ),
        "improvement_suggestions": "Show sync diagnostic info in project detail view.",
        "assigned_to": "admin",
        "comments": [
            (
                "admin",
                "Checking the webhook delivery logs. The MR note event might have been rejected due to an outdated secret.",
                True,
            ),
        ],
    },
    {
        "title": "Request to add dark mode syntax theme selector in user preferences",
        "category": "feature_request",
        "priority": "low",
        "status": "resolved",
        "feedback_type": "feature_request",
        "rating": 5,
        "free_text": (
            "It would be great if users could choose their syntax highlighting theme for diffs and code snippets\n"
            "(e.g., Dracula, Monokai, Solarized Dark, or GitHub Dark).\n"
            "Currently only default theme is applied."
        ),
        "improvement_suggestions": "Support Monaco / Prism themes in preferences.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(days=2),
        "comments": [
            (
                "admin",
                "Syntax themes (Monokai, Dracula, Solarized Dark/Light) have been implemented and released in preferences.",
                False,
            ),
        ],
    },
    {
        "title": "GitLab OAuth session expires unexpectedly after 1 hour",
        "category": "account",
        "priority": "medium",
        "status": "open",
        "feedback_type": "support",
        "rating": 3,
        "free_text": (
            "During long lab sessions, students are frequently logged out in the middle of writing evaluations.\n"
            "Can the OAuth token lifetime or refresh token mechanism be extended to 8 hours?"
        ),
        "improvement_suggestions": "Implement automatic background token renewal via refresh token.",
        "assigned_to": None,
        "comments": [],
    },
    {
        "title": "Discrepancy in weekly compliance score calculation for Week 3",
        "category": "evaluations",
        "priority": "high",
        "status": "in_progress",
        "feedback_type": "bug",
        "rating": 2,
        "free_text": (
            "Week 3 deadline passed yesterday at 23:59. Three students pushed commits before the deadline,\n"
            "but their commits are marked as late in GitPulse.\n"
            "Timezone discrepancy between UTC server clock and local CET/CEST timezone seems to be the culprit."
        ),
        "improvement_suggestions": "Always display explicit timezone suffix (e.g. UTC vs Europe/Bratislava) next to deadline timestamps.",
        "assigned_to": "ac080vs",
        "comments": [
            (
                "ac080vs",
                "Verified commit timestamp was 21:58 UTC (23:58 local). Server was evaluating deadline against local time without UTC conversion.",
                True,
            ),
        ],
    },
    {
        "title": "Export course evaluation reports as CSV or XLSX",
        "category": "reports",
        "priority": "medium",
        "status": "resolved",
        "feedback_type": "feature_request",
        "rating": 5,
        "free_text": (
            "Teachers need to submit final student grades to the university academic information system (AIS).\n"
            "An export button for student scores across all weeks in CSV format would save hours of manual entry."
        ),
        "improvement_suggestions": "CSV export with student ID, username, overall score, and check breakdown.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(days=5),
        "comments": [
            (
                "admin",
                "CSV and JSON export has been implemented in Course Analytics / Reports tab.",
                False,
            ),
        ],
    },
    {
        "title": "Repository webhook deliveries returning 401 Unauthorized",
        "category": "repositories",
        "priority": "critical",
        "status": "open",
        "feedback_type": "bug",
        "rating": 1,
        "free_text": (
            "All push events from course group `devops-2026` are failing with HTTP 401 in GitLab Webhook settings.\n"
            "Last delivery response header shows `X-Gitlab-Event: Push Hook` but response body is `Invalid webhook token`."
        ),
        "improvement_suggestions": "Provide a copyable secret with reveal toggle in webhook settings.",
        "assigned_to": "admin",
        "comments": [
            (
                "admin",
                "Reviewing webhook secret rotation log. The previous secret expired after 24h grace period.",
                True,
            ),
        ],
    },
    {
        "title": "Dashboard activity feed does not filter by active course tab",
        "category": "dashboard",
        "priority": "low",
        "status": "closed",
        "feedback_type": "bug",
        "rating": 4,
        "free_text": (
            "On the main dashboard, the recent activity feed lists events from all enrolled courses,\n"
            "even when filtering courses by semester."
        ),
        "improvement_suggestions": "Sync filter tab selection with global activity stream.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(days=10),
        "comments": [
            (
                "admin",
                "Closed as designed - main dashboard activity feed is intentionally global across all memberships.",
                False,
            ),
        ],
    },
    {
        "title": "Student unable to view assigned project details",
        "category": "account",
        "priority": "high",
        "status": "resolved",
        "feedback_type": "support",
        "rating": 4,
        "free_text": (
            "Student `ab004zz` logged in through OAuth but sees 'No projects assigned' on course page,\n"
            "despite being added to team `team-gamma` in GitLab."
        ),
        "improvement_suggestions": "Trigger targeted user sync when a student logs in for the first time.",
        "assigned_to": "ac080vs",
        "resolved_at": datetime.now(UTC) - timedelta(days=1),
        "comments": [
            ("ac080vs", "Ran manual GitLab group sync. Student membership resolved.", False),
        ],
    },
    {
        "title": "Custom regex check R03 fails to match feature branch naming",
        "category": "evaluations",
        "priority": "medium",
        "status": "in_progress",
        "feedback_type": "bug",
        "rating": 3,
        "free_text": (
            "We configured branch naming convention `^(feat|fix|docs)/[a-z0-9-]+$` in course settings.\n"
            "A branch named `feat/user-auth` was marked non-compliant because the validator included the `origin/` remote prefix."
        ),
        "improvement_suggestions": "Strip remote prefixes like `origin/` before validating branch regex.",
        "assigned_to": "ac080vs",
        "comments": [
            (
                "ac080vs",
                "Good catch. The git ref string `refs/heads/feat/user-auth` wasn't being stripped cleanly in the evaluator.",
                True,
            ),
        ],
    },
    {
        "title": "Question regarding AI LLM analysis prompt customization",
        "category": "general",
        "priority": "low",
        "status": "open",
        "feedback_type": "support",
        "rating": 4,
        "free_text": (
            "Is it possible to include specific Slovak university grading rubrics in the system prompt for AI analysis?\n"
            "We want the LLM summary to reference FEI TUKE standards."
        ),
        "improvement_suggestions": "Provide template presets for Slovak/English university syllabi.",
        "assigned_to": None,
        "comments": [],
    },
    {
        "title": "Dead letter queue accumulated 14 failed sync events",
        "category": "repositories",
        "priority": "high",
        "status": "resolved",
        "feedback_type": "bug",
        "rating": 2,
        "free_text": (
            "Admin system page shows 14 failed tasks in DLQ with error `GitLab API 429 Too Many Requests`.\n"
            "These occurred during simultaneous class-wide sync."
        ),
        "improvement_suggestions": "Add exponential backoff with jitter to GitLab API client.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(days=3),
        "comments": [
            (
                "admin",
                "Retried all 14 DLQ items successfully after rate limit window cleared. Backoff logic added.",
                False,
            ),
        ],
    },
    {
        "title": "Suggestion for mobile navigation: quick switch between teams",
        "category": "dashboard",
        "priority": "low",
        "status": "open",
        "feedback_type": "feature_request",
        "rating": 5,
        "free_text": (
            "When viewing project details on a smartphone during lab sessions,\n"
            "it takes too many clicks to go back to course and select another team.\n"
            "A dropdown in the sub-header to jump directly to another team would be fantastic."
        ),
        "improvement_suggestions": "Add team quick-selector dropdown in project header.",
        "assigned_to": None,
        "comments": [],
    },
    {
        "title": "Audit log shows missing actor IP on OAuth callback",
        "category": "account",
        "priority": "medium",
        "status": "closed",
        "feedback_type": "bug",
        "rating": 3,
        "free_text": (
            "Security audit log recorded `actor_ip: null` for several user logins behind reverse proxy Nginx."
        ),
        "improvement_suggestions": "Configure X-Forwarded-For header parsing in trusted proxies middleware.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(days=7),
        "comments": [
            ("admin", "Added Nginx proxy IP to trusted hosts config in production.", False),
        ],
    },
    {
        "title": "Weekly deadline calendar widget doesn't respect Monday start",
        "category": "general",
        "priority": "low",
        "status": "resolved",
        "feedback_type": "bug",
        "rating": 4,
        "free_text": (
            "Flatpickr date picker in course settings was starting on Sunday despite user preference set to Monday."
        ),
        "improvement_suggestions": "Pass user locale / firstDayOfWeek setting to Flatpickr init.",
        "assigned_to": "admin",
        "resolved_at": datetime.now(UTC) - timedelta(hours=12),
        "comments": [
            (
                "admin",
                "Fixed in recent update: user preferences first-day-of-week is now passed to all calendar pickers.",
                False,
            ),
        ],
    },
]


async def seed_support_tickets() -> None:
    settings = get_settings()
    init_engine(str(settings.database_url))

    async for session in get_async_session():
        # Fetch available courses and users
        courses = (await session.execute(select(Course))).scalars().all()
        users = (await session.execute(select(User))).scalars().all()

        course_ids = [c.id for c in courses] if courses else [None]
        usernames = [u.username for u in users] if users else ["student_demo", "teacher_demo"]

        created_count = 0
        now = datetime.now(UTC)

        for i, item in enumerate(SAMPLE_TICKETS):
            assigned = item.get("assigned_to")
            if assigned and assigned not in usernames and usernames:
                assigned = usernames[0]

            sub_user = usernames[(i + 2) % len(usernames)]
            c_id = course_ids[i % len(course_ids)]

            days_ago = (len(SAMPLE_TICKETS) - i) * 1.5
            created_at = now - timedelta(days=days_ago)

            ticket = SupportTicket(
                feedback_token=uuid.uuid4(),
                course_id=c_id,
                feedback_type=item["feedback_type"],
                context_type="course_context" if c_id else "global",
                title=item["title"],
                status=item["status"],
                priority=item["priority"],
                category=item["category"],
                assigned_to=assigned,
                submitted_by=sub_user,
                rating=item.get("rating", 3),
                usefulness_rating=item.get("rating", 3),
                accuracy_rating=item.get("rating", 3),
                time_saved_rating=item.get("rating", 3),
                would_recommend=item.get("rating", 3) >= 3,
                free_text=item["free_text"],
                improvement_suggestions=item.get("improvement_suggestions"),
                submitted_at=created_at,
                updated_at=created_at + timedelta(hours=4),
                resolved_at=item.get("resolved_at"),
                week_number=(i % 12) + 1,
                is_processed=item["status"] in ("resolved", "closed"),
            )
            session.add(ticket)
            await session.flush()

            # Add comments if defined
            for author, content, is_internal in item.get("comments", []):
                comment = SupportComment(
                    ticket_id=ticket.id,
                    author=author,
                    content=content,
                    is_internal=is_internal,
                )
                session.add(comment)

            created_count += 1

        await session.commit()
        print(f"Successfully seeded {created_count} rich support tickets and threaded comments!")
        break


if __name__ == "__main__":
    asyncio.run(seed_support_tickets())

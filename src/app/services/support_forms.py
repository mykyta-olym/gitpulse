"""Service layer for dynamic support forms and ticket management.

Handles CRUD for form definitions, ticket submission/lifecycle,
comments, filtering and response statistics.
"""

from __future__ import annotations

import contextlib
import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.support_form import SupportForm
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.utils.constants import PAGE_SIZE_STATS_MAX

logger = logging.getLogger(__name__)


async def support_assignees(db: AsyncSession, course_id: uuid.UUID | None) -> list[User]:
    """Only active humans who can open this course's ticket may be assigned."""
    from app.models.course_membership import CourseMembership

    members = select(CourseMembership.user_id).where(
        CourseMembership.course_id == course_id,
        CourseMembership.role.in_(("owner", "teacher")),
    )
    result = await db.execute(
        select(User)
        .where(
            User.is_active.is_(True),
            User.is_bot.is_(False),
            (User.role == "admin") | User.id.in_(members),
        )
        .order_by(User.username)
    )
    return list(result.scalars().all())


# Fixed-column fallback map: question IDs that map to dedicated DB columns
# on SupportTicket for pre-JSONB rows (before dynamic forms were introduced).
_FIXED_COLUMN_MAP: dict[str, str] = {
    "rating": "rating",
    "usefulness_rating": "usefulness_rating",
    "accuracy_rating": "accuracy_rating",
    "time_saved_rating": "time_saved_rating",
    "would_recommend": "would_recommend",
    "free_text": "free_text",
    "improvement_suggestions": "improvement_suggestions",
}

# Default questions (mirrors the previously hard-coded form)
DEFAULT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "description",
        "type": "textarea",
        "label": "Description",
        "required": True,
        "config": {"placeholder": "Describe your issue or request..."},
    },
]

DEFAULT_QUESTIONS_BY_CATEGORY: dict[str, list[dict[str, Any]]] = {
    "bug": [
        {
            "id": "bug_url",
            "type": "text",
            "label": "Page URL or location",
            "required": False,
            "config": {"placeholder": "e.g. /dashboard/courses/5 or CI/CD settings"},
        },
        {
            "id": "bug_severity",
            "type": "select",
            "label": "Severity",
            "required": True,
            "config": {
                "options": ["minor", "major", "blocking"],
                "default": "major",
            },
        },
        {
            "id": "bug_browser",
            "type": "text",
            "label": "Browser & OS",
            "required": False,
            "config": {"placeholder": "e.g. Chrome 120, Windows 11"},
        },
        {
            "id": "bug_screen_resolution",
            "type": "text",
            "label": "Screen Resolution (optional)",
            "required": False,
            "config": {"placeholder": "e.g. 1920x1080"},
        },
        {
            "id": "bug_steps",
            "type": "textarea",
            "label": "Steps to Reproduce",
            "required": False,
            "config": {"placeholder": "1. Go to...\n2. Click on...\n3. Observe that..."},
        },
        {
            "id": "bug_expected",
            "type": "textarea",
            "label": "Expected Behavior",
            "required": False,
            "config": {"placeholder": "What did you expect to happen?"},
        },
        {
            "id": "bug_actual",
            "type": "textarea",
            "label": "Actual Behavior",
            "required": False,
            "config": {"placeholder": "What actually happened instead?"},
        },
        {
            "id": "bug_frequency",
            "type": "select",
            "label": "How often does this happen?",
            "required": True,
            "config": {
                "options": ["always", "sometimes", "rarely", "once", "unknown"],
                "default": "always",
            },
        },
        {
            "id": "bug_error_message",
            "type": "text",
            "label": "Error Message (optional)",
            "required": False,
            "config": {"placeholder": "Paste any error message or console output"},
        },
        {
            "id": "bug_workaround",
            "type": "select",
            "label": "Do you have a workaround?",
            "required": True,
            "config": {
                "options": ["yes", "no", "partial"],
                "default": "no",
            },
        },
    ],
    "feature_request": [
        {
            "id": "feature_area",
            "type": "select",
            "label": "Platform Area",
            "required": True,
            "config": {
                "options": [
                    "dashboard",
                    "cicd",
                    "code_review",
                    "evaluation",
                    "repositories",
                    "notifications",
                    "settings",
                    "other",
                ],
                "default": "other",
            },
        },
        {
            "id": "feature_problem",
            "type": "textarea",
            "label": "What problem does this solve?",
            "required": True,
            "config": {"placeholder": "Describe the problem or limitation you are facing..."},
        },
        {
            "id": "feature_solution",
            "type": "textarea",
            "label": "Proposed Solution",
            "required": False,
            "config": {"placeholder": "How would you like this to work?"},
        },
        {
            "id": "feature_alternatives",
            "type": "textarea",
            "label": "Alternatives Considered (optional)",
            "required": False,
            "config": {"placeholder": "Have you considered any alternatives?"},
        },
        {
            "id": "feature_importance",
            "type": "select",
            "label": "How important is this to you?",
            "required": True,
            "config": {
                "options": ["nice_to_have", "important", "critical"],
                "default": "important",
            },
        },
        {
            "id": "feature_users",
            "type": "select",
            "label": "Who would benefit from this?",
            "required": True,
            "config": {
                "options": ["just_me", "my_team", "whole_course", "all_students"],
                "default": "just_me",
            },
        },
    ],
    "account": [
        {
            "id": "account_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "login",
                    "permissions",
                    "enrollment",
                    "profile",
                    "two_factor",
                    "password_reset",
                    "sso",
                    "other",
                ],
                "default": "login",
            },
        },
        {
            "id": "account_username",
            "type": "text",
            "label": "Username or Login (optional)",
            "required": False,
            "config": {"placeholder": "Your university login, e.g. xsmith01"},
        },
        {
            "id": "account_course",
            "type": "text",
            "label": "Affected Course (optional)",
            "required": False,
            "config": {"placeholder": "e.g. ZSI, DSM"},
        },
        {
            "id": "account_error",
            "type": "text",
            "label": "Error Message (optional)",
            "required": False,
            "config": {"placeholder": "Paste the error message you see"},
        },
        {
            "id": "account_when",
            "type": "select",
            "label": "When did this start?",
            "required": True,
            "config": {
                "options": ["today", "yesterday", "recently", "last_week", "always", "unknown"],
                "default": "today",
            },
        },
        {
            "id": "account_tried",
            "type": "select",
            "label": "What have you tried so far?",
            "required": True,
            "config": {
                "options": [
                    "nothing",
                    "restart",
                    "different_browser",
                    "password_reset",
                    "contacted_admin",
                    "other",
                ],
                "default": "nothing",
            },
        },
    ],
    "grade": [
        {
            "id": "grade_assignment",
            "type": "text",
            "label": "Assignment or Activity",
            "required": True,
            "config": {"placeholder": "e.g. Homework 3, Final project"},
        },
        {
            "id": "grade_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "wrong_grade",
                    "missing_grade",
                    "late_submission",
                    "criteria",
                    "regrade",
                    "partial_credit",
                    "bonus",
                    "other",
                ],
                "default": "wrong_grade",
            },
        },
        {
            "id": "grade_expected",
            "type": "text",
            "label": "What grade did you expect?",
            "required": False,
            "config": {"placeholder": "e.g. 90/100 or A"},
        },
        {
            "id": "grade_received",
            "type": "text",
            "label": "What grade did you receive?",
            "required": False,
            "config": {"placeholder": "e.g. 60/100 or C"},
        },
        {
            "id": "grade_submission_date",
            "type": "text",
            "label": "When did you submit? (optional)",
            "required": False,
            "config": {"placeholder": "e.g. March 20, 2026"},
        },
        {
            "id": "grade_justification",
            "type": "textarea",
            "label": "Why do you believe the grade should be different? (optional)",
            "required": False,
            "config": {"placeholder": "Explain your reasoning and reference grading criteria..."},
        },
        {
            "id": "grade_evidence_url",
            "type": "text",
            "label": "Link to submission or evidence (optional)",
            "required": False,
            "config": {"placeholder": "e.g. URL to your repository or submission"},
        },
    ],
    "cicd": [
        {
            "id": "cicd_repo",
            "type": "text",
            "label": "Repository URL",
            "required": True,
            "config": {"placeholder": "e.g. https://gitlab.example.com/user/project"},
        },
        {
            "id": "cicd_branch",
            "type": "text",
            "label": "Branch Name (optional)",
            "required": False,
            "config": {"placeholder": "e.g. main, develop"},
        },
        {
            "id": "cicd_pipeline_id",
            "type": "text",
            "label": "Pipeline or Job ID (optional)",
            "required": False,
            "config": {"placeholder": "e.g. #12345"},
        },
        {
            "id": "cicd_stage",
            "type": "select",
            "label": "Which stage fails?",
            "required": True,
            "config": {
                "options": ["build", "test", "lint", "security", "deploy", "all", "unknown"],
                "default": "unknown",
            },
        },
        {
            "id": "cicd_error",
            "type": "textarea",
            "label": "Error Output",
            "required": False,
            "config": {"placeholder": "Paste the error output from pipeline log..."},
        },
        {
            "id": "cicd_worked_before",
            "type": "select",
            "label": "Did this work before?",
            "required": True,
            "config": {
                "options": ["yes", "yes_after_change", "no", "first_time", "unknown"],
                "default": "unknown",
            },
        },
        {
            "id": "cicd_last_working",
            "type": "text",
            "label": "Last working commit or date (optional)",
            "required": False,
            "config": {"placeholder": "e.g. commit abc123"},
        },
        {
            "id": "cicd_config_file",
            "type": "select",
            "label": "CI configuration file",
            "required": True,
            "config": {
                "options": [
                    "gitlab_ci",
                    "dockerfile",
                    "docker_compose",
                    "makefile",
                    "custom",
                    "unknown",
                ],
                "default": "gitlab_ci",
            },
        },
    ],
    "code_review": [
        {
            "id": "review_mr_url",
            "type": "text",
            "label": "Merge Request URL",
            "required": True,
            "config": {
                "placeholder": "e.g. https://gitlab.example.com/user/project/-/merge_requests/1"
            },
        },
        {
            "id": "review_source_branch",
            "type": "text",
            "label": "Source Branch (optional)",
            "required": False,
            "config": {"placeholder": "e.g. feature/login"},
        },
        {
            "id": "review_target_branch",
            "type": "text",
            "label": "Target Branch (optional)",
            "required": False,
            "config": {"placeholder": "e.g. main"},
        },
        {
            "id": "review_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "not_reviewed",
                    "wrong_feedback",
                    "merge_blocked",
                    "reviewer_assignment",
                    "review_outdated",
                    "approval_missing",
                    "other",
                ],
                "default": "not_reviewed",
            },
        },
        {
            "id": "review_deadline",
            "type": "text",
            "label": "Review Deadline (optional)",
            "required": False,
            "config": {"placeholder": "e.g. April 15, 2026"},
        },
        {
            "id": "review_waited",
            "type": "select",
            "label": "How long have you been waiting?",
            "required": True,
            "config": {
                "options": ["less_than_day", "few_days", "week", "more_than_week"],
                "default": "few_days",
            },
        },
        {
            "id": "review_reviewer",
            "type": "text",
            "label": "Assigned Reviewer (optional)",
            "required": False,
            "config": {"placeholder": "Who was assigned to review?"},
        },
    ],
    "repositories": [
        {
            "id": "repo_url",
            "type": "text",
            "label": "Repository URL",
            "required": True,
            "config": {"placeholder": "e.g. https://gitlab.example.com/user/project"},
        },
        {
            "id": "repo_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "access",
                    "clone",
                    "push",
                    "fork",
                    "missing",
                    "permissions",
                    "settings",
                    "webhook",
                    "other",
                ],
                "default": "access",
            },
        },
        {
            "id": "repo_error",
            "type": "textarea",
            "label": "Error Message (optional)",
            "required": False,
            "config": {"placeholder": "Paste the error you see"},
        },
        {
            "id": "repo_access_method",
            "type": "select",
            "label": "How are you accessing the repository?",
            "required": True,
            "config": {
                "options": ["https", "ssh", "web", "ide", "unknown"],
                "default": "https",
            },
        },
        {
            "id": "repo_git_client",
            "type": "text",
            "label": "Git Client (optional)",
            "required": False,
            "config": {"placeholder": "e.g. VS Code Git"},
        },
        {
            "id": "repo_visibility",
            "type": "select",
            "label": "Repository Visibility",
            "required": True,
            "config": {
                "options": ["private", "internal", "public", "unknown"],
                "default": "unknown",
            },
        },
    ],
    "dashboard": [
        {
            "id": "dashboard_section",
            "type": "select",
            "label": "Which section?",
            "required": True,
            "config": {
                "options": [
                    "overview",
                    "course_analytics",
                    "student_detail",
                    "team_detail",
                    "leaderboard",
                    "charts",
                    "activity_feed",
                    "export",
                    "other",
                ],
                "default": "overview",
            },
        },
        {
            "id": "dashboard_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "wrong_data",
                    "missing_data",
                    "stale_data",
                    "loading",
                    "slow",
                    "display",
                    "crash",
                    "other",
                ],
                "default": "wrong_data",
            },
        },
        {
            "id": "dashboard_page_url",
            "type": "text",
            "label": "Page URL (optional)",
            "required": False,
            "config": {"placeholder": "e.g. /dashboard/courses/5/analytics"},
        },
        {
            "id": "dashboard_browser",
            "type": "text",
            "label": "Browser & OS",
            "required": False,
            "config": {"placeholder": "e.g. Chrome 120, Windows 11"},
        },
        {
            "id": "dashboard_time_range",
            "type": "select",
            "label": "When does this occur?",
            "required": True,
            "config": {
                "options": ["always", "specific_page", "after_action", "intermittent", "unknown"],
                "default": "always",
            },
        },
    ],
    "evaluation": [
        {
            "id": "eval_assignment",
            "type": "text",
            "label": "Assignment or Check Name",
            "required": True,
            "config": {"placeholder": "e.g. Homework 2, Docker config check"},
        },
        {
            "id": "eval_issue_type",
            "type": "select",
            "label": "Issue Type",
            "required": True,
            "config": {
                "options": [
                    "wrong_result",
                    "not_running",
                    "timeout",
                    "criteria",
                    "weight",
                    "partial_score",
                    "recheck",
                    "other",
                ],
                "default": "wrong_result",
            },
        },
        {
            "id": "eval_expected",
            "type": "text",
            "label": "Expected Result",
            "required": False,
            "config": {"placeholder": "What result did you expect?"},
        },
        {
            "id": "eval_actual",
            "type": "text",
            "label": "Actual Result",
            "required": False,
            "config": {"placeholder": "What result did you receive?"},
        },
        {
            "id": "eval_commit",
            "type": "text",
            "label": "Commit SHA or Branch (optional)",
            "required": False,
            "config": {"placeholder": "e.g. abc123"},
        },
        {
            "id": "eval_repo_url",
            "type": "text",
            "label": "Repository URL (optional)",
            "required": False,
            "config": {"placeholder": "e.g. https://gitlab.example.com/user/project"},
        },
        {
            "id": "eval_local_output",
            "type": "textarea",
            "label": "Local Test Output (optional)",
            "required": False,
            "config": {"placeholder": "If the check passes locally but fails on the platform..."},
        },
    ],
    "question": [
        {
            "id": "question_topic",
            "type": "select",
            "label": "Topic",
            "required": True,
            "config": {
                "options": [
                    "how_to",
                    "course_info",
                    "deadline",
                    "requirements",
                    "platform",
                    "setup",
                    "teamwork",
                    "other",
                ],
                "default": "how_to",
            },
        },
        {
            "id": "question_urgency",
            "type": "select",
            "label": "How urgent is your question?",
            "required": True,
            "config": {
                "options": ["no_rush", "soon", "urgent", "blocking"],
                "default": "soon",
            },
        },
        {
            "id": "question_context",
            "type": "text",
            "label": "Related Course or Assignment (optional)",
            "required": False,
            "config": {"placeholder": "e.g. DSM - Homework 3"},
        },
        {
            "id": "question_tried",
            "type": "textarea",
            "label": "What have you already tried? (optional)",
            "required": False,
            "config": {"placeholder": "Describe what you have checked or tried so far..."},
        },
    ],
    "general": [
        {
            "id": "general_topic",
            "type": "select",
            "label": "Topic",
            "required": True,
            "config": {
                "options": [
                    "suggestion",
                    "complaint",
                    "praise",
                    "accessibility",
                    "documentation",
                    "other",
                ],
                "default": "other",
            },
        },
        {
            "id": "general_area",
            "type": "select",
            "label": "Related Platform Area (optional)",
            "required": True,
            "config": {
                "options": [
                    "dashboard",
                    "cicd",
                    "code_review",
                    "evaluation",
                    "courses",
                    "general",
                ],
                "default": "general",
            },
        },
        {
            "id": "general_context",
            "type": "textarea",
            "label": "Additional Context (optional)",
            "required": False,
            "config": {"placeholder": "Any other details that might help us understand..."},
        },
    ],
}


class SupportFormService:
    """CRUD and helpers for dynamic support forms."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        enabled: bool = True,
        anonymize_text: bool = True,
    ) -> None:
        self.db = db
        self.enabled = enabled
        self.anonymize_text = anonymize_text

    # -- Form CRUD ---------------------------------------------------------

    async def list_forms(
        self,
        course_id: uuid.UUID | None = None,
        *,
        active_only: bool = False,
    ) -> list[SupportForm]:
        """Return forms, optionally filtered by course and active status."""
        stmt = select(SupportForm).order_by(SupportForm.created_at.desc())
        if course_id is not None:
            stmt = stmt.where(SupportForm.course_id == course_id)
        if active_only:
            stmt = stmt.where(SupportForm.is_active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_form(self, form_id: uuid.UUID) -> SupportForm | None:
        result = await self.db.execute(select(SupportForm).where(SupportForm.id == form_id))
        return result.scalars().first()

    async def get_active_form(
        self, course_id: uuid.UUID, category: str | None = None
    ) -> SupportForm | None:
        """Return the active form for a course and category (latest if multiple)."""
        stmt = select(SupportForm).where(
            SupportForm.course_id == course_id, SupportForm.is_active.is_(True)
        )
        if category is not None:
            stmt = stmt.where(SupportForm.category == category)
        result = await self.db.execute(stmt.order_by(SupportForm.created_at.desc()).limit(1))
        return result.scalars().first()

    async def get_or_create_default_form(
        self,
        course_id: uuid.UUID,
        category: str = "general",
        username: str = "",
    ) -> SupportForm:
        """Return the active form for a course and category, creating the default if none exists.

        Uses SELECT ... FOR UPDATE on the course row to serialize concurrent callers.
        """
        from app.models.course import Course

        # Lock course row to prevent duplicate default form creation
        await self.db.execute(select(Course.id).where(Course.id == course_id).with_for_update())

        form = await self.get_active_form(course_id, category)
        if form is not None:
            return form

        questions = DEFAULT_QUESTIONS_BY_CATEGORY.get(category, DEFAULT_QUESTIONS)
        title = f"Default {category.replace('_', ' ').title()} Support Form"

        form = SupportForm(
            course_id=course_id,
            category=category,
            title=title,
            description=f"Automatically generated default support form for {category}.",
            questions=questions,
            is_active=True,
            created_by=username or None,
        )
        self.db.add(form)
        await self.db.flush()
        return form

    # -- Dynamic submission ------------------------------------------------

    async def submit_dynamic(
        self,
        token: str,
        form_id: uuid.UUID,
        course_id: uuid.UUID | None,
        support_type: str,
        context_type: str | None,
        responses: dict[str, Any],
        *,
        title: str | None = None,
        priority: str = "medium",
        category: str = "general",
        submitted_by: str | None = None,
    ) -> int:
        """Store a dynamic-form submission as a support ticket.

        Populates ``responses`` JSONB and also writes matching values into
        the fixed rating columns for indexed query support.
        """
        if not self.enabled:
            msg = "Support forms feature is disabled"
            raise RuntimeError(msg)

        try:
            clean_responses = dict(responses)

            # Anonymize text answers
            if self.anonymize_text:
                form = await self.get_form(form_id)
                if form:
                    text_qids = {
                        q["id"]
                        for q in (form.questions or [])
                        if q.get("type") in ("text", "textarea")
                    }
                    for qid in text_qids:
                        if clean_responses.get(qid):
                            clean_responses[qid] = _anonymize_text(str(clean_responses[qid]))

            ticket = SupportTicket(
                feedback_token=uuid.UUID(token),
                course_id=course_id,
                form_id=form_id,
                feedback_type=support_type,
                context_type=context_type,
                title=title,
                status="open",
                priority=priority,
                category=category,
                responses=clean_responses,
                submitted_by=submitted_by or None,
            )

            # Populate fixed rating columns from JSONB for indexed queries
            for qid, col_name in _FIXED_COLUMN_MAP.items():
                if qid in clean_responses:
                    val = clean_responses[qid]
                    if col_name == "would_recommend":
                        if isinstance(val, str):
                            val = val.lower() in ("true", "1", "yes")
                        setattr(ticket, col_name, bool(val))
                    elif col_name in ("free_text", "improvement_suggestions"):
                        setattr(ticket, col_name, str(val) if val else None)
                    else:
                        with contextlib.suppress(TypeError, ValueError):
                            setattr(ticket, col_name, int(val))

            self.db.add(ticket)
            await self.db.flush()
            return int(ticket.id)  # type: ignore[arg-type,unused-ignore]
        except Exception:
            logger.warning("submit_dynamic failed", exc_info=True)
            raise

    # -- Ticket retrieval ------------------------------------------------

    async def get_responses(
        self,
        course_id: uuid.UUID,
        form_id: uuid.UUID | None = None,
        *,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        search: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return support tickets for a course with optional filtering."""
        base = select(SupportTicket).where(SupportTicket.course_id == course_id)
        if form_id is not None:
            base = base.where(SupportTicket.form_id == form_id)
        if status is not None:
            base = base.where(SupportTicket.status == status)
        if priority is not None:
            base = base.where(SupportTicket.priority == priority)
        if category is not None:
            base = base.where(SupportTicket.category == category)
        if search:
            base = base.where(SupportTicket.title.ilike(f"%{search}%"))

        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        rows_result = await self.db.execute(
            base.order_by(SupportTicket.submitted_at.desc()).limit(limit).offset(offset)
        )
        rows = rows_result.scalars().all()

        # Count comments per ticket in one query
        from app.models.support_comment import SupportComment

        ticket_ids = [row.id for row in rows]
        comment_counts: dict[int, int] = {}
        if ticket_ids:
            cc_result = await self.db.execute(
                select(SupportComment.ticket_id, func.count())
                .where(SupportComment.ticket_id.in_(ticket_ids))
                .group_by(SupportComment.ticket_id)
            )
            comment_counts = {int(r[0]): int(r[1]) for r in cc_result.all()}

        items: list[dict[str, Any]] = []
        for row in rows:
            resp: dict[str, Any] = dict(row.responses) if row.responses else {}
            if not resp:
                resp = {}
                for qid, col_name in _FIXED_COLUMN_MAP.items():
                    val = getattr(row, col_name, None)
                    if val is not None:
                        resp[qid] = val
            row_id: int = int(row.id)
            items.append(
                {
                    "id": row_id,
                    "title": row.title,
                    "submitted_by": row.submitted_by or None,
                    "submitted_at": (row.submitted_at.isoformat() if row.submitted_at else None),
                    "support_type": row.feedback_type,
                    "status": row.status or "open",
                    "priority": row.priority or "medium",
                    "category": row.category or "general",
                    "assigned_to": row.assigned_to,
                    "resolved_at": (row.resolved_at.isoformat() if row.resolved_at else None),
                    "updated_at": (row.updated_at.isoformat() if row.updated_at else None),
                    "week_number": row.week_number,
                    "comment_count": comment_counts.get(row_id, 0),
                    "responses": resp,
                }
            )
        return items, total

    # -- Ticket management -------------------------------------------------

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        """Get a single ticket by ID."""

        result = await self.db.execute(
            select(SupportTicket)
            .options(selectinload(SupportTicket.form))
            .where(SupportTicket.id == ticket_id)
        )
        return result.scalars().first()

    async def update_ticket(
        self,
        ticket_id: int,
        **fields: Any,
    ) -> SupportTicket | None:
        """Update ticket metadata (status, priority, category, assignment)."""
        ticket = await self.get_ticket(ticket_id)
        if ticket is None:
            return None

        for key, value in fields.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value or None)

        # Auto-set resolved_at when status changes to resolved/closed

        if fields.get("status") in ("resolved", "closed") and not ticket.resolved_at:
            cast(Any, ticket).resolved_at = datetime.now(UTC)
        elif fields.get("status") in ("open", "in_progress"):
            cast(Any, ticket).resolved_at = None

        cast(Any, ticket).updated_at = datetime.now(UTC)
        await self.db.flush()
        return ticket

    # -- Comments ----------------------------------------------------------

    async def add_comment(
        self,
        ticket_id: int,
        author: str,
        content: str,
        *,
        is_internal: bool = False,
    ) -> Any:
        """Add a comment to a support ticket."""
        from app.models.support_comment import SupportComment

        ticket = await self.get_ticket(ticket_id)
        if ticket is None:
            return None

        comment = SupportComment(
            ticket_id=ticket_id,
            author=author,
            content=content if not self.anonymize_text else _anonymize_text(content),
            is_internal=is_internal,
        )
        self.db.add(comment)
        await self.db.flush()
        return comment

    async def list_comments(
        self,
        ticket_id: int,
        *,
        include_internal: bool = False,
    ) -> list[Any]:
        """List comments for a ticket, optionally including internal notes."""
        from app.models.support_comment import SupportComment

        stmt = (
            select(SupportComment)
            .where(SupportComment.ticket_id == ticket_id)
            .order_by(SupportComment.created_at.asc())
        )
        if not include_internal:
            stmt = stmt.where(SupportComment.is_internal.is_(False))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # -- Response aggregation (statistics) ---------------------------------

    async def get_response_stats(
        self,
        course_id: uuid.UUID,
        form_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Compute per-question aggregate statistics.

        Returns dict with: total_responses, question_stats (per question_id),
        nps_score (if NPS questions exist), sentiment_summary (for text fields).
        """
        items, total = await self.get_responses(
            course_id, form_id, limit=PAGE_SIZE_STATS_MAX, offset=0
        )
        if not total:
            return {"total_responses": 0, "question_stats": {}, "nps_score": None}

        # Load form definition for type info
        form = None
        if form_id:
            form = await self.get_form(form_id)
        if not form:
            form = await self.get_active_form(course_id)
        q_types: dict[str, str] = {}
        if form:
            for q in form.questions or []:
                q_types[q["id"]] = q["type"]

        # Accumulate per-question values
        q_values: dict[str, list[Any]] = {}
        for item in items:
            for qid, val in item.get("responses", {}).items():
                q_values.setdefault(qid, []).append(val)

        question_stats: dict[str, dict[str, Any]] = {}
        nps_scores: list[int] = []

        for qid, values in q_values.items():
            qtype = q_types.get(qid, "")
            stat: dict[str, Any] = {"count": len(values), "type": qtype}

            if qtype in ("rating", "scale", "nps"):
                nums = [v for v in values if isinstance(v, (int, float))]
                if nums:
                    stat["average"] = round(sum(nums) / len(nums), 2)
                    stat["min"] = min(nums)
                    stat["max"] = max(nums)
                    # Distribution
                    dist: dict[int, int] = {}
                    for n in nums:
                        dist[int(n)] = dist.get(int(n), 0) + 1
                    stat["distribution"] = dict(sorted(dist.items()))
                if qtype == "nps":
                    nps_scores.extend(int(v) for v in nums)

            elif qtype == "boolean":
                true_count = sum(1 for v in values if v is True or v == "true")
                false_count = sum(1 for v in values if v is False or v == "false")
                stat["true_count"] = true_count
                stat["false_count"] = false_count
                stat["true_pct"] = round(true_count / len(values) * 100, 1) if values else 0

            elif qtype == "select":
                dist_s: dict[str, int] = {}
                for v in values:
                    dist_s[str(v)] = dist_s.get(str(v), 0) + 1
                stat["distribution"] = dict(sorted(dist_s.items(), key=lambda x: -x[1]))

            elif qtype == "multiselect":
                dist_ms: dict[str, int] = {}
                for v in values:
                    if isinstance(v, list):
                        for item_val in v:
                            dist_ms[str(item_val)] = dist_ms.get(str(item_val), 0) + 1
                    else:
                        dist_ms[str(v)] = dist_ms.get(str(v), 0) + 1
                stat["distribution"] = dict(sorted(dist_ms.items(), key=lambda x: -x[1]))

            elif qtype in ("text", "textarea"):
                texts = [str(v) for v in values if v and str(v).strip()]
                stat["response_count"] = len(texts)
                # Sentiment summary
                sentiments = [analyze_sentiment(t) for t in texts]
                if sentiments:
                    avg_score = round(sum(s["score"] for s in sentiments) / len(sentiments), 2)
                    stat["sentiment"] = {
                        "average_score": avg_score,
                        "positive": sum(1 for s in sentiments if s["label"] == "positive"),
                        "neutral": sum(1 for s in sentiments if s["label"] == "neutral"),
                        "negative": sum(1 for s in sentiments if s["label"] == "negative"),
                    }

            question_stats[qid] = stat

        # NPS score: %Promoters - %Detractors
        nps_result = None
        if nps_scores:
            promoters = sum(1 for s in nps_scores if s >= 9)
            detractors = sum(1 for s in nps_scores if s <= 6)
            n = len(nps_scores)
            nps_result = round((promoters - detractors) / n * 100, 1)

        result: dict[str, Any] = {
            "total_responses": total,
            "question_stats": question_stats,
            "nps_score": nps_result,
        }
        if total > PAGE_SIZE_STATS_MAX:
            result["truncated"] = True
            result["analyzed_responses"] = len(items)
        return result


# -- Helpers -------------------------------------------------------------------


def _anonymize_text(text: str) -> str:
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[EMAIL]", text)
    text = re.sub(r"@\w+", "[MENTION]", text)
    text = re.sub(r"https?://\S+", "[URL]", text)
    return re.sub(r"\b[A-Z]{2,3}\d{5,8}\b", "[ID]", text)


# -- Sentiment helpers -----------------------------------------------------

_POSITIVE_WORDS = frozenset(
    {
        "great",
        "good",
        "excellent",
        "amazing",
        "helpful",
        "useful",
        "love",
        "awesome",
        "fantastic",
        "nice",
        "perfect",
        "best",
        "easy",
        "intuitive",
        "clear",
        "efficient",
        "fast",
        "beautiful",
        "brilliant",
        "outstanding",
        "recommend",
        "saved",
        "enjoy",
        "impressed",
        "wonderful",
        "superb",
        "convenient",
        "reliable",
        "smooth",
        "powerful",
        "elegant",
        "clean",
    }
)
_NEGATIVE_WORDS = frozenset(
    {
        "bad",
        "poor",
        "terrible",
        "awful",
        "slow",
        "confusing",
        "difficult",
        "broken",
        "bug",
        "crash",
        "frustrating",
        "annoying",
        "useless",
        "ugly",
        "complicated",
        "unclear",
        "missing",
        "worse",
        "worst",
        "hate",
        "fails",
        "error",
        "problem",
        "issue",
        "wrong",
        "hard",
        "laggy",
        "clunky",
        "unreliable",
        "inconsistent",
        "painful",
        "disappointing",
    }
)


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Keyword-based sentiment scoring for support text.

    Returns {"score": float (-1..1), "label": "positive"|"negative"|"neutral",
             "positive_count": int, "negative_count": int}.
    """
    if not text or not text.strip():
        return {"score": 0.0, "label": "neutral", "positive_count": 0, "negative_count": 0}

    words = set(re.findall(r"[a-z]+", text.lower()))
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    total = pos + neg

    score = 0.0 if total == 0 else round((pos - neg) / total, 2)

    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"

    return {"score": score, "label": label, "positive_count": pos, "negative_count": neg}

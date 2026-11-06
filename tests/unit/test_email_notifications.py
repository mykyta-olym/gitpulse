"""Unit tests for email notification service.

Covers all notification functions, HTML builder, and SMTP transport via mocks.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest


def _make_settings(**overrides):
    s = MagicMock()
    s.feature_email_notifications = True
    s.smtp_host = "smtp.example.com"
    s.smtp_port = 587
    s.smtp_use_tls = True
    s.smtp_username = "user@example.com"
    s.smtp_password = "secret"
    s.smtp_from_name = "GitPulse"
    s.smtp_from_email = "noreply@example.com"
    s.app_base_url = "https://gitpulse.example.com/"
    s.database_url = "postgresql+asyncpg://localhost/test"
    s.redis_url = "redis://localhost:6379/0"
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


@pytest.fixture(autouse=True)
def _patch_settings():
    """Patch get_settings for the whole module."""
    settings = _make_settings()
    with patch("app.services.email_notifications._get_settings", return_value=settings):
        yield settings


# --- _base_url / _build_ticket_url ---------------------------------------


def test_base_url_strips_trailing_slash():
    from app.services.email_notifications import _base_url

    assert _base_url() == "https://gitpulse.example.com"


def test_build_ticket_url():
    from app.services.email_notifications import _build_ticket_url

    assert _build_ticket_url(42) == "https://gitpulse.example.com/dashboard/support/ticket/42"


# --- _build_html ---------------------------------------------------------


def test_build_html_basic():
    from app.services.email_notifications import _build_html

    result = _build_html(heading="Test", body_lines=["Hello <world>"])
    assert "Test" in result
    assert "Hello &lt;world&gt;" not in result  # body_lines are pre-escaped by caller
    assert "Hello <world>" in result
    assert "GitPulse" in result


def test_build_html_with_action():
    from app.services.email_notifications import _build_html

    result = _build_html(
        heading="H",
        body_lines=["B"],
        action_url="https://example.com/action",
        action_label="Click Me",
    )
    assert "https://example.com/action" in result
    assert "Click Me" in result


def test_build_html_with_meta_rows():
    from app.services.email_notifications import _build_html

    result = _build_html(
        heading="H",
        body_lines=[],
        meta_rows=[("Label", "Value"), ("Key", "Data")],
    )
    assert "<strong>Label</strong>" in result
    assert "Value" in result
    assert "<strong>Key</strong>" in result


def test_build_html_no_action_no_meta():
    from app.services.email_notifications import _build_html

    result = _build_html(heading="Simple", body_lines=["para"])
    assert "Simple" in result
    assert "para" in result
    # No CTA button
    assert "inline-block" not in result


# --- _send_email removed - function deleted as dead code (queue-based delivery only) ---


# --- Ticket notifications -----------------------------------------------


class TestTicketNotifications:
    def test_ticket_created_no_email(self):
        from app.services.email_notifications import notify_ticket_created

        assert notify_ticket_created(1, "Bug", "bug") is None

    def test_ticket_created_sends(self):
        from app.services.email_notifications import notify_ticket_created

        with patch("app.services.email_notifications.enqueue_email", return_value=42) as m:
            assert notify_ticket_created(1, "Bug", "bug", to_email="u@x.com") == 42
        m.assert_called_once()
        assert m.call_args.kwargs["to_email"] == "u@x.com"
        assert "#1" in m.call_args.kwargs["subject"]

    def test_ticket_comment_no_email(self):
        from app.services.email_notifications import notify_ticket_comment

        assert notify_ticket_comment(1, "t", "a", "c") is None

    def test_ticket_comment_sends(self):
        from app.services.email_notifications import notify_ticket_comment

        with patch("app.services.email_notifications.enqueue_email", return_value=43) as m:
            assert notify_ticket_comment(1, "t", "a", "body", to_email="u@x.com") == 43
        m.assert_called_once()

    def test_ticket_comment_long_body_truncated(self):
        from app.services.email_notifications import notify_ticket_comment

        long_text = "x" * 600
        with patch("app.services.email_notifications.enqueue_email", return_value=44) as m:
            notify_ticket_comment(1, "t", "a", long_text, to_email="u@x.com")
        # The text_body passed should contain truncated content
        assert "\u2026" in m.call_args.kwargs["text_body"]

    def test_ticket_assignment_no_email(self):
        from app.services.email_notifications import notify_ticket_assignment

        assert notify_ticket_assignment(1, "t", "admin") is None

    def test_ticket_assignment_sends(self):
        from app.services.email_notifications import notify_ticket_assignment

        with patch("app.services.email_notifications.enqueue_email", return_value=45) as m:
            assert notify_ticket_assignment(1, "t", "admin", to_email="u@x.com") == 45
        m.assert_called_once()

    def test_ticket_status_change_no_email(self):
        from app.services.email_notifications import notify_ticket_status_change

        assert notify_ticket_status_change(1, "t", "resolved") is None

    def test_ticket_status_change_sends(self):
        from app.services.email_notifications import notify_ticket_status_change

        with patch("app.services.email_notifications.enqueue_email", return_value=46) as m:
            assert notify_ticket_status_change(1, "t", "in_progress", to_email="u@x.com") == 46
        m.assert_called_once()
        assert "In Progress" in m.call_args.kwargs["subject"]


# --- User management notifications --------------------------------------


class TestUserNotifications:
    def test_role_change_no_email(self):
        from app.services.email_notifications import notify_role_change

        assert notify_role_change("u", "student", "teacher", "admin") is None

    def test_role_change_sends(self):
        from app.services.email_notifications import notify_role_change

        with patch("app.services.email_notifications.enqueue_email", return_value=50) as m:
            result = notify_role_change("u", "student", "teacher", "admin", to_email="u@x.com")
            assert result == 50
        m.assert_called_once()
        assert "teacher" in m.call_args.kwargs["subject"]

    def test_account_reactivated_no_email(self):
        from app.services.email_notifications import notify_account_reactivated

        assert notify_account_reactivated("u", "admin") is None

    def test_account_reactivated_sends(self):
        from app.services.email_notifications import notify_account_reactivated

        with patch("app.services.email_notifications.enqueue_email", return_value=51) as m:
            assert notify_account_reactivated("u", "admin", to_email="u@x.com") == 51
        m.assert_called_once()


# --- Course management notifications ------------------------------------


class TestCourseNotifications:
    def test_teacher_assigned_no_email(self):
        from app.services.email_notifications import notify_teacher_assigned_to_course

        assert notify_teacher_assigned_to_course("t", "CS101", "Intro", "admin") is None

    def test_teacher_assigned_sends(self):
        from app.services.email_notifications import notify_teacher_assigned_to_course

        cid = uuid.uuid4()
        with patch("app.services.email_notifications.enqueue_email", return_value=60) as m:
            assert (
                notify_teacher_assigned_to_course(
                    "t", "CS101", "Intro", "admin", course_id=cid, to_email="t@x.com"
                )
                == 60
            )
        m.assert_called_once()
        assert "CS101" in m.call_args.kwargs["subject"]
        assert str(cid) in m.call_args.kwargs["html_body"]

    def test_teacher_assigned_no_course_id(self):
        from app.services.email_notifications import notify_teacher_assigned_to_course

        with patch("app.services.email_notifications.enqueue_email", return_value=61) as m:
            notify_teacher_assigned_to_course("t", "CS101", "Intro", "admin", to_email="t@x.com")
        # Falls back to dashboard URL
        assert "/dashboard" in m.call_args.kwargs["html_body"]

    def test_course_archived_no_email(self):
        from app.services.email_notifications import notify_course_archived

        assert notify_course_archived("CS101", "Intro", "admin") is None

    def test_course_archived_sends(self):
        from app.services.email_notifications import notify_course_archived

        with patch("app.services.email_notifications.enqueue_email", return_value=62) as m:
            assert notify_course_archived("CS101", "Intro", "admin", to_email="s@x.com") == 62
        m.assert_called_once()

    def test_course_reactivated_no_email(self):
        from app.services.email_notifications import notify_course_reactivated

        assert notify_course_reactivated("CS101", "Intro", "admin") is None

    def test_course_reactivated_sends(self):
        from app.services.email_notifications import notify_course_reactivated

        cid = uuid.uuid4()
        with patch("app.services.email_notifications.enqueue_email", return_value=63) as m:
            assert (
                notify_course_reactivated(
                    "CS101", "Intro", "admin", course_id=cid, to_email="s@x.com"
                )
                == 63
            )
        m.assert_called_once()
        assert str(cid) in m.call_args.kwargs["html_body"]

    def test_course_reactivated_no_course_id(self):
        from app.services.email_notifications import notify_course_reactivated

        with patch("app.services.email_notifications.enqueue_email", return_value=64) as m:
            notify_course_reactivated("CS101", "Intro", "admin", to_email="s@x.com")
        assert "/dashboard" in m.call_args.kwargs["html_body"]


# --- Welcome email ------------------------------------------------------


class TestWelcomeEmail:
    def test_welcome_no_email_returns_none(self):
        from app.services.email_notifications import notify_welcome

        assert notify_welcome("alice", "student", to_email=None) is None
        assert notify_welcome("alice", "student", to_email="") is None

    def test_welcome_student_sends(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=70) as m:
            result = notify_welcome("alice", "student", to_email="a@x.com")
        assert result == 70
        assert m.call_args.kwargs["category"] == "welcome"
        assert "Dashboard" in m.call_args.kwargs["html_body"]
        assert "alice" in m.call_args.kwargs["text_body"]

    def test_welcome_teacher_sends(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=71) as m:
            result = notify_welcome("bob", "teacher", to_email="b@x.com")
        assert result == 71
        assert "Courses" in m.call_args.kwargs["html_body"]
        assert "Checks" in m.call_args.kwargs["html_body"]

    def test_welcome_admin_sends(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=72) as m:
            result = notify_welcome("root", "admin", to_email="r@x.com")
        assert result == 72
        assert "Users" in m.call_args.kwargs["html_body"]
        assert "Security" in m.call_args.kwargs["html_body"]

    def test_welcome_unknown_role_falls_back_to_student(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=73) as m:
            result = notify_welcome("eve", "ta", to_email="e@x.com")
        assert result == 73
        assert "Dashboard" in m.call_args.kwargs["html_body"]

    def test_welcome_uses_full_name_when_provided(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=74) as m:
            notify_welcome("alice", "student", to_email="a@x.com", full_name="Alice Smith")
        assert "Alice Smith" in m.call_args.kwargs["html_body"]
        assert "Alice Smith" in m.call_args.kwargs["text_body"]

    def test_welcome_idempotency_key_by_username(self):
        from app.services.email_notifications import notify_welcome

        with patch("app.services.email_notifications.enqueue_email", return_value=75) as m:
            notify_welcome("alice", "student", to_email="a@x.com")
        idem = m.call_args.kwargs["idempotency_key"]
        assert idem  # non-empty
        # Same username -> same key (idempotency)
        with patch("app.services.email_notifications.enqueue_email", return_value=76) as m2:
            notify_welcome("alice", "student", to_email="a@x.com")
        assert m2.call_args.kwargs["idempotency_key"] == idem


class TestNotificationOptOutIsEnforcedOnEveryPath:
    """One persistence function enforces preferences for every caller.

    Inspect the AST so a mention inside a docstring cannot pass as a check.
    """

    @staticmethod
    def _enqueue_tree():
        import ast
        import inspect

        from app.services import email_notifications

        source = inspect.getsource(email_notifications)
        return ast.parse(source)

    def test_the_single_persistence_path_calls_the_opt_out_as_code(self) -> None:
        import ast

        tree = self._enqueue_tree()
        found = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("_persist_with"):
                found[node.name] = [
                    call
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and getattr(call.func, "id", "") == "_recipient_opted_out"
                ]
        assert len(found) == 1, f"expected one persistence path, found {sorted(found)}"
        for name, calls in found.items():
            assert calls, (
                f"{name} never CALLS _recipient_opted_out - a mention inside a "
                "docstring or comment does not gate anything"
            )

    def test_every_opt_out_column_exists_on_the_model(self) -> None:
        from app.models.user import User
        from app.services.email_notifications import NOTIFICATION_OPT_OUTS

        for category, column in NOTIFICATION_OPT_OUTS.items():
            assert hasattr(User, column), (
                f"category {category!r} maps to User.{column}, which does not exist"
            )

    def test_every_opt_out_column_is_offered_on_the_preferences_page(self) -> None:
        """A switch the server honours but the page never shows is unreachable."""
        from app.api.dashboard.preferences import PREFERENCE_FIELDS
        from app.services.email_notifications import NOTIFICATION_OPT_OUTS

        offered = {f.name for f in PREFERENCE_FIELDS}
        missing = set(NOTIFICATION_OPT_OUTS.values()) - offered
        assert not missing, f"enforced but not offered anywhere: {sorted(missing)}"

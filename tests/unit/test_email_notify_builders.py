"""Coverage for every ``notify_*`` email builder in email_notifications.

Each builder is a thin function: return ``None`` when there is no recipient,
otherwise build subject/text/HTML bodies and hand off to ``enqueue_email``.
We patch ``enqueue_email`` (so nothing touches Redis/DB/SMTP) and assert both
branches - the valid-recipient path returns the enqueued id, and the
missing-recipient path short-circuits to ``None``.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services import email_notifications as en


def _settings() -> MagicMock:
    s = MagicMock()
    s.feature_email_notifications = True
    s.app_base_url = "https://gitpulse.example.com/"
    s.smtp_from_name = "GitPulse"
    s.smtp_from_email = "noreply@example.com"
    return s


@pytest.fixture(autouse=True)
def enqueue_mock():
    with (
        patch("app.services.email_notifications._get_settings", return_value=_settings()),
        patch("app.services.email_notifications.enqueue_email", return_value=4242) as enq,
    ):
        yield enq


# (callable, kwargs-with-recipient) for every notify_* builder.
_TO = "person@example.com"
_BUILDERS = [
    (en.notify_ticket_created, {"ticket_id": 1, "title": "T", "category": "bug", "to_email": _TO}),
    (
        en.notify_ticket_new_to_staff,
        {
            "ticket_id": 1,
            "title": "T",
            "category": "bug",
            "submitted_by": "stu",
            "course_code": "DEVOPS",
            "to_email": _TO,
        },
    ),
    (
        en.notify_ticket_comment,
        {"ticket_id": 1, "title": "T", "author": "a", "comment_content": "hi", "to_email": _TO},
    ),
    (
        en.notify_ticket_assignment,
        {"ticket_id": 1, "title": "T", "assigned_by": "boss", "to_email": _TO},
    ),
    (
        en.notify_ticket_status_change,
        {"ticket_id": 1, "title": "T", "new_status": "resolved", "to_email": _TO},
    ),
    (
        en.notify_role_change,
        {
            "username": "u",
            "old_role": "student",
            "new_role": "teacher",
            "changed_by": "admin",
            "to_email": _TO,
        },
    ),
    (
        en.notify_account_reactivated,
        {"username": "u", "reactivated_by": "admin", "to_email": _TO},
    ),
    (
        en.notify_teacher_assigned_to_course,
        {
            "teacher_username": "t",
            "course_code": "DEVOPS",
            "course_name": "DevOps",
            "assigned_by": "admin",
            "course_id": uuid.uuid4(),
            "to_email": _TO,
        },
    ),
    (
        en.notify_course_archived,
        {"course_code": "DEVOPS", "course_name": "DevOps", "archived_by": "admin", "to_email": _TO},
    ),
    (
        en.notify_course_reactivated,
        {
            "course_code": "DEVOPS",
            "course_name": "DevOps",
            "reactivated_by": "admin",
            "course_id": 7,
            "to_email": _TO,
        },
    ),
    (
        en.notify_welcome,
        {"username": "u", "role": "student", "to_email": _TO, "full_name": "U Ser"},
    ),
]


@pytest.mark.parametrize(("func", "kwargs"), _BUILDERS, ids=[f.__name__ for f, _ in _BUILDERS])
def test_builder_enqueues_when_recipient_present(func, kwargs, enqueue_mock) -> None:
    result = func(**kwargs)
    assert result == 4242
    assert enqueue_mock.call_count == 1
    # The enqueued email carries a real subject + non-empty bodies.
    call_kwargs = enqueue_mock.call_args.kwargs
    assert call_kwargs["to_email"] == _TO
    assert call_kwargs["subject"]
    assert call_kwargs["html_body"]
    assert call_kwargs["text_body"]


# Builders that accept an optional recipient must short-circuit to None.
_OPTIONAL_RECIPIENT = [
    (en.notify_ticket_created, {"ticket_id": 1, "title": "T", "category": "bug"}),
    (
        en.notify_ticket_comment,
        {"ticket_id": 1, "title": "T", "author": "a", "comment_content": "x"},
    ),
    (en.notify_ticket_assignment, {"ticket_id": 1, "title": "T", "assigned_by": "b"}),
    (en.notify_ticket_status_change, {"ticket_id": 1, "title": "T", "new_status": "open"}),
    (
        en.notify_role_change,
        {"username": "u", "old_role": "student", "new_role": "teacher", "changed_by": "a"},
    ),
    (en.notify_account_reactivated, {"username": "u", "reactivated_by": "a"}),
    (en.notify_course_archived, {"course_code": "C", "course_name": "N", "archived_by": "a"}),
    (en.notify_welcome, {"username": "u", "role": "student"}),
]


@pytest.mark.parametrize(
    ("func", "kwargs"), _OPTIONAL_RECIPIENT, ids=[f.__name__ for f, _ in _OPTIONAL_RECIPIENT]
)
def test_builder_returns_none_without_recipient(func, kwargs, enqueue_mock) -> None:
    assert func(**kwargs) is None
    assert enqueue_mock.call_count == 0

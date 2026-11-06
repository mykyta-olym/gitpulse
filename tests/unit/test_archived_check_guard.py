"""Archived courses must be read-only for check mutations.

The settings-save endpoint already rejected archived courses, but the check
mutation endpoints (create/update/delete custom check, update check, import)
did not, leaving an archived course's checks editable through the API while the
UI dimmed the buttons. `_archived_block` is the shared guard now called by each
of those endpoints.
"""

from types import SimpleNamespace

from starlette.responses import JSONResponse

from app.api.dashboard.courses.checks import _archived_block


def test_active_course_is_not_blocked() -> None:
    course = SimpleNamespace(is_active=True)
    assert _archived_block(course) is None


def test_archived_course_is_blocked_with_409() -> None:
    course = SimpleNamespace(is_active=False)
    resp = _archived_block(course)
    assert isinstance(resp, JSONResponse)
    assert resp.status_code == 409


def test_block_message_tells_the_user_to_reactivate() -> None:
    resp = _archived_block(SimpleNamespace(is_active=False))
    assert resp is not None
    assert b"archived" in resp.body.lower()
    assert b"reactivate" in resp.body.lower()

"""Reactivating a course says that its webhooks are still switched off.

Archiving a course deactivates every webhook configuration it owns, and
reactivating deliberately leaves them off - the operator decides which scopes
still apply. That decision is documented in `_deactivate_course_webhooks` and it
is a reasonable one. What was missing is that nothing said so at the moment it
matters: a reactivated course looks live, and GitLab keeps getting 401 for every
delivery.

Found exactly that way while clicking the lifecycle through: archive the demo
course, reactivate it, and every webhook - issue, push, merge request, pipeline -
came back 401 with the configuration silently inactive.

The archive already logs `course_webhooks_deactivated`. The reactivation now
logs the other half, with the count and what to do about it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SERVICE = Path(__file__).resolve().parents[2] / "src/app/services/courses.py"


@pytest.fixture(scope="module")
def src() -> str:
    return SERVICE.read_text(encoding="utf-8")


def test_the_archive_still_switches_them_off(src: str) -> None:
    """The behaviour this warning is about - if it ever stops, the warning is
    wrong rather than merely unnecessary."""
    assert "async def _deactivate_course_webhooks" in src
    assert "course_webhooks_deactivated" in src, "the archive no longer logs what it turned off"


def test_activation_counts_what_is_still_disabled(src: str) -> None:
    activate = src.split("async def activate_course", 1)[1].split("\nasync def ", 1)[0]
    assert "WebhookConfiguration" in activate, (
        "reactivation does not look at the configurations the archive disabled"
    )
    assert re.search(r"is_active\.is_\(False\)", activate), (
        "it should count the INACTIVE configurations - the ones that stay dead"
    )
    assert "course_activated_webhooks_still_disabled" in activate


def test_the_message_says_what_to_do(src: str) -> None:
    activate = src.split("async def activate_course", 1)[1].split("\nasync def ", 1)[0]
    block = activate.split("course_activated_webhooks_still_disabled", 1)[1][:500]
    assert "count=" in block, "the number of dead configurations is not reported"
    assert "401" in block, "the log line does not say what the reader will see"
    assert "course settings" in block, "the log line does not say where to fix it"

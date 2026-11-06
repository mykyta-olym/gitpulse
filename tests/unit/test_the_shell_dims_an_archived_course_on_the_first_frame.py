"""An archived course's write actions are dimmed on the FIRST frame, everywhere.

`tab_content()` marks the content well `is-course-archived` from the server,
so the guarded buttons inside it never paint in their real colours. The page
HEADER actions - Add Group, Import from GitLab, Sync All, Run Checks - live in
the page shell, outside that well, and were dimmed only by the read-only guard
in core/48-archived-course.js adding the same class to `#main-content` after the
deferred bundle ran. Measured with the bundle held back: on a full load or
reload of an archived course all four painted as available, under a banner
saying "read-only", and greyed a beat later.

base.html now emits the class on `#main-content` itself whenever the page's
`course` is archived. The guard keeps owning the tooltip, the click answer and
clearing the class after an SPA swap to a page that is not archived - it still
toggles the same element.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "src/app/templates/base.html"
GUARD = REPO / "src/app/templates/static/js/_parts/core/48-archived-course.js"


def _main_tag() -> str:
    src = BASE.read_text(encoding="utf-8")
    match = re.search(r"<main id=\"main-content\"[^>]*>", src)
    assert match, "base.html lost its #main-content element"
    return match.group(0)


def test_the_content_well_is_marked_archived_by_the_server() -> None:
    tag = _main_tag()
    assert "is-course-archived" in tag, (
        "the shell no longer dims the page-header actions of an archived course "
        "on the first frame - they paint as available until the guard runs"
    )
    assert "not course.is_active" in tag, "the class is not keyed on the course being archived"


def test_a_page_without_a_course_is_never_marked() -> None:
    tag = _main_tag()
    assert "course is defined" in tag, (
        "base.html reads `course` unguarded - every page without one would fail to render"
    )


def test_the_guard_still_toggles_the_same_element() -> None:
    """The server sets the class; the guard clears it after an SPA swap to an
    active page and re-applies it on the way back. Both have to agree on the
    element or a stale class outlives its page."""
    src = GUARD.read_text(encoding="utf-8")
    host = src.split("function _readOnlyHost()", 1)[1].split("}", 1)[0]
    assert "getElementById('main-content')" in host

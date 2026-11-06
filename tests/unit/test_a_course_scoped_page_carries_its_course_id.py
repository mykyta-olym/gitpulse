"""Every course-scoped page exposes its id to live refresh and action guards.

The read-only marker belongs only to archived pages; the course identity is
needed on both active and archived pages.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def render():
    sys.path.insert(0, str(REPO / "src"))
    from app.main import templates as app_templates

    def _render(course) -> str:
        body = (
            '{% from "components/layout.html" import tab_content %}'
            "{% call tab_content(course) %}CONTENT{% endcall %}"
        )
        return app_templates.env.from_string(body).render(
            course=course, t=lambda s, **k: s, request=None
        )

    return _render


def test_an_active_course_page_names_its_course(render) -> None:
    html = render(SimpleNamespace(id="0da061ac-c7e7-472a-a2c6-9387a60d7c45", is_active=True))
    assert 'data-course-id="0da061ac-c7e7-472a-a2c6-9387a60d7c45"' in html, (
        "an active course-scoped page carries no course id - live refresh and "
        "anything else that looks for one finds nothing"
    )
    assert "data-course-archived" not in html
    assert "is-course-archived" not in html


def test_an_archived_course_page_still_announces_the_lock(render) -> None:
    html = render(SimpleNamespace(id="c9d04dde-bbfc-41ed-be19-87ff67cb0db2", is_active=False))
    assert 'data-course-id="c9d04dde-bbfc-41ed-be19-87ff67cb0db2"' in html
    assert 'data-course-archived="1"' in html, "the read-only guard lost its announcement"
    assert "is-course-archived" in html, "the CSS that dims the guarded buttons lost its class"


def test_a_page_with_no_course_claims_none(render) -> None:
    html = render(None)
    assert "data-course-id" not in html
    assert "data-course-archived" not in html
    assert "CONTENT" in html

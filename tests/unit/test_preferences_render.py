"""Render the preferences page end to end, for every role.

The contract tests hold the field table; this holds the page. The failure it
exists to catch is the one that actually reaches a reader - the page 500s
because a template touches a macro or attribute that no longer exists - and it
runs for student, teacher and admin because this page is the one surface in the
app that every role shares.
"""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request

from app.api.dashboard._helpers import _templates
from app.api.dashboard.preferences import (
    PREFERENCE_FIELDS,
    SUGGESTED_DIFF_COLORS,
    current_preferences,
)
from app.i18n import get_template_i18n_context
from app.models.user import User

ROLES = ("student", "teacher", "admin")


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/dashboard/preferences",
            "raw_path": b"/dashboard/preferences",
            "query_string": b"",
            "headers": [],
            "root_path": "",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 1),
            "app": None,
        }
    )


def _render(role: str, user: User | None = None) -> str:
    request = _request()
    subject = user if user is not None else User()
    context: dict[str, Any] = {
        "request": request,
        "fields": PREFERENCE_FIELDS,
        "prefs": current_preferences(subject),
        "defaults": {f.name: f.default for f in PREFERENCE_FIELDS},
        "suggested_diff_colors": SUGGESTED_DIFF_COLORS,
        "csrf_token": "test-csrf",
        "csp_nonce": "test-nonce",
        "is_admin": role == "admin",
        "is_teacher": role in {"teacher", "admin"},
        "user_role": role,
        **get_template_i18n_context(request),
    }
    return _templates(request).env.get_template("preferences.html").render(**context)


@pytest.fixture(scope="module")
def rendered() -> str:
    return _render("teacher")


@pytest.mark.parametrize("role", ROLES)
def test_page_renders_for_every_role(role: str) -> None:
    """These are the reader's OWN settings - no role may be refused the page."""
    html = _render(role)
    assert len(html) > 3_000, f"{role} got a suspiciously short page"
    assert 'id="preferencesForm"' in html


@pytest.mark.parametrize("field", PREFERENCE_FIELDS, ids=lambda f: f.name)
def test_every_field_reaches_the_page(rendered: str, field: Any) -> None:
    """theme_preference is the deliberate exception: the Mode section renders
    the shared theme switcher, which persists itself through its own endpoint,
    so it is not one of the form's saved inputs."""
    if field.name == "theme_preference":
        assert "data-theme-value" in rendered
        return
    assert f'name="{field.name}"' in rendered


@pytest.mark.parametrize("field", PREFERENCE_FIELDS, ids=lambda f: f.name)
def test_every_choice_reaches_the_page(rendered: str, field: Any) -> None:
    """Only the choices THIS role may pick - the fixture renders as a teacher."""
    if field.name == "theme_preference":
        pytest.skip("rendered by the shared theme switcher, not as form inputs")
    for choice in field.choices_for("teacher"):
        if choice.value == "":
            continue  # the "follow my browser" option has an empty value
        assert choice.value in rendered, f"{field.name}={choice.value} missing"


@pytest.mark.parametrize("role", ROLES)
def test_role_restricted_choices_are_not_rendered(role: str) -> None:
    """A page that OFFERS a destination the role gate would refuse teaches the
    reader to distrust the setting."""
    html = _render(role)
    field = next(f for f in PREFERENCE_FIELDS if f.name == "default_homepage")
    for choice in field.choices:
        if choice.allowed_for(role):
            assert choice.value in html, f"{role} should be offered {choice.value}"
        else:
            assert f'value="{choice.value}"' not in html, (
                f"{role} was offered {choice.value}, which they cannot open"
            )


def test_a_student_is_offered_no_admin_destination() -> None:
    html = _render("student")
    for admin_only in ("admin-courses", "admin-system", "admin-users"):
        assert f'value="{admin_only}"' not in html


def test_mode_section_reuses_the_shared_switcher(rendered: str) -> None:
    """One control per interaction: a second radio group for the colour mode
    would double-write on save, because the switcher already persists."""
    assert "theme-switcher" in rendered
    assert 'name="theme_preference"' not in rendered


def test_sections_match_gitlabs_preferences(rendered: str) -> None:
    for anchor in ("mode", "accent-theme", "behavior", "localization", "time-preferences"):
        assert f'id="{anchor}"' in rendered, f"section #{anchor} missing"


def test_stored_values_are_reflected(rendered: str) -> None:
    user = User()
    user.layout_width = "fluid"
    user.use_relative_times = False
    html = _render("student", user)
    # The chosen radio carries `checked`; find it on the fluid input only.
    fluid = html.split('value="fluid"')[1][:200]
    assert "checked" in fluid
    # An unchecked box must not render `checked` at all.
    box = html.split('name="use_relative_times"')[1][:200]
    assert "checked" not in box


def test_page_loads_its_script_and_config(rendered: str) -> None:
    # static_url() resolves to the .min sibling when one has been built, so
    # match the stem rather than the exact filename.
    assert "js/pages/preferences" in rendered
    assert 'id="gp-page-config"' in rendered
    assert "/dashboard/api/preferences" in rendered


def test_no_native_title_tooltips(rendered: str) -> None:
    """The app uses Tippy via data-tippy-content; a raw title= is rejected."""
    assert " title=" not in rendered


def test_every_string_on_the_page_has_a_slovak_translation() -> None:
    """Slovak is the DEFAULT locale, so an untranslated string is what most
    readers actually see. The page first shipped 26 of its 29 strings in
    English; this stops that recurring.
    """
    import json
    import re
    from pathlib import Path

    catalog = json.loads(
        (Path(__file__).resolve().parents[2] / "src/app/i18n/catalogs/sk.json").read_text(
            encoding="utf-8"
        )
    )
    template = (
        Path(__file__).resolve().parents[2] / "src/app/templates/preferences.html"
    ).read_text(encoding="utf-8")

    missing = sorted(s for s in set(re.findall(r"t\('([^']+)'\)", template)) if s not in catalog)
    assert not missing, f"untranslated on the Preferences page: {missing}"


def test_every_choice_label_has_a_slovak_translation() -> None:
    """The labels come from Python but are rendered through t(), so they need
    catalogue entries exactly like the template's own strings."""
    import json
    from pathlib import Path

    catalog = json.loads(
        (Path(__file__).resolve().parents[2] / "src/app/i18n/catalogs/sk.json").read_text(
            encoding="utf-8"
        )
    )
    missing = []
    for field in PREFERENCE_FIELDS:
        for choice in field.choices:
            for text in (choice.label, choice.description):
                if text and text not in catalog:
                    missing.append(text)
    assert not missing, f"untranslated preference choices: {sorted(set(missing))}"


def test_every_page_anchor_has_a_tour_step_and_vice_versa() -> None:
    """The tour was written before the Diffs and Notifications sections existed
    and silently fell behind: the page carried anchors nothing walked to. A step
    pointing at a missing anchor is worse - compileSteps drops it, so the tour
    quietly gets shorter instead of failing."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    template = (root / "src/app/templates/preferences.html").read_text(encoding="utf-8")
    tour = (root / "src/app/templates/static/js/_parts/tours/50-preferences.js").read_text(
        encoding="utf-8"
    )

    anchors = set(re.findall(r'data-tour="(preferences-[a-z]+)"', template))
    steps = set(re.findall(r'\[data-tour~="(preferences-[a-z]+)"\]', tour))

    assert not anchors - steps, f"page anchors with no tour step: {sorted(anchors - steps)}"
    assert not steps - anchors, f"tour steps pointing at nothing: {sorted(steps - anchors)}"


def test_the_tour_is_bilingual_throughout() -> None:
    """A step missing its Slovak copy falls back to English mid-tour, which is
    worse than not translating it at all."""
    import re
    from pathlib import Path

    tour = (
        Path(__file__).resolve().parents[2]
        / "src/app/templates/static/js/_parts/tours/50-preferences.js"
    ).read_text(encoding="utf-8")

    for field in ("title", "body"):
        en = len(re.findall(rf"{field}_en:", tour))
        sk = len(re.findall(rf"{field}_sk:", tour))
        assert en == sk, f"{field}: {en} English vs {sk} Slovak"

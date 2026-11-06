"""The preferences endpoint's validation contract.

The page and the endpoint are driven by one table (``PREFERENCE_FIELDS``), so
these tests hold that table to three promises:

* every option the form can render is a value the endpoint accepts;
* a key outside the table is refused rather than written - this endpoint takes
  user input and calls ``setattr`` on a User, which is exactly the shape of the
  mass-assignment finding that keeps recurring in review here;
* the defaults describe the behaviour the app had before the page existed, so
  an untouched account behaves identically.
"""

from __future__ import annotations

import pytest

from app.api.dashboard.preferences import (
    PREFERENCE_FIELDS,
    Choice,
    PreferenceField,
    current_preferences,
)
from app.models.user import User

FIELDS_BY_NAME = {f.name: f for f in PREFERENCE_FIELDS}


def test_every_field_exists_on_the_user_model() -> None:
    """A field the page renders but the model lacks would 500 on save."""
    missing = [name for name in FIELDS_BY_NAME if not hasattr(User, name)]
    assert not missing, f"not columns on User: {missing}"


def test_choice_fields_declare_choices_and_others_do_not() -> None:
    for field in PREFERENCE_FIELDS:
        if field.kind == "choice":
            assert field.choices, f"{field.name} is a choice field with no choices"
        else:
            assert field.kind in {"bool", "color"}, f"{field.name} has unknown kind {field.kind}"
            assert not field.choices, f"{field.name} is a {field.kind} but declares choices"


def test_every_default_is_itself_a_valid_choice() -> None:
    """Otherwise "Restore defaults" would post a value the endpoint refuses."""
    for field in PREFERENCE_FIELDS:
        if field.kind == "bool":
            assert isinstance(field.default, bool)
            continue
        if field.kind == "color":
            # "" is the meaningful default: no override, use the app's own
            # green/red. It must survive a round trip like any other value.
            assert field.default == ""
            assert field.coerce(field.default) == ""
            continue
        assert field.coerce(field.default) == field.default, (
            f"{field.name} default {field.default!r} is not one of its choices"
        )


@pytest.mark.parametrize("field", PREFERENCE_FIELDS, ids=lambda f: f.name)
def test_every_rendered_choice_is_accepted(field: PreferenceField) -> None:
    for choice in field.choices:
        assert field.coerce(choice.value) == choice.value


@pytest.mark.parametrize("field", PREFERENCE_FIELDS, ids=lambda f: f.name)
def test_values_outside_the_choices_are_refused(field: PreferenceField) -> None:
    for bogus in ("../../etc/passwd", "<script>", "admin", "999", "'; DROP TABLE"):
        assert field.coerce(bogus) is None, f"{field.name} accepted {bogus!r}"


COLOR_FIELDS = [f for f in PREFERENCE_FIELDS if f.kind == "color"]


@pytest.mark.parametrize("field", COLOR_FIELDS, ids=lambda f: f.name)
def test_colour_fields_take_only_full_hex(field: PreferenceField) -> None:
    """The value is echoed into a CSS custom property, so a lax pattern here
    is how a style-injection bug starts. Only #RRGGBB is accepted."""
    assert field.coerce("#D99530") == "#d99530", "must normalise case"
    assert field.coerce("  #1f75cb  ") == "#1f75cb", "must tolerate whitespace"
    assert field.coerce("") == "", "empty clears the override"
    for bogus in (
        "#abc",  # 3-digit form
        "red",  # named
        "rgb(1,2,3)",
        "#1f75cbb",  # too long
        "#1f75c",  # too short
        "#12345g",  # not hex
        "#1f75cb; background: url(x)",  # the injection this guards
        "var(--gl-red-500)",
        123,
        True,
    ):
        assert field.coerce(bogus) is None, f"{field.name} accepted {bogus!r}"


def test_bool_fields_accept_only_booleanish_input() -> None:
    field = FIELDS_BY_NAME["keyboard_shortcuts_enabled"]
    assert field.coerce(True) is True
    assert field.coerce(False) is False
    assert field.coerce("true") is True
    assert field.coerce("off") is False
    # Not a decision the user could have expressed - refused, not coerced.
    assert field.coerce("maybe") is None
    assert field.coerce(7) is None
    assert field.coerce(None) is None


def test_choice_fields_refuse_non_strings() -> None:
    field = FIELDS_BY_NAME["layout_width"]
    for bogus in (1, True, None, ["fixed"], {"value": "fixed"}):
        assert field.coerce(bogus) is None


def test_no_privileged_column_is_reachable() -> None:
    """The endpoint only ever setattrs names in this table, so the table itself
    must never grow a column that decides access."""
    forbidden = {
        "role",
        "role_locked",
        "is_active",
        "is_bot",
        "password_hash",
        "gitlab_access_token",
        "gitlab_refresh_token",
        "id",
        "username",
        "email",
    }
    assert not (set(FIELDS_BY_NAME) & forbidden)


def test_language_choices_cover_exactly_the_shipped_locales() -> None:
    """A language the app has no catalogue for would render an untranslated
    page; a shipped locale missing here would be unreachable."""
    from app.i18n import SUPPORTED_LOCALES

    offered = {c.value for c in FIELDS_BY_NAME["preferred_language"].choices}
    # "" is the "follow my browser" option, which is not a locale.
    assert offered - {""} == set(SUPPORTED_LOCALES)
    assert "" in offered, "there must be a way back to following the browser"


def test_current_preferences_falls_back_to_defaults() -> None:
    """A row written before the migration reads as the default, not None."""
    user = User()
    values = current_preferences(user)
    for field in PREFERENCE_FIELDS:
        if field.name == "preferred_language":
            assert values[field.name] == ""
        else:
            assert values[field.name] == field.default


def test_current_preferences_returns_stored_values() -> None:
    user = User()
    user.layout_width = "fluid"
    user.use_relative_times = False
    user.preferred_language = "en"
    values = current_preferences(user)
    assert values["layout_width"] == "fluid"
    assert values["use_relative_times"] is False
    assert values["preferred_language"] == "en"


def test_choice_labels_are_present_for_the_template() -> None:
    """The template renders t(choice.label); an empty one is a blank option."""
    for field in PREFERENCE_FIELDS:
        for choice in field.choices:
            assert isinstance(choice, Choice)
            assert choice.label.strip(), f"{field.name} has an unlabelled choice"


# -- Homepage redirect ------------------------------------------------------


def test_every_homepage_choice_has_a_destination() -> None:
    """A choice with no path would silently do nothing when selected."""
    from app.api.dashboard.preferences import HOMEPAGE_PATHS

    field = FIELDS_BY_NAME["default_homepage"]
    for choice in field.choices:
        assert choice.value in HOMEPAGE_PATHS, f"{choice.value} has no destination"


def test_no_homepage_destination_resolves_back_to_the_dashboard() -> None:
    """/dashboard/ redirecting to something that resolves to /dashboard/ loops
    forever. A fragment never reaches the server, so #anchor targets are out."""
    from app.api.dashboard.preferences import HOMEPAGE_PATHS

    for value, path in HOMEPAGE_PATHS.items():
        if path is None:
            continue
        assert "#" not in path, f"{value} points at a fragment, which would loop"
        assert path.rstrip("/") != "/dashboard", f"{value} redirects to itself"


def test_dashboard_choice_does_not_redirect() -> None:
    from app.api.dashboard.preferences import homepage_redirect_for

    assert homepage_redirect_for("admin", "dashboard") is None
    assert homepage_redirect_for("admin", None) is None
    assert homepage_redirect_for("admin", "") is None


@pytest.mark.parametrize(
    ("role", "preference", "expected"),
    [
        ("admin", "admin-users", "/dashboard/admin/users"),
        ("teacher", "admin-courses", "/dashboard/admin/courses"),
        ("student", "support", "/dashboard/support"),
        # Role no longer permits it - fall back rather than bounce off the gate.
        ("student", "admin-users", None),
        ("teacher", "admin-users", None),
        # A value that is not a choice at all.
        ("admin", "../../etc/passwd", None),
        ("admin", "nonsense", None),
    ],
)
def test_homepage_redirect_respects_the_role(
    role: str, preference: str, expected: str | None
) -> None:
    from app.api.dashboard.preferences import homepage_redirect_for

    assert homepage_redirect_for(role, preference) == expected


def test_a_student_cannot_save_an_admin_homepage() -> None:
    """The form does not offer it; this is the half that actually enforces it."""
    field = FIELDS_BY_NAME["default_homepage"]
    assert field.coerce("admin-users", "student") is None
    assert field.coerce("admin-courses", "student") is None
    assert field.coerce("admin-users", "teacher") is None
    assert field.coerce("admin-users", "admin") == "admin-users"
    assert field.coerce("support", "student") == "support"

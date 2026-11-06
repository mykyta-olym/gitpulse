"""Static/rendered invariants for shared form components."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.i18n import register_jinja_i18n

_TEMPLATES = Path("src/app/templates")


def _render(snippet: str) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    register_jinja_i18n(env)
    return env.from_string(snippet).render()


def test_bare_text_input_preserves_validation_attributes() -> None:
    html = _render(
        """
        {% from "components/forms.html" import text_input %}
        {{ text_input(
            'slug',
            bare=true,
            pattern='[a-z0-9-]+',
            minlength='3',
            maxlength='20',
            autofocus=true
        ) }}
        """
    )

    assert 'pattern="[a-z0-9-]+"' in html
    assert 'minlength="3"' in html
    assert 'maxlength="20"' in html
    assert "autofocus" in html


def test_bare_checkbox_preserves_submitted_value() -> None:
    html = _render(
        """
        {% from "components/forms.html" import checkbox %}
        {{ checkbox('enabled_checks', label='R01', value='R01', bare=true) }}
        """
    )

    assert 'name="enabled_checks"' in html
    assert 'value="R01"' in html


def test_number_stepper_is_plain_markup_not_alpine() -> None:
    """The stepper must stay framework-free.

    The check editor clones this control into modals at runtime; Alpine never
    initialises injected nodes, which is why a second hand-rolled stepper (and
    its own document-level click handler) grew alongside it and double-stepped
    the value on every click.
    """
    html = _render(
        """
        {% from "components/forms.html" import number_stepper %}
        {{ number_stepper('llm_count', value=3, min=1, max=20, step=1) }}
        """
    )

    assert "data-number-input" in html
    assert 'data-number-step="-1"' in html
    assert 'data-number-step="1"' in html
    assert "x-data" not in html
    assert "@click" not in html
    # The superseded markup must not come back.
    assert "number-btn-minus" not in html
    assert "number-input-wrapper" not in html


def test_number_stepper_omits_unset_range_attributes() -> None:
    """A bare stepper (the cloned template) must not inherit a 0-100 range."""
    html = _render(
        """
        {% from "components/forms.html" import number_stepper %}
        {{ number_stepper() }}
        """
    )

    # Leading space keeps these from matching `data-number-step="-1"`.
    assert ' min="' not in html
    assert ' max="' not in html
    assert ' step="' not in html


def test_json_drop_renders_one_surface_with_the_editor_as_the_target() -> None:
    """The editor IS the drop zone.

    It replaced a dashed upload box stacked on a separate textarea - one value
    with two controls, each of which cleared the other.
    """
    html = _render(
        """
        {% from "components/forms.html" import json_drop %}
        {{ json_drop('weekly_deadlines', rows=8, value='[]') }}
        """
    )

    assert "data-json-drop" in html
    assert 'name="weekly_deadlines"' in html
    assert "gl-json-drop-input" in html
    assert "gl-file-upload-input" in html
    assert "gl-json-drop-overlay" in html
    # Exactly one editable field: the textarea. The file input is visually
    # hidden and carries no name, so it never posts a second copy of the value.
    assert html.count("<textarea") == 1
    assert "gl-file-upload-area" not in html


def test_json_drop_upload_is_a_label_for_the_input() -> None:
    """ "Upload file" opens the native picker through the label's own
    activation - no script relays a click, so nothing that intercepts clicks
    can leave the button dead ("I click Upload file and nothing opens"). The
    input is real and focusable, not `hidden`: a label cannot activate an input
    the browser does not render, and Tab + Enter must reach it."""
    html = _render(
        """
        {% from "components/forms.html" import json_drop %}
        {{ json_drop('full_config_paste', id='full_config_paste_input') }}
        """
    )
    assert '<label for="full_config_paste_input_file" class="btn btn-icon btn-ghost btn-sm' in html
    assert 'btn-sm btn-responsive"' in html
    assert 'id="full_config_paste_input_file" class="gl-file-upload-input sr-only"' in html
    assert "aria-hidden" not in html.split("gl-file-upload-input")[1][:120]
    assert 'tabindex="-1"' not in html
    helpers = (_TEMPLATES / "static/js/_parts/core/37-json-drop.js").read_text(encoding="utf-8")
    assert "fileInput.click()" not in helpers
    css = (_TEMPLATES / "static/css/forms.css").read_text(encoding="utf-8")
    assert ".gl-json-drop-file[hidden] { display: none; }" in css


def test_json_drop_keeps_the_element_ids_page_scripts_bind_to() -> None:
    """Consumers look these up by id; renaming them silently breaks import."""
    html = _render(
        """
        {% from "components/forms.html" import json_drop %}
        {{ json_drop('full_config_paste', id='full_config_paste_input') }}
        """
    )

    assert 'id="full_config_paste_input"' in html


def test_required_custom_select_uses_focusable_validator_not_hidden_required() -> None:
    html = _render(
        """
        {% from "components/forms.html" import select_field %}
        {{ select_field('role', options=[('', 'Choose'), ('teacher', 'Teacher')], required=true) }}
        """
    )

    assert 'type="hidden" name="role" id="role" x-ref="input" value="" :value="selected">' in html
    assert 'class="gl-form-dropdown-validator"' in html
    assert 'x-ref="validator"' in html
    assert 'aria-label="role"' in html
    assert 'aria-required="true"' in html

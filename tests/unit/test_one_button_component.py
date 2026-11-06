"""The three button macros carry the same attributes, from one place.

`btn`, `btn_icon` and `btn_icon_only` each wrote out ~15 lines of attribute
plumbing, and the copies had drifted into different capability sets:

* `disabled_reason` - the tooltip that says WHY a control is off - worked only
  on `btn_icon`, so a disabled `btn` or `btn_icon_only` could not explain
  itself at all;
* `aria_pressed` worked only on `btn`, so a toggle drawn as an icon button
  could not announce its state;
* `form` and `x_bind_disabled` were missing from `btn_icon_only`.

The `hx_*` attributes are gone: no template ever passed one - htmx in this
app is driven from script, for navigation - so every button carried six
parameters and a search box a default `hx-trigger` for nothing.

Which of those a control supported depended on which macro happened to draw it.
`button_attrs()` emits them all now; each macro keeps only its own shape
(`size_class` / `variant_class` / what goes inside).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUTTONS = REPO / "src/app/templates/components/buttons.html"
BUTTON_MACROS = ("btn", "btn_icon", "btn_icon_only")

# Attributes every button must be able to carry, whichever macro draws it.
SHARED_PARAMS = (
    "type",
    "id",
    "name",
    "value",
    "form",
    "disabled",
    "loading",
    "title",
    "data_attrs",
    "x_click",
    "x_bind_disabled",
    "aria_pressed",
    "disabled_reason",
)


def _signatures() -> dict[str, set[str]]:
    src = BUTTONS.read_text(encoding="utf-8")
    out: dict[str, set[str]] = {}
    for name, args in re.findall(r"\{%\s*macro\s+(\w+)\(([^)]*)\)\s*%\}", src, re.S):
        params = {a.split("=")[0].strip() for a in re.split(r",(?![^{]*\})", args) if a.strip()}
        out[name] = params
    return out


def test_the_shared_attribute_macro_exists() -> None:
    assert "{% macro button_attrs(" in BUTTONS.read_text(encoding="utf-8")


def test_every_button_macro_accepts_every_shared_attribute() -> None:
    sigs = _signatures()
    missing = {
        name: sorted(p for p in SHARED_PARAMS if p not in sigs[name]) for name in BUTTON_MACROS
    }
    missing = {k: v for k, v in missing.items() if v}
    assert not missing, f"button macros missing shared attributes: {missing}"


def test_no_button_macro_re_emits_the_plumbing_itself() -> None:
    """Each macro delegates; none writes the attributes out a second time."""
    src = BUTTONS.read_text(encoding="utf-8")
    lines = src.split("\n")
    for name in BUTTON_MACROS:
        start = next(i for i, ln in enumerate(lines) if ln.startswith(f"{{% macro {name}("))
        depth = 0
        end = start
        for j in range(start, len(lines)):
            depth += len(re.findall(r"\{%-?\s*macro\s", lines[j]))
            depth -= len(re.findall(r"\{%-?\s*endmacro\s*-?%\}", lines[j]))
            if depth == 0:
                end = j
                break
        body = "\n".join(lines[start : end + 1])
        assert "button_attrs(" in body, f"{name} does not use the shared attribute macro"
        for attr in ("hx-post=", "hx-target=", "hx-indicator="):
            assert attr not in body, f"{name} still writes {attr} itself"


def test_the_capabilities_actually_render() -> None:
    sys.path.insert(0, str(REPO / "src"))
    from app.main import templates as app_templates

    def render(body: str) -> str:
        html = app_templates.env.from_string(
            '{% from "components/buttons.html" import btn, btn_icon, btn_icon_only %}' + body
        ).render(t=lambda s, **k: s, request=None)
        return " ".join(html.split())

    cases = [
        ("{{ btn('Go', disabled=true, disabled_reason='no permission') }}", "gl-tip-wrap"),
        ("{{ btn_icon_only('trash', disabled=true, disabled_reason='archived') }}", "gl-tip-wrap"),
        ("{{ btn_icon('F', 'filter', aria_pressed=true) }}", 'aria-pressed="true"'),
        ("{{ btn_icon_only('filter', aria_pressed=false) }}", 'aria-pressed="false"'),
        ("{{ btn_icon_only('save', form='f1') }}", 'form="f1"'),
        ("{{ btn_icon_only('save', x_bind_disabled='busy') }}", ':disabled="busy"'),
    ]
    for body, needle in cases:
        assert needle in render(body), f"{needle} missing from {body}"


def test_an_icon_only_button_always_has_an_accessible_name() -> None:
    """No visible label, so the name has to come from somewhere every time."""
    sys.path.insert(0, str(REPO / "src"))
    from app.main import templates as app_templates

    def render(body: str) -> str:
        return " ".join(
            app_templates.env.from_string(
                '{% from "components/buttons.html" import btn_icon_only %}' + body
            )
            .render(t=lambda s, **k: s, request=None)
            .split()
        )

    for body in (
        "{{ btn_icon_only('trash', aria_label='Delete') }}",
        "{{ btn_icon_only('trash', title='Delete') }}",
        "{{ btn_icon_only('trash', data_attrs={'tippy-content': 'Delete'}) }}",
    ):
        assert 'aria-label="Delete"' in render(body), body

"""One component for a soft-deleted entity's actions, and one margin scale.

Two kinds of drift were measured on 2026-08-25 and collapsed here.

**The restore / permanently-delete pair.** It was hand-written at six call
sites across four templates and no two agreed. The restore button was captioned
"Restore", "Restore group" or "Reactivate"; the gap between the two buttons was
`ml-1` (a class no CSS rule ever defined, so the buttons touched), `ml-2` (a
real margin stacked on top of the container's own `gap`), or nothing at all;
two sites shipped no tooltip; and in the group page's project table the restore
button rendered full-width beside a `btn-icon-only` delete, so one row held two
differently shaped buttons. `components/lifecycle.html` now emits both, and
`icon_only` decides the shape for BOTH of them.

**The margin utilities.** `utilities.css` declared the same class twice with
different values (`.mt-1` was `--gl-spacing-1` at the top of the file and
`1rem` five hundred lines down, so every call site silently got 16px from a
rule the author of the first one never saw), and it carried five alias names
for values a numbered utility already had (`.mt-05` == `.mt-3` == 8px). These
tests fail if either grows back.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
CSS_DIR = TEMPLATES / "static/css"
COMPONENT = TEMPLATES / "components/lifecycle.html"

LIFECYCLE_ACTIONS = (
    "reactivateTeam",
    "deleteTeamPermanent",
    "reactivateProject",
    "deleteProjectPermanent",
)


def _templates() -> list[Path]:
    return [p for p in TEMPLATES.rglob("*.html") if p != COMPONENT]


def _stylesheets() -> list[Path]:
    return [
        p
        for p in CSS_DIR.rglob("*.css")
        if ".min." not in p.name and "bundle" not in p.name and p.name != "vendor.css"
    ]


def test_the_component_exists() -> None:
    src = COMPONENT.read_text(encoding="utf-8")
    for macro in ("restore_actions", "deleted_toggle", "deleted_note"):
        assert f"{{% macro {macro}(" in src, f"{macro} is gone from lifecycle.html"


def test_no_template_hand_writes_a_lifecycle_button() -> None:
    """The pair comes from the macro or it does not exist."""
    offenders: dict[str, list[str]] = {}
    for p in _templates():
        hits = [
            line.strip()[:90]
            for line in p.read_text(encoding="utf-8").splitlines()
            if "<button" in line and any(f'data-action="{a}"' in line for a in LIFECYCLE_ACTIONS)
        ]
        if hits:
            offenders[str(p.relative_to(TEMPLATES))] = hits
    assert not offenders, (
        "these hand-write a lifecycle button instead of calling restore_actions() "
        f"from components/lifecycle.html: {offenders}"
    )


def test_no_template_hand_writes_the_deleted_toggle_or_note() -> None:
    offenders: dict[str, list[str]] = {}
    for p in _templates():
        hits = [
            line.strip()[:90]
            for line in p.read_text(encoding="utf-8").splitlines()
            if re.search(r'class="gp-deleted-(toggle|note)"', line)
        ]
        if hits:
            offenders[str(p.relative_to(TEMPLATES))] = hits
    assert not offenders, (
        f"use deleted_toggle() / deleted_note() from components/lifecycle.html: {offenders}"
    )


def test_both_buttons_in_a_pair_always_share_one_shape() -> None:
    """The bug this replaces: a full-width restore beside an icon-only delete."""
    from app.main import templates as app_templates

    def render(**kwargs: object) -> str:
        src = (
            '{% from "components/lifecycle.html" import restore_actions with context %}'
            "{{ restore_actions(kind, 'ID', lock_scope='course:C team:T') }}"
        )
        return app_templates.env.from_string(src).render(t=lambda s, **k: s, request=None, **kwargs)

    for kind in ("team", "project"):
        for icon_only in (False, True):
            src = (
                '{% from "components/lifecycle.html" import restore_actions with context %}'
                "{{ restore_actions(kind, 'ID', icon_only=icon_only,"
                " lock_scope='course:C team:T') }}"
            )
            html = app_templates.env.from_string(src).render(
                t=lambda s, **k: s, request=None, kind=kind, icon_only=icon_only
            )
            classes = re.findall(r'<button[^>]*class="([^"]*)"', html)
            assert len(classes) == 2, f"{kind}/{icon_only}: expected 2 buttons, got {len(classes)}"
            shapes = ["btn-icon-only" if "btn-icon-only" in c else "btn-icon" for c in classes]
            assert shapes[0] == shapes[1], (
                f"{kind}/icon_only={icon_only}: the pair rendered as {shapes} - "
                "one full-width button beside an icon-only one is the bug this "
                "component exists to prevent"
            )
            tips = re.findall(r'data-tippy-content="[^"]+"', html)
            assert len(tips) == 2, (
                f"{kind}/{icon_only}: both buttons need a tooltip, got {len(tips)}"
            )
            assert not re.search(r"\bm[tblr]-\w+\b", html), (
                "the macro must not add a margin utility - the container owns the gap"
            )

    assert render(kind="team")  # the default (labelled) path still renders


def _margin_rules() -> dict[str, tuple[str, str, Path]]:
    """{class: (property, value, file)} for every numbered margin utility.

    Restricted to the `m<side>-<number>` scale on purpose: `mr-card`,
    `mr-section` and `mr-count` are merge-request classes, not margin-right
    utilities, and a looser pattern reads them as spacing debt.
    """
    out: dict[str, tuple[str, str, Path]] = {}
    for p in _stylesheets():
        body = re.sub(r"/\*.*?\*/", "", p.read_text(encoding="utf-8"), flags=re.S)
        for name, prop, val in re.findall(
            r"^\.(m[tblr]?-(?:\d+|auto))\s*\{\s*(margin[\w-]*):\s*([^;}]+)[;}]", body, re.M
        ):
            assert name not in out, (
                f".{name} is declared twice: {out[name][2].name} and {p.name}. "
                "The later one silently wins, which is how .mt-1 came to mean "
                "16px while the rule at the top of the file said 2px."
            )
            out[name] = (prop, val.strip(), p)
    return out


def test_no_margin_utility_is_declared_twice() -> None:
    _margin_rules()  # the assertion lives inside, where both files are known


def test_one_utility_name_per_margin_value() -> None:
    by_value: dict[tuple[str, str], list[str]] = {}
    for name, (prop, val, _) in _margin_rules().items():
        by_value.setdefault((prop, val), []).append(name)
    dupes = {k: sorted(v) for k, v in by_value.items() if len(v) > 1}
    assert not dupes, (
        f"these margin utilities are different names for the same value: {dupes}. "
        "Pick the numbered one and rename the call sites."
    )


def test_every_margin_class_used_in_a_template_has_a_rule() -> None:
    """`ml-1` was written at three call sites and defined nowhere, so three
    elements sat flush against their neighbour while their markup claimed a gap."""
    defined = set(_margin_rules())
    corpus: list[str] = [p.read_text(encoding="utf-8") for p in TEMPLATES.rglob("*.html")]
    corpus += [
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (TEMPLATES / "static/js").rglob("*.js")
        if ".min." not in p.name and "bundle" not in p.name
    ]
    used: dict[str, int] = {}
    for text in corpus:
        for m in re.finditer(r'class="([^"{}]*)"', text):
            for cls in m.group(1).split():
                if re.fullmatch(r"m[tblr]?-(?:\d+|auto)", cls):
                    used[cls] = used.get(cls, 0) + 1
    missing = {c: n for c, n in used.items() if c not in defined}
    assert not missing, f"margin classes used in markup with no CSS rule: {missing}"

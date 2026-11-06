"""An icon name with no symbol behind it renders as nothing.

`icon('file-code')` sat in two templates - the code-reference toolbar and the
"Raw Check Details (JSON)" card header - and the macro has no branch for that
name, so it emitted an empty string. No error, no placeholder, no failing test:
just a gap where the icon was, which is how it survived long enough to be
reported.

Names reach the macro two ways and both are checked: `icon('x')` directly, and
`icon_name='x'` passed through a wrapper macro (banners, cards, empty states).

JS-rendered markup asks for icons too, and it must ask ONE registry: GP.icons
in static/js/icons.js, generated from this same file. Four more tables had
grown beside it - `GP._ICON_PATHS` and `_toastIcon` in core/09-toasts.js, and
private ones in the User Info card, the job bar, the support-ticket page, the
LLM error card and the webhook rows - and every extra copy had drifted back
onto the 24x24 stroked Feather glyphs the app moved off, so a JS-rendered icon
and the server-rendered one beside it were two different families. Worse, the
copies were incomplete: four of the names asked of `GP._ICON_PATHS` were simply
absent, and a missing name answers with '' - an empty, padded icon box where an
error state's alert mark belongs.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"
ICONS = TEMPLATES / "components/icons.html"
STATIC_JS = TEMPLATES / "static/js"
ICONS_JS = STATIC_JS / "icons.js"
BASE_JS = STATIC_JS / "_parts/core/09-toasts.js"


def _defined() -> set[str]:
    text = ICONS.read_text(encoding="utf-8")
    names = set(re.findall(r"name\s*==\s*'([\w-]+)'", text))
    for group in re.findall(r"name\s+in\s+\[([^\]]+)\]", text):
        names |= set(re.findall(r"'([\w-]+)'", group))
    assert names, "no icon names parsed out of icons.html"
    return names


def _used() -> dict[str, set[str]]:
    used: dict[str, set[str]] = {}
    for path in TEMPLATES.rglob("*.html"):
        if path.name == "icons.html":
            continue
        text = path.read_text(encoding="utf-8")
        found = set(re.findall(r"\bicon\(\s*'([\w-]+)'", text))
        found |= set(re.findall(r"\bicon_name\s*=\s*'([\w-]+)'", text))
        for name in found:
            used.setdefault(name, set()).add(str(path.relative_to(TEMPLATES)))
    return used


def test_every_icon_name_used_in_a_template_has_a_symbol() -> None:
    defined = _defined()
    missing = {n: v for n, v in sorted(_used().items()) if n not in defined}
    assert not missing, "icon names with no symbol behind them: " + ", ".join(
        f"{n} ({', '.join(sorted(f))})" for n, f in missing.items()
    )


# -- The JS registry (icons.js) --


def _registered() -> dict[str, str]:
    """GP.icons - the one icon table JS renders from."""
    text = ICONS_JS.read_text(encoding="utf-8")
    block = re.search(r"const PATHS = \{(.*?)\n  \};", text, re.S)
    assert block, "PATHS not found in icons.js"
    entries = dict(
        re.findall(r"^\s*'([\w-]+)': \{ vb: '[^']*', d: '(.*)' \},\s*$", block.group(1), re.M)
    )
    assert entries, "no icon paths parsed out of icons.js"
    return entries


def _asked_for_in_js() -> dict[str, set[str]]:
    """Both front doors: GP.iconSvg(name, token) and GP.icons.get(name, px)."""
    asked: dict[str, set[str]] = {}
    for path in STATIC_JS.rglob("*.js"):
        if ".min." in path.name or "bundle" in path.name or "vendor" in path.parts:
            continue
        if path.name == "icons.js":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in (r"iconSvg\(\s*'([\w-]+)'", r"icons\.get\(\s*'([\w-]+)'"):
            for name in re.findall(pattern, text):
                asked.setdefault(name, set()).add(str(path.relative_to(STATIC_JS)))
    return asked


def test_every_icon_name_used_from_js_has_a_path() -> None:
    registry = _registered()
    missing = {n: v for n, v in sorted(_asked_for_in_js().items()) if n not in registry}
    assert not missing, "icon names with no path behind them: " + ", ".join(
        f"{n} ({', '.join(sorted(f))})" for n, f in missing.items()
    )


def test_the_js_registry_matches_icons_html() -> None:
    """Same glyph as the macro - a registry that drifts is two icon sets."""
    html = ICONS.read_text(encoding="utf-8")
    branches = dict(re.findall(r"name == '([\w-]+)' %\}\s*(<svg.*?</svg>)", html, re.S))
    drifted = []
    for name, inner in _registered().items():
        source = branches.get(name)
        if source is None:
            drifted.append(f"{name}: no such branch in icons.html")
            continue
        expected = re.sub(r"^<svg[^>]*>|</svg>$", "", source.strip())
        if expected != inner:
            drifted.append(f"{name}: differs from the macro")
    assert not drifted, "; ".join(drifted)


def test_there_is_only_one_js_icon_table() -> None:
    """Four of them existed, and every extra one had drifted onto Feather.

    core/09-toasts.js kept `GP._ICON_PATHS` (six entries, missing four of the
    names its own callers asked for) and `_toastIcon` (seven more); the job
    bar, the User Info card, the support-ticket page, the LLM error card and
    the webhook rows carried their own. A private table is a second icon set.
    """
    offenders = []
    for path in STATIC_JS.rglob("*.js"):
        if ".min." in path.name or "bundle" in path.name or "vendor" in path.parts:
            continue
        if path.name == "icons.js":
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"(\w+)\s*=\s*\{[^}]*?'?<(?:svg|path|circle|polyline)", text):
            offenders.append(f"{path.relative_to(STATIC_JS)}: {match.group(1)}")
    assert not offenders, "private icon tables: " + ", ".join(offenders)


def test_icon_lookup_tables_hold_names_not_markup() -> None:
    """A lookup that maps a domain word to an icon must map to a NAME.

    A literal scan cannot see `GP.iconSvg(_JOB_ICONS[key])`, so the job bar's
    table is checked against the registry directly.
    """
    src = (STATIC_JS / "_parts/global-job-bar/00-state-polling.js").read_text(encoding="utf-8")
    block = re.search(r"const _JOB_ICONS = \{(.*?)\n\};", src, re.S)
    assert block, "_JOB_ICONS not found"
    names = re.findall(r":\s*'([\w-]+)'", block.group(1))
    assert len(names) >= 10, names

    base = BASE_JS.read_text(encoding="utf-8")
    toast = re.search(r"const _TOAST_ICONS = \{(.*?)\n\};", base, re.S)
    assert toast, "_TOAST_ICONS not found"
    names += re.findall(r":\s*'([\w-]+)'", toast.group(1))

    registry = _registered()
    assert not [n for n in names if n not in registry], [n for n in names if n not in registry]

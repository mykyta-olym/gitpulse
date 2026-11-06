"""The interactive colours must stay 1:1 with GitLab's published design tokens.

GitLab's confirm/primary button and its checked form controls are NEUTRAL, not
blue - blue is reserved for links, focus rings and info. That is easy to "fix"
back to blue by accident, and nothing else in the suite would notice, so the
expected values below are pinned here.

The DARK values of the selected highlight (--gl-action-selected-*), the
confirm button and the checked controls are deliberately NOT
pinned: GitLab's are the confirm ramp inverted - near-white on dark - which on
a dark page reads as a white block, not a highlight. On dark the app paints
them with the accent instead; test_theme_highlights.py owns that. Their LIGHT
values stay GitLab's and are pinned in EXPECTED_LIGHT below.

Source of truth: @gitlab/ui 136.3.0, src/tokens/build/css/tokens.css and
tokens.dark.css (--gl-button-*, --gl-action-*, --gl-control-*), resolved to hex.
Re-derive with:  npm pack @gitlab/ui  and read those two files.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TOKENS = _REPO / "src/app/templates/static/css/tokens.css"

# token name -> (light value, dark value)
EXPECTED: dict[str, tuple[str, str]] = {
    # Default / secondary button
    "--gl-btn-default-bg": ("#fff", "rgba(137, 136, 141, 0.4)"),
    "--gl-btn-default-bg-hover": ("#ececef", "rgba(137, 136, 141, 0.64)"),
    "--gl-btn-default-bg-active": ("#dcdcde", "rgba(137, 136, 141, 0.32)"),
    "--gl-btn-default-text": ("#3a383f", "#ececef"),
    "--gl-btn-default-border": ("#bfbfc3", "transparent"),
    # Danger button
    "--gl-btn-danger-bg": ("#dd2b0e", "#f6806d"),
    "--gl-btn-danger-bg-hover": ("#c02f12", "#fcb5aa"),
    "--gl-btn-danger-bg-active": ("#812713", "#ec5941"),
    "--gl-btn-danger-text": ("#fff", "#18171d"),
    "--gl-btn-danger-border": ("#c02f12", "transparent"),
    # Disabled button
    "--gl-btn-disabled-text": ("#737278", "#89888d"),
    "--gl-btn-disabled-bg": ("#fbfafd", "rgba(137, 136, 141, 0.16)"),
    # Form control chrome
    "--gl-control-border-default": ("#89888d", "#737278"),
    "--gl-control-placeholder-color": ("#737278", "#89888d"),
    # Badges are a muted chip, NOT a bright one - but the POLARITY flips by
    # theme, and it flipped upstream too. Light is unchanged since 136.1.0
    # (a -100 chip carrying -700 text). Dark used to mirror it (-800 chip,
    # -300 text); as of 136.3.0 @gitlab/ui INVERTS dark instead - a light -300
    # chip carrying -950 text. These are the resolved 136.3.0 dark values.
    "--gl-badge-neutral-bg": ("#dcdcde", "#a4a3a8"),
    "--gl-badge-neutral-text": ("#4c4b51", "#18171d"),
    "--gl-badge-info-bg": ("#cbe2f9", "#63a6e9"),
    "--gl-badge-info-text": ("#2f5ca0", "#1d283e"),
    "--gl-badge-success-bg": ("#c3e6cd", "#52b87a"),
    "--gl-badge-success-text": ("#306440", "#17291c"),
    "--gl-badge-warning-bg": ("#f5d9a8", "#d99530"),
    "--gl-badge-warning-text": ("#894b16", "#382315"),
    "--gl-badge-danger-bg": ("#fdd4cd", "#f6806d"),
    "--gl-badge-danger-text": ("#a32c12", "#3e1a14"),
}

# token name -> light value; the dark value is the theme's own (see above)
EXPECTED_LIGHT: dict[str, str] = {
    # Confirm / primary button
    "--gl-btn-confirm-bg": "#3a383f",
    "--gl-btn-confirm-bg-hover": "#18171d",
    "--gl-btn-confirm-bg-active": "#050506",
    "--gl-btn-confirm-text": "#fff",
    # Checked checkbox / radio
    "--gl-control-bg-selected": "#3a383f",
    "--gl-control-bg-selected-hover": "#18171d",
    "--gl-control-indicator-selected": "#fff",
}

_DECL = re.compile(r"^\s*(--[a-z0-9-]+)\s*:\s*([^;]+);", re.IGNORECASE)


def _blocks() -> tuple[dict[str, str], dict[str, str]]:
    """Return (light, dark) token tables, each already carrying the shared palette.

    The dark theme lives on `:root` (the app is dark by default) and light on
    `html[data-theme="light"]`, which is also where the palette is declared.
    """
    dark: dict[str, str] = {}
    light: dict[str, str] = {}
    selector = ""
    depth = 0
    for line in _TOKENS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.endswith("{"):
            depth += 1
            if depth == 1:
                selector = stripped[:-1].strip()
            continue
        if stripped.startswith("}"):
            depth = max(0, depth - 1)
            continue
        match = _DECL.match(line)
        if not match or depth < 1:
            continue
        name, value = match.group(1), match.group(2).split("/*")[0].strip()
        if selector == ":root":
            dark[name] = value
        elif 'data-theme="light"' in selector:
            light[name] = value
    # the palette is only declared once, on :root
    for name, value in dark.items():
        light.setdefault(name, value)
    return light, dark


def _resolve(name: str, table: dict[str, str], seen: frozenset[str] = frozenset()) -> str | None:
    if name in seen:
        return None
    value = table.get(name)
    if value is None:
        return None
    ref = re.fullmatch(r"var\((--[a-z0-9-]+)\)", value.strip())
    if ref:
        return _resolve(ref.group(1), table, seen | {name})
    return value.strip()


def test_interactive_colours_match_gitlab() -> None:
    light, dark = _blocks()
    assert light, "tokens.css parsing broke - no light-theme declarations found"
    assert dark, "tokens.css parsing broke - no dark-theme declarations found"

    problems: list[str] = []
    for token, (want_light, want_dark) in EXPECTED.items():
        for theme, table, want in (("light", light, want_light), ("dark", dark, want_dark)):
            got = _resolve(token, table)
            if got is None:
                problems.append(f"{token} ({theme}): not defined")
            elif got.replace(" ", "").lower() != want.replace(" ", "").lower():
                problems.append(f"{token} ({theme}): app={got} gitlab={want}")

    assert not problems, "tokens drifted from @gitlab/ui 136.3.0:\n  " + "\n  ".join(problems)


def test_light_only_pins_match_gitlab() -> None:
    light, _dark = _blocks()
    problems: list[str] = []
    for token, want in EXPECTED_LIGHT.items():
        got = _resolve(token, light)
        if got is None:
            problems.append(f"{token} (light): not defined")
        elif got.replace(" ", "").lower() != want.replace(" ", "").lower():
            problems.append(f"{token} (light): app={got} gitlab={want}")
    assert not problems, "tokens drifted from @gitlab/ui 136.3.0:\n  " + "\n  ".join(problems)

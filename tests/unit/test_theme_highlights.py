"""Shared controls use the theme and accent selected-state tokens."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css"
TOKENS = (CSS / "tokens.css").read_text(encoding="utf-8")

SELECTED = (
    "--gl-action-selected-bg-default",
    "--gl-action-selected-bg-hover",
    "--gl-action-selected-bg-active",
    "--gl-action-selected-border",
    "--gl-action-selected-text",
)
NEAR_WHITE = ("--gl-gray-0", "--gl-gray-10", "--gl-gray-50")


def _block(selector_fragment: str) -> str:
    start = TOKENS.index(selector_fragment)
    return TOKENS[start : TOKENS.index("\n}", start)]


def _decl(block: str, name: str) -> str:
    match = re.search(re.escape(name) + r"\s*:\s*([^;]+);", block)
    assert match, f"{name} is not declared in this theme block"
    return match.group(1).strip()


def test_each_mode_declares_its_own_selected_highlight() -> None:
    dark = TOKENS[: TOKENS.index("html:not([data-theme])")]
    light = _block('html[data-theme="light"] {')
    for name in SELECTED:
        for theme, block in (("dark", dark), ("light", light)):
            value = _decl(block, name)
            for white in NEAR_WHITE:
                assert f"var({white})" not in value, (
                    f"{name} on {theme} is {value}: a near-white block, not a highlight"
                )


def test_the_accent_retints_the_selected_highlight() -> None:
    accent = _block('html[data-accent]:not([data-accent="default"]) {')
    for name in SELECTED:
        assert "var(--_accent)" in _decl(accent, name), f"{name} ignores the accent"
    for name in ("indigo", "blue", "green", "red", "gray"):
        assert f'html[data-accent="{name}"]' in TOKENS
    # the sidebar is DERIVED from the same tokens, so it cannot drift
    sidebar = (CSS / "sidebar.css").read_text(encoding="utf-8")
    assert "--sidebar-active-bg: var(--gl-action-selected-bg-default);" in sidebar
    assert "--_accent:" not in sidebar, "the accent colour is declared twice"


def test_every_table_state_uses_the_accent_on_an_opaque_surface() -> None:
    dark = TOKENS[: TOKENS.index("html:not([data-theme])")]
    light = _block('html[data-theme="light"] {')
    for block in (dark, light):
        for state in ("hover", "selected"):
            value = _decl(block, f"--gl-table-row-{state}-bg")
            assert "var(--gl-action-selected-border)" in value
            assert "var(--gl-background-color-default)" in value
            assert "transparent" not in value, "pinned cells must cover the text below them"


def test_every_selected_state_reads_the_shared_tokens() -> None:
    for rel, selector in (
        ("tables.css", ".pagination-current {"),
        ("sidebar.css", ".gl-sidebar-item.active {"),
    ):
        src = (CSS / rel).read_text(encoding="utf-8")
        start = src.index(selector)
        rule = src[start : src.index("}", start)]
        assert "selected" in rule, f"{rel} {selector} paints its own selected colour"


def test_dark_paints_no_control_near_white() -> None:
    """GitLab's dark confirm button and checked checkbox/radio are the neutral-50
    whites too; on dark they are the accent (blue-500 by default) with a white
    indicator, and the accent block retints the controls."""
    dark = TOKENS[: TOKENS.index("html:not([data-theme])")]
    for name in (
        "--gl-btn-confirm-bg",
        "--gl-btn-confirm-bg-hover",
        "--gl-btn-confirm-bg-active",
        "--gl-control-bg-selected",
        "--gl-control-bg-selected-hover",
        "--gl-control-border-selected",
    ):
        value = _decl(dark, name)
        for white in NEAR_WHITE:
            assert f"var({white})" not in value, f"{name} on dark is {value}"
    assert _decl(dark, "--gl-control-indicator-selected") == "var(--gl-gray-0)"
    accent = _block('html[data-accent]:not([data-accent="default"]) {')
    for name in ("--gl-control-bg-selected", "--gl-control-border-selected"):
        assert "var(--_accent)" in _decl(accent, name), f"{name} ignores the accent"


def test_the_accent_is_the_whole_theme() -> None:
    """Picking a Theme in Preferences retints the primary colour, the confirm
    button (filled and outlined, per mode), the focus ring, links, the tab
    indicator, the chart brand series and the listbox selection - not only the
    sidebar - and the dark default confirm button is the calmer blue-600."""
    dark = TOKENS[: TOKENS.index("html:not([data-theme])")]
    assert _decl(dark, "--gl-btn-confirm-bg") == "var(--gl-blue-600)"
    assert _decl(dark, "--gl-btn-confirm-bg-hover") == "var(--gl-blue-500)"
    accent = _block('html[data-accent]:not([data-accent="default"]) {')
    for name in (
        "--primary",
        "--gl-btn-confirm-bg",
        "--gl-btn-confirm-bg-hover",
        "--gl-btn-confirm-secondary-border",
        "--focus-ring",
        "--focus-ring-inset",
    ):
        assert "var(--_accent)" in _decl(accent, name), f"{name} ignores the accent"
    dark_accent = TOKENS[TOKENS.index('html[data-theme="dark"][data-accent]') :]
    dark_accent = dark_accent[: dark_accent.index("\n}")]
    assert "var(--gl-gray-900)" in _decl(dark_accent, "--gl-btn-confirm-bg"), (
        "the dark accent confirm fill is not laid over the page"
    )
    # links, the tab indicator, the chart brand series and the listbox selection
    for name in (
        "--gl-text-color-link",
        "--gl-tab-selected-indicator",
        "--chart-brand",
        "--gl-dropdown-item-selected-bg",
    ):
        assert "var(--_accent)" in _decl(accent, name), f"{name} ignores the accent"
    # no component paints the brand blue for itself any more
    for rel, needle in (
        ("home.css", "border-bottom-color:var(--gl-blue-500)"),
        ("navbar.css", "background: var(--gl-blue-600)"),
        ("animations.css", "var(--gl-blue-500) 0%"),
    ):
        assert needle not in (CSS / rel).read_text(encoding="utf-8"), (
            f"{rel} paints blue for itself"
        )
    helpers = (REPO / "src/app/templates/static/js/_parts/core/47-chart-theme.js").read_text(
        encoding="utf-8"
    )
    assert "brand: resolveToken('--chart-brand'" in helpers
    preview = (REPO / "src/app/templates/components/theme_preview.html").read_text(encoding="utf-8")
    assert 'fill="var(--theme-preview-accent)"' in preview


def test_the_chart_palette_is_the_themes() -> None:
    """The categorical chart colours (one per check category) and the role
    colours are tokens per mode, read by the charts and the legend dots from
    the same place; no chart appends a hex alpha to a resolved rgb() colour."""
    dark = TOKENS[: TOKENS.index("html:not([data-theme])")]
    light = _block('html[data-theme="light"] {')
    for name in ("--chart-cat-issue", "--chart-cat-mr", "--chart-cat-review", "--chart-cat-ci"):
        assert _decl(dark, name) != _decl(light, name), f"{name} is the same on both modes"
    cards = (CSS / "cards.css").read_text(encoding="utf-8")
    assert ".gl-chart-legend-marker--issue   { background: var(--chart-cat-issue); }" in cards
    js = REPO / "src/app/templates/static/js"
    for rel in (
        "_parts/admin-system/10-stats.js",
        "_parts/course-analytics/00-charts.js",
        "_parts/course-analytics/20-week-explorer.js",
        "_parts/project-detail/30-live-intel.js",
    ):
        src = (js / rel).read_text(encoding="utf-8")
        assert "+ 'cc'" not in src, f"{rel} appends a hex alpha to a resolved colour"
    helpers = (js / "_parts/core/47-chart-theme.js").read_text(encoding="utf-8")
    assert "catIssue:   resolveToken('--chart-cat-issue'" in helpers
    assert "alpha: alpha, token: resolveToken" in helpers

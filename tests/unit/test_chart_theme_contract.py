"""Charts follow the theme they are drawn in, on the first frame and after a switch.

Found on the student's Compliance Progress card in dark mode: the ticks were
Chart.js's own #666, the labels Helvetica, the radar's web invisible, the
threshold lines at 70/40 while the pills under the chart said 80/50, and the
point rings stayed white after a switch to dark. Each of these is one contract
below.
"""

from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "src/app/templates/static"
TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"


def _read(rel: str) -> str:
    return (STATIC / rel).read_text(encoding="utf-8")


def test_chart_defaults_are_applied_once_chart_js_has_loaded() -> None:
    """Chart.js is a per-page script that loads after the core bundle.

    applyDefaults() at bundle init therefore ran against no Chart at all and
    every chart kept the library's defaults until a theme toggle. The theme
    module re-applies on DOMContentLoaded, by which time deferred scripts ran.
    """
    src = _read("js/_parts/core/47-chart-theme.js")
    block = src.split("GP.chartTheme = {", 1)[1][:800]
    assert "document.addEventListener('DOMContentLoaded', refresh)" in block


def test_chart_grid_has_its_own_token_visible_on_the_dark_chart_surface() -> None:
    """Dark charts sit on the strong surface (gray-800), which is what
    --gl-border-color-subtle resolves to in that mode - the grid vanished."""
    tokens = _read("css/tokens.css")
    assert tokens.count("--chart-grid:") == 2, "one value per mode"
    assert re.search(r"--chart-grid:\s*var\(--gl-gray-700\)", tokens)
    assert re.search(r"--chart-grid:\s*var\(--gl-border-color-subtle\)", tokens)
    theme = _read("js/_parts/core/47-chart-theme.js")
    assert "grid: resolveToken('--chart-grid'" in theme


def test_score_trend_thresholds_come_from_the_course() -> None:
    """The dashed lines, the point colours and the pills must agree."""
    page = _read("js/pages/student-detail.js")
    assert "_SCORE_GREEN = 0.7" not in page
    assert "_thresholdPanel?.dataset.greenPct" in page
    assert "_thresholdPanel?.dataset.yellowPct" in page
    card = (TEMPLATES / "partials/student/_compliance_history.html").read_text(encoding="utf-8")
    assert "'data-green-pct': green_pct|default(DEFAULT_GREEN_PCT)" in card
    assert "'data-yellow-pct': yellow_pct|default(DEFAULT_YELLOW_PCT)" in card


def test_score_trend_reads_live_theme_colours_when_it_draws() -> None:
    """Bands, threshold lines and point rings resolve the theme at draw time,
    so a mode switch repaints them instead of leaving the old theme's ink."""
    page = _read("js/pages/student-detail.js")
    bands = page.split("id: 'thresholdBands'", 1)[1].split("}],", 1)[0]
    assert "GP.chartTheme && GP.chartTheme.colors" in bands
    assert "chartColors.green + '0A'" not in bands
    assert "fillText(Math.round(v * 100) + ' %'" in bands, "threshold lines are labelled"
    assert "pointBorderColor: () => (GP.chartTheme?.colors?.background)" in page
    # The fill under the line is the brand series colour, like the line.
    assert "gradient.addColorStop(0, chartAlpha(chartColors.brand, 0.19))" in page
    assert not re.search(r"chartColors\.\w+\s*\+\s*'", page)
    assert "chartColors.blue + '30'" not in page


def test_skill_radar_uses_the_category_tokens() -> None:
    page = _read("js/pages/student-detail.js")
    radar = page.split("function initSkillRadar(data) {", 1)[1].split("\n  function ", 1)[0]
    for token in ("catIssue", "catMr", "catReview", "catCi"):
        assert f"chartColors.{token}" in radar
    assert "pointBorderColor: _liveBg" in radar
    assert "angleLines: { color: _liveGrid }" in radar


def test_the_install_card_is_on_and_speaks_the_catalogue() -> None:
    """The custom PWA install card was gated behind a flag nothing set since
    July, so 'the install popup stopped appearing'; and its strings were
    looked up by dotted keys the catalogue never had."""
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert 'data-custom-pwa-install="true"' in base
    pwa = _read("js/pwa-install.js")
    assert "const _t = (text) => {" in pwa
    assert "pwa.install." not in pwa, "dotted keys are not catalogue keys"
    for text in ("Install GitPulse", "Not now", "Install", "Close"):
        assert f"_t('{text}')" in pwa


def test_language_names_stay_in_their_own_language() -> None:
    """The switcher lists "English" and "Slovenčina" whatever the page
    language, or a reader who cannot read Slovak cannot find their way out
    of it. i18n.js honours the HTML translate="no" attribute for that."""
    i18n = _read("js/i18n.js")
    assert i18n.count("""closest('[translate="no"]')""") == 2, "text nodes and attributes"
    forms = (TEMPLATES / "components/forms.html").read_text(encoding="utf-8")
    switcher = forms.split("{% macro language_selector(", 1)[1].split("{% endmacro %}", 1)[0]
    markup = re.sub(r"\{#.*?#\}", "", switcher, flags=re.DOTALL)
    assert markup.count('translate="no"') == 2, "the selected label and every option"


def test_a_new_service_worker_asks_the_server_before_any_reload() -> None:
    """After a deploy the new worker claims the page and `controllerchange`
    fires. Reloading on that alone turned one manual refresh into two: on a
    server still warming up after a restart the worker's install ran past
    the ten-second settle window, and the reload landed while the reader
    was scrolling. Control of the page says nothing about the page being
    behind; X-App-Version does, and the version check reloads once, at a
    quiet moment, with a notice - so that is the only path allowed."""
    src = _read("js/_parts/core/36-boot.js")
    body = src.split("function _initServiceWorker() {", 1)[1].split("\n}\n", 1)[0]
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", body, flags=re.DOTALL)
    assert "location.reload" not in code
    assert "SW_SETTLE_MS" not in code
    assert "controllerchange" in code
    assert "_checkVersionHeader(resp.headers)" in code
    assert "fetch('/dashboard/session-check'" in code


def test_hover_never_takes_the_focus_ring_off_a_control() -> None:
    """`.form-input:hover:not(:disabled)` outranks `.form-input:focus`, so the
    pointer resting on the field being typed in swapped the focus ring for the
    hover border - "the blue outline disappears when I move the cursor over an
    input". Hover yields to focus on every control that has both."""
    forms = _read("css/forms.css")
    assert ".form-input:hover:not(:disabled):not(:focus) {" in forms
    assert ".form-check-input:hover:not(:disabled):not(:focus-visible) {" in forms
    assert ".search-box input:hover:not(:disabled):not(:focus) {" in forms
    tables = _read("css/tables.css")
    assert ".table-controls .tab-btn" not in tables, "table placement must not restyle tab focus"
    theme = _read("css/theme.css")
    assert ".theme-switcher-button:focus-visible" in theme
    assert ":where(html[data-theme-preference=" in theme, (
        "the selected segment must not outrank focus"
    )
    assert ".theme-switcher-button" not in _read("css/pages/preferences.css")


def test_every_checkbox_is_the_shared_form_check_input() -> None:
    """Four JS-rendered checkboxes shipped as the browser's own control next to
    the GitLab-styled one in the same tables."""
    for rel in (
        "js/_parts/course-settings/10-sections.js",
        "js/_parts/course-settings/20-checks-import.js",
        "js/_parts/course-settings/30-llm-generate.js",
        "js/_parts/course-settings/40-full-config.js",
        "js/_parts/course-settings/50-danger-zone.js",
        "js/_parts/course-settings/60-live-state.js",
        "js/_parts/course-settings/70-webhooks.js",
        "js/_parts/course-settings/80-weekly-deadlines.js",
        "js/pages/admin-events.js",
    ):
        src = _read(rel)
        bare = re.findall(r"<input type=\?\"checkbox\?\"(?![^>]*form-check-input)[^>]*>", src)
        assert not bare, (rel, bare[:2])


def test_the_markdown_preview_has_an_empty_state() -> None:
    src = _read("js/markdown-helpers.js")
    assert "'Nothing to preview.'" in src
    assert "gh-md-preview-empty" in _read("css/pages/support.css")


def test_the_home_greeting_is_gitlabs_on_the_pc_and_on_the_phone() -> None:
    """Measured on gitlab.example.com: a 64px avatar, the name at 20px/600
    (18px on a phone - Pajamas heading-scale-500), the sentence at 16px,
    centred on the avatar with a 16px gap, the same on both. The name was a
    30px page title here and shrank to 24px with a 48px avatar on a phone."""
    home = _read("css/home.css")
    title = home.split(".gl-home-title {", 1)[1].split("}", 1)[0]
    assert "font-size: var(--font-size-xl);" in title
    assert "font-weight: var(--font-weight-semibold);" in title
    phone = home.split("@media (max-width: 768px) {", 1)[1].split("\n}\n", 1)[0]
    assert ".gl-home-avatar {" not in phone, "the avatar stays 64px on a phone"
    assert ".gl-home-greeting {" not in phone, "centred, same gap - like GitLab"
    phone_title = phone.split(".gl-home-title {", 1)[1].split("}", 1)[0]
    assert "font-size: var(--font-size-lg);" in phone_title
    narrow = _read("css/_parts/responsive/20-small-touch.css")
    assert ".gl-home-title" not in narrow

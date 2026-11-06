"""The preferences must actually DO something.

A settings page that stores values nothing reads is worse than no page at all:
it tells the reader their choice took effect when it did not. Each test here
follows one preference from the stored column to the thing that consumes it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.dashboard._helpers import _role_context
from app.api.dashboard.preferences import PREFERENCE_FIELDS
from app.dependencies import _choice_allowlists
from app.models.user import User

REPO = Path(__file__).resolve().parents[2]
BASE_HTML = (REPO / "src/app/templates/base.html").read_text(encoding="utf-8")
DEPENDENCIES = (REPO / "src/app/dependencies.py").read_text(encoding="utf-8")
SIDEBAR_CSS = (REPO / "src/app/templates/static/css/sidebar.css").read_text(encoding="utf-8")
NAVBAR_CSS = (REPO / "src/app/templates/static/css/navbar.css").read_text(encoding="utf-8")
SHORTCUTS_JS = (REPO / "src/app/templates/static/js/_parts/core/25-shortcuts.js").read_text(
    encoding="utf-8"
)
TIME_JS = (REPO / "src/app/templates/static/js/localize-time.js").read_text(encoding="utf-8")

# preference -> the attribute base.html puts it on <html>
ROOT_ATTRIBUTES = {
    "accent_theme": "data-accent",
    "layout_width": "data-layout-width",
    "time_format": "data-time-format",
    "first_day_of_week": "data-first-day",
}


@pytest.mark.parametrize(("pref", "attribute"), ROOT_ATTRIBUTES.items())
def test_preference_reaches_the_root_element(pref: str, attribute: str) -> None:
    """On <html>, not <body>: CSS keys off these before first paint, so a
    class added later by script would reflow the page in front of the reader."""
    assert attribute in BASE_HTML, f"{attribute} missing from base.html"
    assert pref in BASE_HTML, f"{pref} is never read by base.html"


def test_boolean_preferences_render_as_presence_flags() -> None:
    """Both are absence-means-default, so an old session renders as before."""
    assert "data-absolute-times" in BASE_HTML
    assert "data-no-shortcuts" in BASE_HTML
    assert "not use_relative_times" in BASE_HTML
    assert "not keyboard_shortcuts_enabled" in BASE_HTML


@pytest.mark.parametrize(
    "pref",
    [
        "accent_theme",
        "layout_width",
        "keyboard_shortcuts_enabled",
        "default_homepage",
        "first_day_of_week",
        "use_relative_times",
        "time_format",
    ],
)
def test_preference_is_hydrated_per_request(pref: str) -> None:
    """dependencies.py loads it from the column into the session, which is
    what _role_context hands to every template.

    A "choice" preference reaches the session through the table-driven loop
    rather than a line of its own, so it is looked for by name in that loop.
    """
    assert f"User.{pref}" in DEPENDENCIES, f"{pref} is never SELECTed"
    assigned = f'session_data["{pref}"]' in DEPENDENCIES
    hydrated_by_table = f'("{pref}", {pref})' in DEPENDENCIES
    assert assigned or hydrated_by_table, f"{pref} never reaches the session"


def test_role_context_exposes_every_preference() -> None:
    context = _role_context({})
    for pref in ROOT_ATTRIBUTES:
        assert pref in context, f"{pref} missing from _role_context"
    assert context["layout_width"] == "fixed"
    assert context["use_relative_times"] is True
    assert context["keyboard_shortcuts_enabled"] is True


def test_hydration_revalidates_instead_of_trusting_the_column() -> None:
    """A value that fell out of the allowed set must degrade to the default
    rather than reach a template and render a broken attribute."""
    allowlists = _choice_allowlists()
    assert allowlists, "hydration re-validates nothing"
    for field in PREFERENCE_FIELDS:
        if field.kind != "choice":
            continue
        allowed, fallback = allowlists[field.name]
        assert fallback in allowed or fallback == "", (
            f"{field.name} falls back to {fallback!r}, which it does not offer"
        )


def test_hydration_accepts_every_value_the_page_offers() -> None:
    """The allowed set and the offered set are ONE list, not two.

    They were two, and had drifted apart in both directions without a word:
    `syntax_theme` was offered "light" and "dark" but hydration dropped them,
    so picking either saved and reverted on the next request; `default_homepage`
    was re-validated against "courses" and "activity", names it does not offer,
    while every real option but "dashboard" was thrown away.
    """
    allowlists = _choice_allowlists()
    for field in PREFERENCE_FIELDS:
        if field.kind != "choice":
            continue
        allowed, _ = allowlists[field.name]
        offered = {choice.value for choice in field.choices}
        assert offered == allowed, (
            f"{field.name}: the page offers {sorted(offered - allowed)} that "
            f"hydration drops, and re-validates {sorted(allowed - offered)} "
            f"that the page does not offer"
        )


def test_every_choice_preference_is_hydrated() -> None:
    """A choice the session never carries is a setting that does nothing off
    its own page. preferred_language is the one exemption: NULL there means
    "follow the browser", so the locale middleware keeps deciding."""
    for field in PREFERENCE_FIELDS:
        if field.kind != "choice" or field.name == "preferred_language":
            continue
        assert f'("{field.name}", {field.name})' in DEPENDENCIES, (
            f"{field.name} is offered but never hydrated into the session"
        )


TOKENS_CSS = (REPO / "src/app/templates/static/css/tokens.css").read_text(encoding="utf-8")


def test_layout_width_uncaps_every_content_wrapper_not_just_one() -> None:
    """FIVE elements cap themselves at --content-width-lg: .main-container, the
    job bar, the cookie banner and both global banners. Overriding only
    .main-container left the chrome above it narrow while the content spread,
    which is why "Fluid" read as broken. The TOKEN is flipped instead, so all
    five move together and a wrapper added later inherits it."""
    assert 'html[data-layout-width="fluid"]' in TOKENS_CSS
    # Read to the rule's closing brace, not a fixed character window: a comment
    # explaining the rule was added inside it and pushed the declarations past
    # the 120 chars this used to look at, so the check silently started failing
    # on a rule that was still correct.
    body = TOKENS_CSS.split('html[data-layout-width="fluid"]')[1]
    rule = body[: body.index("}")]
    assert "--content-width-lg: none" in rule

    # No per-element override may creep back and re-split the behaviour.
    assert 'html[data-layout-width="fluid"] .main-container' not in NAVBAR_CSS


def test_every_content_wrapper_uses_the_token() -> None:
    """A wrapper hardcoding 1280px or 1296px would not follow the fluid setting."""
    import glob
    import re

    offenders = []
    width_re = re.compile(r"(?:max-)?width:\s*(?:1280|1296)px")
    for path in glob.glob(str(REPO / "src/app/templates/static/css/**/*.css"), recursive=True):
        if ".min." in path:
            continue
        body = Path(path).read_text(encoding="utf-8")
        has_hardcoded = width_re.search(body)
        is_token_exempt = "--content-width-lg:" in body or "--gl-layout-width" in body
        if has_hardcoded and not is_token_exempt:
            offenders.append(Path(path).name)
    assert not offenders, f"hardcoded content width, will ignore Fluid: {offenders}"


def test_accent_colours_the_selected_nav_item() -> None:
    """The accent is a ROOT token (tokens.css): one colour per theme that the
    sidebar surface and the shared selected highlight are both derived from."""
    tokens = (REPO / "src/app/templates/static/css/tokens.css").read_text(encoding="utf-8")
    for accent in ("indigo", "blue", "green", "red", "gray"):
        assert f'html[data-accent="{accent}"]' in tokens, f"{accent} has no rule"
    # `default` must NOT be restyled: an untouched account keeps the blue
    # alpha tokens byte for byte.
    assert 'not([data-accent="default"])' in tokens
    assert "--sidebar-active-bg: var(--gl-action-selected-bg-default);" in SIDEBAR_CSS


def test_shortcuts_are_gated_at_the_single_dispatcher() -> None:
    """Gating each handler instead would leave the next one someone adds
    ungated. Escape is not a registered shortcut, so dialogs still close."""
    assert "data-no-shortcuts" in SHORTCUTS_JS
    gate = SHORTCUTS_JS.split("document.addEventListener('keydown'")[1][:900]
    assert "data-no-shortcuts" in gate, "the gate is not inside the keydown dispatcher"

    registered = set(re.findall(r"registerShortcut\('([^']+)'", SHORTCUTS_JS))
    assert "escape" not in {r.lower() for r in registered}


def test_time_format_reaches_every_absolute_rendering() -> None:
    """Routing only one branch through fmtClock would leave a 24h stamp beside
    a 12h one on the same page."""
    assert "function fmtClock" in TIME_JS
    assert TIME_JS.count("fmtClock(d)") >= 4
    assert "data-time-format" in TIME_JS


def test_relative_times_can_be_turned_off() -> None:
    assert "data-absolute-times" in TIME_JS
    assert "absoluteTimesForced" in TIME_JS


def test_saving_a_language_writes_the_switcher_cookie() -> None:
    """resolve_locale reads the cookie before any account value, so a saved
    language that did not write it would appear not to save at all."""
    source = (REPO / "src/app/api/dashboard/preferences.py").read_text(encoding="utf-8")
    assert "set_locale_cookie" in source
    assert "delete_cookie" in source, "System default must drop the pin"


# -- Responsiveness ---------------------------------------------------------

PREFS_CSS = (REPO / "src/app/templates/static/css/pages/preferences.css").read_text(
    encoding="utf-8"
)

LAYOUT_CSS = (REPO / "src/app/templates/static/css/layout.css").read_text(encoding="utf-8")
LAYOUT_HTML = (REPO / "src/app/templates/components/layout.html").read_text(encoding="utf-8")


def test_a_section_stacks_its_description_under_its_heading() -> None:
    """GitLab's settings sections read heading, then description underneath.

    `.section-title-group` was a ROW, so a whole sentence sat on the same line
    as a 21px heading and neither read as the other's caption. The disclosure
    chevron still belongs beside the title, which is why the title has its own
    row inside the column.
    """
    group = LAYOUT_CSS.split(".section-title-group {")[1]
    group = group[: group.index("}")]
    assert "flex-direction: column" in group, (
        "the heading and its description are side by side again"
    )

    row = LAYOUT_CSS.split(".section-title-row {")[1]
    row = row[: row.index("}")]
    reason = "the disclosure chevron must stay beside the title, not above it"
    assert "display: flex" in row, reason
    assert "column" not in row, reason

    # The markup has to match: title inside the row, description outside it.
    block = LAYOUT_HTML.split('<div class="section-title-group">')[1]
    title_at = block.index('class="section-title"')
    row_close = block.index("</div>")
    subtitle_at = block.index('class="section-subtitle"')
    assert title_at < row_close < subtitle_at, (
        "the description must be a sibling of the title row, not inside it"
    )


def test_preferences_page_adds_no_new_breakpoint() -> None:
    """GitLab ships four breakpoints and the app already carries a frozen debt
    list (test_gitlab_breakpoint_inventory). A new page must not grow it."""
    assert not re.findall(r"\((?:max|min)-width:\s*[0-9.]+px\)", PREFS_CSS)


def test_accent_grid_reflows_instead_of_using_media_queries() -> None:
    """auto-fit reaches GitLab's 2/3/6-column theme picker at every width
    without three hand-written breakpoints."""
    assert "repeat(auto-fit, minmax(" in PREFS_CSS


def test_nothing_on_the_page_can_force_a_horizontal_scrollbar() -> None:
    """A fixed width on a flex/grid child is the usual cause. Two fixed
    dimensions are allowed: the 32px accent swatch, which is `flex: 0 0 auto` on
    purpose, and the 16px line-number gutter, which sits inside a `<pre>` that
    clips its own content and so cannot push anything wider."""
    widths = re.findall(r"(?m)^\s*width:\s*([^;]+);", PREFS_CSS)
    for value in widths:
        assert value.strip() in {"32px", "16px", "100%", "auto"}, (
            f"unexpected fixed width {value.strip()} - can overflow a narrow viewport"
        )
    # The label column must be allowed to shrink, or long text pushes the row.
    assert "min-width: 0" in PREFS_CSS
    # The action row wraps rather than overflowing on a phone.
    assert "flex-wrap: wrap" in PREFS_CSS


def test_the_page_states_no_native_tooltips() -> None:
    """The app's rule: component tooltips (Tippy) only. The Mode switcher this
    page reuses already carries data-tippy-content for each button."""
    switcher = (REPO / "src/app/templates/components/theme_switcher.html").read_text(
        encoding="utf-8"
    )
    assert "data-tippy-content" in switcher
    assert " title=" not in switcher


# -- Diff colours -----------------------------------------------------------

STUDENT_CSS = (REPO / "src/app/templates/static/css/pages/student.css").read_text(encoding="utf-8")
PREFS_JS = (REPO / "src/app/templates/static/js/pages/preferences.js").read_text(encoding="utf-8")


def test_diff_colours_reach_the_real_diff_renderer() -> None:
    """Not a preview-only setting: the student profile renders the unified diff
    these colour, so the override has to land on .dn-code-row itself."""
    for prop in ("--gl-diff-color-added", "--gl-diff-color-removed"):
        assert prop in STUDENT_CSS, f"{prop} never reaches the diff rows"
    # ...with the theme's own green/red per colour mode as the default
    # (tokens.css), so an account that never set one renders in its mode's
    # steps; the inline override on <html> out-ranks the stylesheet.
    tokens = (REPO / "src/app/templates/static/css/tokens.css").read_text(encoding="utf-8")
    assert tokens.count("--gl-diff-color-added:") == 2, "the diff colour is not declared per mode"
    assert tokens.count("--gl-diff-color-removed:") == 2
    assert "var(--gl-diff-color-added, " not in STUDENT_CSS, "a page fallback shadows the token"


def test_diff_colours_are_only_emitted_when_overridden() -> None:
    """An empty custom-property value is invalid CSS and drops the whole
    declaration, which would take the other colour down with it."""
    assert "_diff_style" in BASE_HTML
    assert "diff_color_removed" in BASE_HTML
    assert "diff_color_added" in BASE_HTML


def test_diff_colours_are_revalidated_before_reaching_a_style_attribute() -> None:
    """These two are interpolated into style="", so the hydration check must be
    the strict #RRGGBB one - not merely 'is a string'."""
    assert "_HEX_COLOR" in DEPENDENCIES
    assert "[0-9a-fA-F]{6}" in DEPENDENCIES


def test_the_preview_is_the_real_diff_component() -> None:
    """A separately styled mock preview drifts from the thing it previews."""
    template = (REPO / "src/app/templates/preferences.html").read_text(encoding="utf-8")
    assert "dn-code-row--del" in template
    assert "dn-code-row--add" in template
    assert "dn-code-table" in template


def test_the_preview_repaints_live_and_ignores_half_typed_hex() -> None:
    assert "repaintPreview" in PREFS_JS
    assert "#[0-9a-fA-F]{6}" in PREFS_JS
    # Restoring defaults must repaint too, or the preview keeps the old colour.
    restore = PREFS_JS.split("applyValues(form, defaults);")[1][:120]
    assert "repaintPreview()" in restore


# -- Notifications ----------------------------------------------------------

EMAIL_SERVICE = (REPO / "src/app/services/email_notifications.py").read_text(encoding="utf-8")


def test_every_email_category_has_an_opt_out_or_is_deliberately_exempt() -> None:
    """A category with no flag can never be turned off; a flag with no category
    can never take effect. Both are silent failures, so the two lists are held
    against each other."""
    import re as _re

    from app.services.email_notifications import NOTIFICATION_OPT_OUTS

    sent = set(_re.findall(r'category="([a-z_]+)"', EMAIL_SERVICE))
    # welcome: sent before the reader has ever seen the preferences page.
    # general: operational, not a notification the reader subscribes to.
    exempt = {"welcome", "general"}
    uncovered = sent - set(NOTIFICATION_OPT_OUTS) - exempt
    assert not uncovered, f"email categories with no opt-out: {sorted(uncovered)}"

    stale = set(NOTIFICATION_OPT_OUTS) - sent
    assert not stale, f"opt-outs for categories nothing sends: {sorted(stale)}"


def test_the_opt_out_is_enforced_on_the_server_not_just_the_form() -> None:
    """A preference only the form respects is a suggestion. Every notification
    funnels through enqueue_email, so its single persistence path checks it."""
    assert "_recipient_opted_out" in EMAIL_SERVICE
    assert EMAIL_SERVICE.count("await _recipient_opted_out(to_email, category, local_factory)") == 1


def test_the_opt_out_fails_open() -> None:
    """An unreachable database must not silently swallow mail: a missed ticket
    notification is worse than an unwanted one."""
    body = EMAIL_SERVICE.split("async def _recipient_opted_out")[1].split("\ndef ")[0]
    assert "except Exception" in body
    assert "return False" in body
    # None (no account with that address - an external recipient) must send.
    assert "wants is False" in body


@pytest.mark.parametrize("flag", ["notify_tickets", "notify_courses", "notify_account"])
def test_notification_flags_are_hydrated_and_exposed(flag: str) -> None:
    from app.api.dashboard.preferences import PREFERENCE_FIELDS

    assert flag in {f.name for f in PREFERENCE_FIELDS}
    assert User.__table__.columns[flag].nullable is False


# -- GitLab settings-section chrome -----------------------------------------
#
# Ground truth: app/components/layouts/settings_section_component.html.haml and
# app/assets/stylesheets/page_bundles/profiles/preferences.scss.

TOKENS_FOR_TYPE = (REPO / "src/app/templates/static/css/tokens.css").read_text(encoding="utf-8")


def test_section_headings_use_gitlabs_heading_2_scale() -> None:
    """GitLab renders every settings heading as h2.gl-heading-2 - a RESPONSIVE
    clamp from 21px to 25px. The page shipped them at the base 14px, which is
    why the type read as wrong beside GitLab's."""
    assert "--gl-font-size-600: clamp(" in TOKENS_FOR_TYPE
    assert "1.3125rem" in TOKENS_FOR_TYPE  # 21px floor
    assert "1.5625rem" in TOKENS_FOR_TYPE  # 25px ceiling
    assert "--gl-line-height-heading: 1.25" in TOKENS_FOR_TYPE
    assert "--gl-letter-spacing-heading: -0.01em" in TOKENS_FOR_TYPE

    forms = (REPO / "src/app/templates/static/css/forms.css").read_text(encoding="utf-8")
    rule = forms.split(".settings-form .section-title")[1][:300]
    for prop in (
        "var(--gl-font-size-600)",
        "var(--gl-line-height-heading)",
        "var(--gl-letter-spacing-heading)",
        "var(--gl-font-weight-heading)",
    ):
        assert prop in rule, f"heading is missing {prop}"


def test_section_headers_are_sticky() -> None:
    """`.settings-sticky-header` is a real GitLab class - the heading stays put
    while its own section scrolls past. An opaque background is required or the
    body text shows through underneath it."""
    # Read to the rule's closing brace rather than a fixed character window:
    # a comment inside the rule pushed `background:` past the window and the
    # check failed on a rule that was still correct. Same flaw as the
    # layout-width check in this file.
    forms = (REPO / "src/app/templates/static/css/forms.css").read_text(encoding="utf-8")
    body = forms.split(".settings-form .section-header")[1]
    rule = body[: body.index("}")]
    assert "position: sticky" in rule
    assert "top: 0" in rule
    assert "background:" in rule, "a transparent sticky header shows text through"
    assert "z-index" in rule
    # It must pass UNDER the scroll-boundary strip, which is sticky at the same
    # offset - otherwise the strip disappears the moment the page scrolls.
    strip = (REPO / "src/app/templates/static/css/sidebar.css").read_text(encoding="utf-8")
    strip_rule = strip.split(".gl-page-content::before")[1]
    strip_z = int(strip_rule[: strip_rule.index("}")].split("z-index:")[1].split(";")[0])
    header_z = int(rule.split("z-index:")[1].split(";")[0])
    assert header_z < strip_z, (
        f"the sticky heading (z-index {header_z}) must sit below the scroll-boundary "
        f"strip (z-index {strip_z}), or it paints over the line under the breadcrumb"
    )


def test_theme_preview_uses_gitlabs_own_values() -> None:
    """preferences.scss sets these five explicitly; approximating them is what
    made the previews not match. Dark hardcodes #18171e on purpose - GitLab
    notes a tinted theme scope would otherwise drag the panel colour with it."""
    assert "var(--gl-gray-50)" in PREFS_CSS
    assert "var(--gl-gray-0)" in PREFS_CSS
    assert "#18171e" in PREFS_CSS
    for ink in ("--alpha-dark-8", "--alpha-dark-16", "--alpha-dark-24"):
        assert ink in PREFS_CSS
    for ink in ("--alpha-light-8", "--alpha-light-16", "--alpha-light-24"):
        assert ink in PREFS_CSS, f"{ink} missing - dark ink falls back to light"
        assert f"{ink}:" in TOKENS_FOR_TYPE, f"{ink} is used but never defined"


def test_theme_preview_matches_the_preview_rule() -> None:
    """font-size: 0 / gl-border / gl-rounded-lg / gl-mb-3 / overflow hidden."""
    rule = PREFS_CSS.split(".gl-theme-preview {")[1][:420]
    assert "font-size: 0" in rule
    assert "border-radius: var(--gl-border-radius-lg)" in rule
    assert "overflow: hidden" in rule
    assert "margin-bottom: var(--gl-spacing-3)" in rule


# -- GitPulse's own preferences (not copied from GitLab) --------------------

PAGINATOR_JS = (REPO / "src/app/templates/static/js/components.js").read_text(encoding="utf-8")
SIDEBAR_JS = (REPO / "src/app/templates/static/js/sidebar.js").read_text(encoding="utf-8")


def test_rows_per_page_is_an_account_default_the_paginator_reads() -> None:
    """The "Per page" control already existed and wrote localStorage per table,
    so a new device silently fell back to 50 however the reader had it set."""
    assert "data-page-size" in BASE_HTML
    assert "data-page-size" in PAGINATOR_JS
    assert "accountDefault" in PAGINATOR_JS


def test_a_per_table_choice_still_beats_the_account_default() -> None:
    """The local choice is the more specific answer AND the more recent one -
    the account value is a default, not an override."""
    block = PAGINATOR_JS.split("this.pageSize = saved")[1][:220]
    assert "accountDefault" in block, "the account value must be the FALLBACK branch"


def test_sidebar_default_applies_only_where_there_is_no_local_state() -> None:
    assert "data-sidebar-collapsed" in BASE_HTML
    assert "data-sidebar-collapsed" in SIDEBAR_JS
    block = SIDEBAR_JS.split("savedState = localStorage.getItem('sidebar-collapsed')")[1][:260]
    assert "savedState === null" in block, "it must not override a local choice"


@pytest.mark.parametrize("pref", ["default_page_size", "sidebar_collapsed"])
def test_gitpulse_preferences_are_hydrated(pref: str) -> None:
    assert f"User.{pref}" in DEPENDENCIES
    # A "choice" preference is hydrated by the table-driven loop, a bool by a
    # line of its own; either way it has to reach the session.
    assigned = f'session_data["{pref}"]' in DEPENDENCIES
    hydrated_by_table = f'("{pref}", {pref})' in DEPENDENCIES
    assert assigned or hydrated_by_table, f"{pref} never reaches the session"

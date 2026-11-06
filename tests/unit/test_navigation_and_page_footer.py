"""Navigation controls retain their destination and the page footer keeps its layout."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "app"
TEMPLATES = SRC / "templates"
CORE_JS = TEMPLATES / "static" / "js" / "_parts" / "core"


def _js(name: str) -> str:
    return (CORE_JS / name).read_text(encoding="utf-8")


def _tpl(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def _css(name: str) -> str:
    """Stylesheet with /* comments */ stripped, so prose cannot satisfy a rule."""
    raw = (TEMPLATES / "static" / "css" / name).read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)


# --------------------------------------------------------------------------
# Auto-reload on job completion is page-scoped
# --------------------------------------------------------------------------


def test_job_reload_registration_is_clearable() -> None:
    """`GP.clearJobReload` must exist and actually empty the pattern list.

    Without it, patterns registered by one page (Admin > Courses registers
    `['sync*', 'import']`) outlive that page: core.bundle.js is loaded once in
    <head> and SPA navigation only swaps #main-content, so a sync finishing while
    the reader sat on the Dashboard hard-reloaded THAT page.
    """
    src = _js("16-reload.js")
    assert "GP.clearJobReload = function clearJobReload" in src
    body = src.split("GP.clearJobReload = function clearJobReload", 1)[1][:400]
    assert "_jobReloadPatterns.length = 0" in body


def test_navigation_clears_job_reload_registration() -> None:
    """Leaving a page must retire its auto-reload registration.

    The call belongs next to `activePageCleanup` before the successful swap,
    so it cannot race the incoming page's own registration. Failed requests
    leave the current page's registration intact.
    """
    src = _js("42-spa-navigation.js")
    assert "GP.clearJobReload()" in src
    cleanup_at = src.index("GP.runPageCleanup();")
    clear_at = src.index("GP.clearJobReload()")
    assert 0 < clear_at - cleanup_at < 400, "clearJobReload must sit with activePageCleanup"


def test_navigation_feedback_does_not_claim_a_measured_percentage() -> None:
    """Requests have no measured completion fraction; the indicator is indeterminate.

    Real concurrent requests, failures and page readiness are exercised in
    test_navigation_request_states.py, including reduced page script availability.
    """
    src = _js("40-top-progress.js")
    assert "setAttribute('role', 'progressbar')" in src
    assert "aria-valuenow" not in src
    assert "GP.motion.topProgress(bar, inner)" in src
    assert "Math.random" not in src


# --------------------------------------------------------------------------
# Page footer
# --------------------------------------------------------------------------


def test_page_footer_renders_inside_main_content() -> None:
    """The footer must live inside #main-content so a content swap carries it.

    Anything outside that region survives SPA navigation and would need explicit
    reconciliation - which is how the Dashboard would end up wearing another
    page's footer.
    """
    base = _tpl("base.html")
    footer_at = base.index('<footer class="gl-page-footer">')
    main_open = base.index('<main id="main-content"')
    main_close = base.index("</main>", main_open)
    assert main_open < footer_at < main_close


def test_page_footer_is_opt_out_and_dashboard_opts_out() -> None:
    """Every page gets the footer except the Dashboard.

    The home sidebar already ends with the "Support & suggestions" panel, so the
    shell footer would duplicate its feedback link.
    """
    base = _tpl("base.html")
    assert "{% if page_footer|default(true) %}" in base
    assert re.search(r"{%\s*set page_footer = false\s*%}", _tpl("dashboard.html"))


def test_page_footer_carries_both_links() -> None:
    base = _tpl("base.html")
    block = base.split('<footer class="gl-page-footer">', 1)[1].split("</footer>", 1)[0]
    assert "t('Leave feedback')" in block
    assert "t('Documentation')" in block
    assert 'class="gl-page-footer-sep"' in block, "GitLab separates the pair with a bar"


def test_page_footer_is_styled() -> None:
    css = _css("navbar.css")
    block = css.split(".gl-page-footer {", 1)[1].split("}", 1)[0]
    assert "justify-content: center" in block, "GitLab centres the footer"


# The KPI-card test that used to live here is deliberately gone. It pinned
# "outlined, colour-only, no transform" - a reading of GitLab parity the author
# rejected on sight, twice. The cards keep their own filled style with the lift,
# and a test asserting otherwise would only re-break them on the next edit.

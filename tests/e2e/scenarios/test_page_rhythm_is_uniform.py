"""The pages must share one vertical rhythm, not each invent its own.

The report was that the Dashboard reads as designed and every other page reads
as chaos. Measuring them said the cards themselves are uniform - one style, one
radius, one padding - and that what actually differed was the SPACING between
the blocks, which no page sets deliberately: it falls out of whatever the last
element on that page happens to carry as a margin.

That is the kind of defect a screenshot shows and a component test cannot: each
page is self-consistent, so nothing looks wrong until two pages sit side by
side. These checks compare pages against each other, which is the only place
the inconsistency exists.
"""

from __future__ import annotations

from contextlib import suppress
from urllib.parse import urlsplit

import pytest

pytestmark = pytest.mark.e2e

# Pages built from the standard shell: a `.page-header`, then content blocks,
# then the footer. The Dashboard is deliberately not one of them - it has no
# page header and no footer (its sidebar carries the feedback link instead), so
# it has no rhythm to compare.
_SHELL_PAGES = (
    "/dashboard/admin/users",
    "/dashboard/admin/courses",
    "/dashboard/admin/system",
    "/dashboard/admin/events",
    "/dashboard/preferences",
)

_RHYTHM = """
() => {
  const mc = document.querySelector('.main-container');
  if (!mc) return {error: 'no .main-container'};
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return r.height > 0 && s.display !== 'none'
      && s.position !== 'absolute' && s.position !== 'fixed';
  };
  const kids = [...mc.children].filter(vis);
  const box = (e) => {
    const r = e.getBoundingClientRect();
    return {top: Math.round(r.top), bottom: Math.round(r.bottom),
            left: Math.round(r.left), width: Math.round(r.width)};
  };
  const header = mc.querySelector(':scope > .page-header');
  const footer = mc.querySelector(':scope > .gl-page-footer');
  // A sticky save bar replaces the page footer.
  const savebar = !!mc.querySelector('.settings-sticky-footer');
  const prevOfFooter = footer ? kids[kids.indexOf(footer) - 1] : null;
  return {
    contentLeft: kids.length ? box(kids[0]).left : null,
    contentWidth: kids.length ? box(kids[0]).width : null,
    headerTop: header ? box(header).top : null,
    // Gap between the page header and the first block under it.
    afterHeader: (header && kids.indexOf(header) + 1 < kids.length)
      ? box(kids[kids.indexOf(header) + 1]).top - box(header).bottom : null,
    // Gap between the last content block and the footer.
    beforeFooter: (footer && prevOfFooter)
      ? box(footer).top - box(prevOfFooter).bottom : null,
    savebar,
  };
}
"""


@pytest.fixture(scope="module")
def rhythm(browser, live_server: str) -> dict[str, dict]:
    """Measure every shell page once; the checks below compare the results.

    Module-scoped because all four checks read the same measurements - walking
    five pages once instead of once per assertion.
    """
    from app.security.session_auth import SESSION_COOKIE_NAME
    from tests.e2e.scenarios.conftest import _session_token

    host = urlsplit(live_server).hostname or "127.0.0.1"
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.add_cookies(
        [
            {
                "name": SESSION_COOKIE_NAME,
                "value": _session_token("admin"),
                "domain": host,
                "path": "/",
            }
        ]
    )
    try:
        page = context.new_page()
        out: dict[str, dict] = {}
        for path in _SHELL_PAGES:
            response = page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
            assert response is not None, f"{path} returned no response"
            assert response.status < 400, f"{path} -> {response.status}"
            page.wait_for_timeout(900)
            out[path] = page.evaluate(_RHYTHM)
            assert "error" not in out[path], f"{path}: {out[path]['error']}"
        return out
    finally:
        with suppress(Exception):
            context.close()


def test_every_page_starts_its_content_at_the_same_place(rhythm):
    """A page that indents differently reads as a different application."""
    lefts = {p: v["contentLeft"] for p, v in rhythm.items()}
    widths = {p: v["contentWidth"] for p, v in rhythm.items()}
    assert len(set(lefts.values())) == 1, f"content starts at different x: {lefts}"
    assert len(set(widths.values())) == 1, f"content has different widths: {widths}"


def test_every_page_header_sits_at_the_same_height(rhythm):
    tops = {p: v["headerTop"] for p, v in rhythm.items()}
    assert None not in tops.values(), f"a shell page has no .page-header: {tops}"
    assert len(set(tops.values())) == 1, f"page headers start at different y: {tops}"


def test_the_gap_under_the_page_header_is_the_same_everywhere(rhythm):
    gaps = {p: v["afterHeader"] for p, v in rhythm.items()}
    assert len(set(gaps.values())) == 1, f"inconsistent gap under the header: {gaps}"


def test_the_gap_above_the_footer_is_the_same_everywhere(rhythm):
    """This one was genuinely broken.

    The footer's `margin-top` collapses with the last block's `margin-bottom`,
    and a collapse takes the larger of the two - so the gap was 32px on the
    pages ending in a card and 24px on the pages ending in a form or a bare
    div. Nothing declared either number; the page's last element decided it.
    """
    # A page that ends in a sticky save bar (Preferences) has no footer by
    # design - the bar is its last line - so it has no gap above one.
    gaps = {p: v["beforeFooter"] for p, v in rhythm.items() if not v["savebar"]}
    assert None not in gaps.values(), f"a shell page has no footer: {gaps}"
    assert len(set(gaps.values())) == 1, (
        f"the space above the footer depends on what the page ends with: {gaps}"
    )

"""A navigation says it is loading without covering the page or moving anything.

Measured in the browser, because every one of these is about what the reader
sees and where:

  1. the top progress bar, from the first millisecond;
  2. the CLICKED control, when it leads with an icon: that icon becomes the app's
     spinner, in its own box, so the control does not change size by a pixel;
  3. a `progress` cursor over the content region - which is what reports a click
     on a card, a table row or a bare link, none of which has an icon slot.

Four page-level shapes were tried before this and every one was reported: a
blanked page, a toast, a full-screen veil carrying a second copy of the brand
mark, and a "Loading..." pill. The pill was visible but was one more thing on the
screen saying what the progress bar already said.

The placement rule is the other thing under test here. It used to be "the first
icon anywhere inside the control", which put a spinner in the top-right corner of
a stat card, on top of that card's own category icon - reported as "chaotically
placed, not where it should be". The rule is now "the control's FIRST child, if
it sits in the leading quarter", and a control that has no such icon gets no mark
at all.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_LINK = "/dashboard/admin/users"
# Long enough to reach the 4s line and still leave the fetch in flight.
_LATENCY_MS = 6000

_SNAPSHOT = """
(href) => {
  const link = document.querySelector('a[href="' + href + '"]');
  const bar = document.getElementById('gp-top-progress');
  const mc = document.getElementById('main-content');
  const box = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return {x: Math.round(b.x), y: Math.round(b.y),
            w: Math.round(b.width), h: Math.round(b.height)};
  };
  const scroller = document.querySelector('.gl-page-content');
  return {
    pageLevelLoaders: document.querySelectorAll('.gp-nav-loader, .gp-nav-pill').length,
    busy: link ? link.getAttribute('aria-busy') : null,
    mark: !!(link && link.querySelector('.nav-busy-spinner .gp-spinner')),
    linkBox: box(link),
    progressOpacity: bar ? parseFloat(getComputedStyle(bar).opacity) : 0,
    contentOpacity: mc ? parseFloat(getComputedStyle(mc).opacity) : 0,
    contentPointerEvents: mc ? getComputedStyle(mc).pointerEvents : null,
    cursor: scroller ? getComputedStyle(scroller).cursor : null,
  };
}
"""


def _slow_network(ctx, page) -> None:
    cdp = ctx.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": _LATENCY_MS,
            "downloadThroughput": -1,
            "uploadThroughput": -1,
        },
    )


def _open_dashboard(page, live_server: str) -> None:
    # SSE keeps connections open; page readiness does not require network idle.
    page.goto(live_server + "/dashboard/", wait_until="load")
    page.wait_for_function("""() => window.GP?.navigateTo
      && document.documentElement.hasAttribute('data-gp-ready')""")
    page.evaluate("() => document.fonts.ready")


def test_the_wait_is_shown_on_the_control_that_was_clicked(context_for, live_server: str) -> None:
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    _open_dashboard(page, live_server)

    idle = page.evaluate(_SNAPSHOT, _LINK)
    assert idle["linkBox"], f"no sidebar link to {_LINK} on this page"

    _slow_network(ctx, page)
    page.click(f"a[href='{_LINK}']", no_wait_after=True)
    page.wait_for_timeout(700)
    busy = page.evaluate(_SNAPSHOT, _LINK)

    assert busy["pageLevelLoaders"] == 0, "a page-level loader is back over the page"
    assert busy["busy"] == "true", "the clicked control does not say it is busy"
    assert busy["mark"], "the clicked control shows no loading mark"
    assert busy["linkBox"] == idle["linkBox"], (
        f"the control moved or resized when it became busy: {idle['linkBox']} -> {busy['linkBox']}"
    )
    assert busy["progressOpacity"] > 0, "the top progress bar is not running"
    assert busy["cursor"] == "progress", "the content region does not say it is busy"

    # The page it is leaving stays on screen and stays readable - it is the only
    # content there is until the next one lands - but it must not look live.
    assert busy["contentOpacity"] >= 0.7, (
        f"the outgoing page is dimmed to {busy['contentOpacity']} - that reads as broken, not busy"
    )
    assert busy["contentPointerEvents"] == "none", "the stale page is still clickable"


def test_a_control_with_no_leading_icon_gets_no_mark(context_for, live_server: str) -> None:
    """The stat card is the control the old rule got wrong: it leads with a
    heading and carries its own category icon in the corner, which a
    `querySelector('svg')` happily found. Nothing may be put on it now - the
    bar and the cursor report the click instead."""
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    _open_dashboard(page, live_server)

    card = page.evaluate(
        """() => {
          const a = Array.from(document.querySelectorAll('a.gl-home-stat[href]'))[0];
          return a ? a.getAttribute('href') : null;
        }"""
    )
    if not card:
        pytest.skip("this account sees no linked stat card on the dashboard")

    _slow_network(ctx, page)
    page.click(f"a.gl-home-stat[href='{card}']", no_wait_after=True)
    page.wait_for_timeout(600)

    seen = page.evaluate(
        """(href) => {
          const a = document.querySelector(`a.gl-home-stat[href='${href}']`);
          const scroller = document.querySelector('.gl-page-content');
          return {
            busy: a.getAttribute('aria-busy'),
            mark: !!a.querySelector('.nav-busy-spinner'),
            hiddenIcon: !!a.querySelector('.is-nav-busy-icon'),
            cursor: getComputedStyle(scroller).cursor,
            pageLevelLoaders: document.querySelectorAll('.gp-nav-loader, .gp-nav-pill').length,
          };
        }""",
        card,
    )
    assert seen["busy"] == "true", "the clicked card does not say it is busy"
    assert not seen["mark"], "a mark was put on a control with no icon slot for it"
    assert not seen["hiddenIcon"], "the card's own icon was hidden to make room for a mark"
    assert seen["cursor"] == "progress", "nothing reports the click on this card"
    assert seen["pageLevelLoaders"] == 0, "a page-level loader is back"


def test_the_mark_keeps_turning_under_reduced_motion(context_for, live_server: str) -> None:
    """animations.css carries a blanket `* { animation-duration: 0.01ms
    !important; animation-iteration-count: 1 !important }` for reduced motion,
    which every spinner in the app used to lose to - measured `spin 1e-05s 1`,
    a mark that renders one frame and then stands still. A frozen spinner says
    the app has hung, which is the opposite of what it is there for."""
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    cdp = ctx.new_cdp_session(page)
    cdp.send(
        "Emulation.setEmulatedMedia",
        {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
    )
    _open_dashboard(page, live_server)

    _slow_network(ctx, page)
    page.click(f"a[href='{_LINK}']", no_wait_after=True)
    page.wait_for_selector(".nav-busy-spinner .gp-spinner", timeout=8000)

    ring = page.evaluate(
        """
        () => {
          const s = document.querySelector('.nav-busy-spinner .gp-spinner');
          const cs = getComputedStyle(s, '::before');
          return {name: cs.animationName, duration: cs.animationDuration,
                  iterations: cs.animationIterationCount};
        }
        """
    )
    assert ring["name"] == "spin", "the mark has no turn animation at all"
    assert ring["iterations"] == "infinite", (
        f"the mark turns {ring['iterations']} time(s) and then stops - it is frozen for the "
        "rest of the fetch"
    )
    assert float(ring["duration"].rstrip("s")) > 0.5, (
        f"the turn lasts {ring['duration']} - fast enough to be invisible, which is the same "
        "as frozen"
    )

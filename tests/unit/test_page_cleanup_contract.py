"""Every page bundle retires its own listeners and timers.

The SPA swaps `#main-content` and re-injects the page's `js/pages/*.js` on every
navigation into that page - `_loadScriptsSeq` in core/42-spa-navigation.js says
so in as many words ("always re-run (drop the stale copy first)"). A bundle that
registers a `document` or `window` listener therefore registers it AGAIN on
every visit, so the contract is:

    1. retire the previous page on entry - `GP.runPageCleanup()`, which runs
       its `GP.activePageCleanup` once;
    2. publish your own teardown as `GP.activePageCleanup` on the way out.

Sixteen of the eighteen bundles did both. `preferences.js` did neither: its
`htmx:afterSwap` listener accumulated one copy per visit, and after N visits
every swap anywhere in the app ran its `init()` N times.

`login.js` and `logout.js` are exempt: those pages are rendered outside the SPA
shell (no `hx-boost`, no `#main-content`), so their scripts run once per real
document load and there is nothing to retire.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGES = REPO / "src/app/templates/static/js/pages"
CORE = REPO / "src/app/templates/static/js/_parts/core"

OUTSIDE_THE_SPA = {"login.js", "logout.js"}


def _bundles() -> list[Path]:
    return sorted(p for p in PAGES.glob("*.js") if ".min." not in p.name)


def test_page_bundles_are_re_executed_on_navigation() -> None:
    """The premise behind everything else here."""
    src = (CORE / "42-spa-navigation.js").read_text(encoding="utf-8")
    assert "_loadScriptsSeq" in src
    assert "always re-run" in src, (
        "the navigation no longer re-runs page bundles - if that is deliberate, "
        "the cleanup contract these tests enforce may no longer be needed"
    )


def test_every_spa_page_bundle_publishes_a_cleanup() -> None:
    offenders = {}
    for p in _bundles():
        if p.name in OUTSIDE_THE_SPA:
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        adds = len(re.findall(r"(?:document|window)\.addEventListener\(", src))
        if adds and not re.search(r"GP\.activePageCleanup\s*=", src):
            offenders[p.name] = adds
    assert not offenders, (
        f"these register global listeners on every navigation and never retire them: {offenders}"
    )


def test_every_spa_page_bundle_retires_the_previous_page() -> None:
    offenders = []
    for p in _bundles():
        if p.name in OUTSIDE_THE_SPA:
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"(?:document|window)\.addEventListener\(", src):
            continue
        if "GP.runPageCleanup()" not in src:
            offenders.append(p.name)
    assert not offenders, f"these never retire the outgoing page (GP.runPageCleanup()): {offenders}"


def test_the_pages_outside_the_spa_really_are_outside_it() -> None:
    """The exemption has to keep earning itself."""
    templates = REPO / "src/app/templates"
    for name in ("login.html", "logout.html"):
        src = (templates / name).read_text(encoding="utf-8")
        reason = (
            f"{name} now renders inside the SPA shell, so its bundle re-runs on "
            "navigation and must join the cleanup contract"
        )
        assert "hx-boost" not in src, reason
        assert 'id="main-content"' not in src, reason


# Deliberately app-lifetime. The cross-tab leader lease works by every tab
# heartbeating: a tab that is NOT the leader needs its own heartbeat to notice
# the leader stopped renewing and take the lease over. Stopping it in a
# non-leader tab is exactly what would break the takeover. `_startLeaderHeartbeat`
# guards on the handle so it is started once, and `pagehide` releases the lease.
APP_LIFETIME_INTERVALS = {"_leaderHeartbeatId"}


def test_no_interval_is_started_without_a_way_to_stop_it() -> None:
    """A timer that outlives its page keeps polling for the rest of the session."""
    js_root = REPO / "src/app/templates/static/js"
    build = (REPO / "scripts/build_bundle.py").read_text(encoding="utf-8")
    generated = set(re.findall(r'"(pages/[\w-]+\.js)"', build))
    offenders = {}
    for p in js_root.rglob("*.js"):
        if ".min." in p.name or "bundle" in p.name or "vendor" in p.parts:
            continue
        if f"pages/{p.name}" in generated:
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        if p.parent.name == "global-job-bar":
            # These parts share one IIFE; _stopPoller clears handles stored by
            # either transport, rather than duplicating cleanup in each part.
            src = "\n".join(
                part.read_text(encoding="utf-8") for part in sorted(p.parent.glob("*.js"))
            )
        for m in re.finditer(r"(\w+)\s*=\s*(?:window\.)?setInterval\s*\(", src):
            var = m.group(1)
            if var in APP_LIFETIME_INTERVALS:
                continue
            # cleared directly, or parked on an object/map that is cleared later
            if re.search(rf"clearInterval\s*\(\s*[\w.\[\]'\"]*{re.escape(var)}\b", src):
                continue
            if re.search(rf"{re.escape(var)}\s*[,;}}]", src) and "clearInterval" in src:
                continue
            offenders.setdefault(str(p.relative_to(js_root)), []).append(var)
    assert not offenders, f"intervals with no clearInterval path: {offenders}"

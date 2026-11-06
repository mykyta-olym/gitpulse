"""One in-flight request per key, and a superseded one never paints.

A filter changed twice, a tab clicked twice, a refresh that overlaps its own
previous tick: each fires a second request before the first has answered, and
whichever lands LAST wins the DOM - which is not necessarily the one the reader
asked for. It is the same bug wherever it appears, so the answer lives in the
transport rather than in each page: `apiCall(..., { key })` aborts the previous
call under that key, and the superseded promise rejects with `superseded` set
so callers can ignore it instead of painting an error over a live request.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"
BASE = JS / "_parts/core/07-api.js"


def test_the_transport_supersedes_by_key() -> None:
    src = BASE.read_text(encoding="utf-8")
    assert "_inflightByKey" in src, "the keyed in-flight registry is gone"
    assert "prev.superseded = true" in src
    assert "err.superseded = true" in src, (
        "a superseded call no longer marks its rejection, so callers cannot "
        "tell it apart from a real failure"
    )
    assert "_inflightByKey.delete(opts.key)" in src, (
        "the registry is never cleaned up - it would leak one controller per call"
    )


def test_the_keyed_call_still_honours_a_callers_own_signal() -> None:
    src = BASE.read_text(encoding="utf-8")
    block = src.split("if (opts.key) {", 1)[1].split("\n  }\n", 1)[0]
    assert "const signal = config.signal" in block
    assert "signal.addEventListener('abort', onAbort" in block, (
        "passing both `key` and `signal` would silently drop the caller's signal"
    )
    assert "signal.removeEventListener('abort', onAbort)" in block


LIST_LOADERS = {
    "pages/admin-events.js": ("events:recent", "events:dlq"),
    "pages/admin-users.js": ("admin:users:list",),
}


def test_the_list_loaders_are_keyed() -> None:
    missing = {}
    for name, keys in LIST_LOADERS.items():
        src = (JS / name).read_text(encoding="utf-8")
        absent = [k for k in keys if f"'{k}'" not in src]
        if absent:
            missing[name] = absent
    assert not missing, f"these loaders can still be overtaken by a stale response: {missing}"


def test_every_keyed_loader_ignores_a_superseded_rejection() -> None:
    """Otherwise aborting the old request paints its error over the new one."""
    offenders = []
    for name in LIST_LOADERS:
        src = (JS / name).read_text(encoding="utf-8")
        keys = len(re.findall(r"key: '[\w:]+'", src))
        guards = src.count("superseded")
        if guards < keys:
            offenders.append(f"{name}: {keys} keyed calls, {guards} guards")
    assert not offenders, offenders


def test_the_tab_prefetch_stays_narrow() -> None:
    """Some dashboard GETs kick off opportunistic background work, so a
    prefetch must only ever touch the course sub-tabs, which are pure reads."""
    src = (JS / "_parts/core/42-spa-navigation.js").read_text(encoding="utf-8")
    assert "_TAB_RE" in src, "the tab prefetch is gone"
    m = re.search(r"(?:const|let|var) _TAB_RE = (/.*?/);", src)
    assert m, "the prefetch route allowlist is gone"
    pattern = m.group(1)
    for allowed in ("activity", "analytics", "teachers", "settings"):
        assert allowed in pattern
    assert "courses" in pattern, "the prefetch is no longer scoped to course tabs"
    assert "a.tab-btn[href]" in src, "the prefetch listens to more than the tab strip"


POLLS = {
    "_parts/course-detail/00-sync-stream.js": "course-sync-status",
    "_parts/project-detail/10-analysis.js": "analysis-status:",
}


def test_every_repeating_poll_is_keyed() -> None:
    """A poll on a 3-5s interval WILL overlap itself on a slow answer, and then
    the older reply repaints over the newer one."""
    missing = [
        name
        for name, key in POLLS.items()
        if f"'{key}'" not in (JS / name).read_text(encoding="utf-8")
    ]
    assert not missing, f"these polls can still overtake themselves: {missing}"


def test_a_superseded_tick_is_not_treated_as_a_failure() -> None:
    """The sync poll walks itself to a "Connection to server lost" banner after
    N consecutive errors. Counting an abort by its own successor as one of them
    would show that banner while the server was answering perfectly."""
    for name in POLLS:
        src = (JS / name).read_text(encoding="utf-8")
        assert "superseded" in src, f"{name} counts a superseded tick as an error"


def test_the_badge_poll_uses_the_coalescing_mechanic() -> None:
    """It solved this before `key` existed, by folding concurrent calls into one
    re-run rather than aborting - which is right for a poll whose whole job is
    to end up with the freshest counts. That answer was correct and is now
    everyone's: `GP.coalesced`. Its own throttle is separate and stays.

    See tests/unit/test_one_coalescing_mechanic.py for the rest of the rule."""
    src = (JS / "sidebar.js").read_text(encoding="utf-8")
    assert "GP.coalesced('sidebar-badges'" in src
    assert "_POLL_BADGES_MIN_INTERVAL_MS" in src, "the throttle in front of it is gone"


def test_navigation_abandons_in_flight_work() -> None:
    """An internal navigation swaps `#main-content`, so a request started on
    the page being left answers into a DOM that is no longer its own - at best
    writing nothing, at worst painting the previous page's rows, counts or
    error into the page that replaced it."""
    base = BASE.read_text(encoding="utf-8")
    assert "GP.abortInflight = abortInflight;" in base, "the helper is gone"
    body = base.split("function abortInflight()", 1)[1].split("\n}", 1)[0]
    assert "ctl.superseded = true" in body, (
        "an abandoned request must be marked superseded, or callers surface it as a real failure"
    )
    assert "_inflightByKey.clear()" in body

    nav = (JS / "_parts/core/42-spa-navigation.js").read_text(encoding="utf-8")
    assert "GP.abortInflight()" in nav, "the navigation never abandons anything"


def test_only_keyed_calls_are_abandoned() -> None:
    """A one-shot POST with no key - a save, a delete - has to finish even if
    the reader navigates away while it is in flight."""
    base = BASE.read_text(encoding="utf-8")
    body = base.split("function abortInflight()", 1)[1].split("\n}", 1)[0]
    assert "_inflightByKey" in body
    assert "opts.key" not in body, (
        "the abort walks a per-call key, so it would skip the registry entirely"
    )

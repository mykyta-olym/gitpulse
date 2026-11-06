"""A page-level SSE stream is opened in ONE place.

Seven of them had been written out by hand - dashboard, sidebar badges, course
sync, course data, course settings, team, project, and the global job bar's
course stream - and every copy was the same twenty lines: construct inside a
try/catch because a blocked EventSource throws synchronously, zero the error
count whenever anything arrives, and on failure close, count, and either
reconnect after a delay or give up to a polling fallback.

The copies had already drifted. Each kept its reconnect timer OUTSIDE the
connection it belonged to, so "is this stream still trying?" needed a
three-way test - no source AND no poll timer AND no reconnect timer - and the
page that forgot the third term reconnected on top of itself.

A per-JOB stream is a different thing and is deliberately NOT converged: it
ends when its job does, and `GP.streamJobProgress` (sse-stream.js) owns that.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"
BASE = JS / "_parts/core/08-sse.js"

# Individual background jobs use the transport managed by streamJobProgress.
# Page and analysis streams use GP.sse, including the global job bar.
PER_JOB = {
    "sse-stream.js": 1,  # GP.streamJobProgress, the job-progress client
}


def _sources() -> list[Path]:
    parts = sorted((JS / "_parts").rglob("*.js"))
    flat = sorted(JS.glob("*.js"))
    return parts + flat


def test_the_client_exists_once() -> None:
    src = BASE.read_text(encoding="utf-8")
    assert src.count("GP.sse = function") == 1
    body = src.split("GP.sse = function", 1)[1]
    for piece in ("onGiveUp", "onBlocked", "reconnectMs", "maxErrors"):
        assert piece in body, f"the shared client lost {piece}"


def test_page_streams_do_not_construct_their_own() -> None:
    offenders = []
    for path in _sources():
        if path == BASE:
            continue
        src = path.read_text(encoding="utf-8")
        n = len(re.findall(r"new EventSource\(", src))
        allowed = PER_JOB.get(path.name, 0)
        if n > allowed:
            offenders.append(f"{path.name}: {n} (allowed {allowed})")
    assert not offenders, f"hand-rolled SSE clients: {offenders}"


def test_the_job_bar_keeps_its_backoff() -> None:
    """It is the one stream the server closes promptly, so a fixed delay turns
    a finished sync into a tight reconnect loop. The shared client takes a
    function for exactly this."""
    src = (JS / "_parts/global-job-bar/10-sse-render.js").read_text(encoding="utf-8")
    assert "reconnectMs: (n) => Math.min(4000 * n, 20000)" in src


def test_nobody_tracks_a_reconnect_timer_outside_its_stream() -> None:
    """That timer is what made "is the stream still trying?" a three-way test."""
    offenders = []
    for path in _sources():
        if path.name in PER_JOB:
            continue
        src = path.read_text(encoding="utf-8")
        hits = re.findall(r"^\s*(?:let|var)\s+_?\w*[Rr]econnect\w*Timer\s*=", src, re.MULTILINE)
        if hits:
            offenders.append(path.name)
    assert not offenders, f"reconnect timers held outside GP.sse: {offenders}"

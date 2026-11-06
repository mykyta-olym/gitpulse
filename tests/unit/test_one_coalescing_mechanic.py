"""Repeat refreshes are coalesced in ONE place.

Four pollers had hand-rolled the same thing - a module-level `<name>InFlight`
promise plus a `<name>Pending` flag, "join the run in flight, then do exactly
one trailing re-run". Three of the four were in a single file, and one of them
carried a comment pointing at a fourth copy as its reference.

The two halves of the race mechanic answer different questions and both are
needed:

  GP.coalesced(key, fn)   the same read, asked again  -> join it
  apiCall({ key })        a different read of the same region -> supersede

A refresher also passes its coalesce key to apiCall, so navigating away drops
the fetch instead of letting it paint into the page that replaced it.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"

# The shape that was duplicated: a module-level promise holding the run in
# flight AND a flag remembering that another call arrived. Either one alone is
# something else - a one-shot latch, a rAF dedupe - so both must be present.
_IN_FLIGHT = re.compile(r"^\s*(?:let|var)\s+_\w*InFlight\s*=\s*null", re.MULTILINE)
_PENDING = re.compile(r"^\s*(?:let|var)\s+_\w*Pending\s*=\s*false", re.MULTILINE)


def _sources() -> list[Path]:
    parts = sorted((JS / "_parts").rglob("*.js"))
    flat = sorted(JS.glob("*.js"))
    return parts + flat


def test_nobody_hand_rolls_coalescing() -> None:
    offenders = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        if _IN_FLIGHT.search(src) and _PENDING.search(src):
            offenders.append(path.name)
    assert not offenders, f"use GP.coalesced instead: {offenders}"


def test_the_mechanic_is_defined_once() -> None:
    base = (JS / "_parts/core/07-api.js").read_text(encoding="utf-8")
    assert base.count("\nfunction coalesce(") == 1
    assert base.count("\nfunction coalesced(") == 1
    assert "GP.coalesced = coalesced;" in base


def _coalesced_bodies(src: str):
    """Yield (key, body) for each GP.coalesced(...) call, by paren matching."""
    for m in re.finditer(r"GP\.coalesced\(\s*'([a-z-]+)'", src):
        i = src.index("(", m.start())
        depth = 0
        for j in range(i, len(src)):
            if src[j] == "(":
                depth += 1
            elif src[j] == ")":
                depth -= 1
                if depth == 0:
                    yield m.group(1), src[i:j]
                    break


def test_every_coalesced_read_is_droppable_at_navigation() -> None:
    """A coalesce key with no matching apiCall key would survive navigation."""
    unkeyed: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        for key, body in _coalesced_bodies(src):
            # A refresher that pulls an HTML fragment with raw fetch() paints
            # into a node it captured before awaiting, so navigation detaches
            # it harmlessly; only apiCall reads need the key.
            if "apiCall(" in body and f"key: '{key}'" not in body:
                unkeyed.append(f"{path.name}:{key}")
    assert not unkeyed, f"coalesced but not abortable: {unkeyed}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_joined_run_resolves_to_the_loaders_answer(tmp_path: Path) -> None:
    """`coalesced` resolves to what the loader returned, for the first caller too.

    It used to resolve to `undefined`: the first caller got the `.then` that
    cleared the in-flight slot, whose callback returned nothing, while a joiner
    got the raw promise and the real value. A loader answering `true` was read
    as a failure by the System page's Refresh, which then never showed its
    success toast.
    """
    base = (JS / "_parts/core/07-api.js").read_text(encoding="utf-8")
    start = base.index("\nfunction coalesce(")
    end = base.index("GP.coalesced = coalesced;", start)
    script = tmp_path / "coalesce.js"
    script.write_text(
        "const GP = {};\n"
        + base[start:end]
        + """
(async () => {
  let runs = 0;
  const load = async () => {
    runs += 1;
    await new Promise(r => setTimeout(r, 20));
    return 'answer' + runs;
  };
  const first = coalesced('k', load);
  const joined = coalesced('k', load);
  const [a, b] = await Promise.all([first, joined]);
  const failed = await coalesced('k', async () => { throw new Error('boom'); });
  const settled = _coalescedByKey.size;
  let release;
  const oldPage = coalesced('page', () => new Promise(resolve => { release = resolve; }));
  await Promise.resolve();
  const pending = _coalescedByKey.size;
  const newPage = coalesced('page', async () => 'new page');
  release('old page');
  const replacement = await Promise.all([oldPage, newPage]);
  await Promise.all(Array.from({length: 50}, (_, i) => coalesced('revision:' + i, async () => i)));
  console.log(JSON.stringify({ a, b, runs, failed, settled, pending, replacement,
    retained: _coalescedByKey.size }));
})();
""",
        encoding="utf-8",
    )
    out = subprocess.run(  # noqa: S603
        ["node", str(script)],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    result = json.loads(out.strip().splitlines()[-1])
    # The first caller sees the trailing re-run's answer (the newer one); the
    # joiner sees the same promise; a rejected loader reads as a plain false.
    assert result["runs"] == 2
    assert result["a"] == "answer2"
    assert result["b"] == "answer2"
    assert result["failed"] is False
    assert result["settled"] == 0
    assert result["pending"] == 1
    assert result["replacement"] == ["new page", "new page"]
    assert result["retained"] == 0

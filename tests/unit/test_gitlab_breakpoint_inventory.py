"""Breakpoint drift guard.

@gitlab/ui ships FOUR breakpoints (src/scss/variables.scss, and the same four
in tailwind.defaults.js `screens`):

    sm 576px   md 768px   lg 992px   xl 1200px

with `max-width` queries written one step below (Bootstrap's `.98` form). This
app uses 23 distinct values. Normalising the other 18 means moving real
layouts, which cannot be verified without rendering the pages, so they are
recorded here as debt rather than silently "fixed".

Worth noting what is absent: 992 and 1200 appear NOWHERE. The app reaches for
980/1000/1024 and 1180/1199/1439 instead, so its `lg` and `xl` tiers land near
GitLab's without ever landing on them.

What this test IS for: stopping the set from growing. A new hand-picked
breakpoint fails here, so the next one has to be a deliberate decision.
"""

import re
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"

# @gitlab/ui 136.3.0
GITLAB_BREAKPOINTS = {576, 768, 992, 1200}
# The `max-width` counterpart sits one step below the `min-width` value.
ON_SYSTEM = GITLAB_BREAKPOINTS | {bp - 1 for bp in GITLAB_BREAKPOINTS}

# Pre-existing values, measured 2026-08-21. Shrinking this set is the goal;
# adding to it is what the test exists to prevent.
LEGACY_OFF_SYSTEM = {
    360,
    480,
    600,
    601,
    640,
    641,
    680,
    769,
    900,
    980,
    1024,
    1180,
    1439,
    # _parts/responsive/: the wide-desktop tier in 30-misc.css above GitLab's xl.
    # (1800 was a third tier; it hardcoded max-width: 1600px, which ignored
    # --content-width-xl and made the layout-width preference look dead, so it
    # was folded into the 1440 tier. Its comment survives in 30-misc.css.)
    1440,
}

_QUERY = re.compile(r"\((?:max|min)-width:\s*([0-9.]+)px\)")


def _used() -> dict[int, set[str]]:
    """breakpoint -> the stylesheets that declare it (minified files ignored)."""
    found: dict[int, set[str]] = {}
    for path in sorted(CSS_DIR.rglob("*.css")):
        if ".min." in path.name:
            continue
        for raw in _QUERY.findall(path.read_text(encoding="utf-8")):
            found.setdefault(int(float(raw)), set()).add(str(path.relative_to(CSS_DIR)))
    return found


def test_no_new_off_system_breakpoint() -> None:
    used = _used()
    unexpected = {
        bp: sorted(files)
        for bp, files in used.items()
        if bp not in ON_SYSTEM and bp not in LEGACY_OFF_SYSTEM
    }
    assert not unexpected, (
        "new breakpoint(s) that are neither GitLab's nor recorded debt: "
        f"{unexpected}. GitLab's four are {sorted(GITLAB_BREAKPOINTS)} - reuse "
        "one, or add the value to LEGACY_OFF_SYSTEM with a reason."
    )


def test_the_scan_actually_reads_the_stylesheets() -> None:
    """Without this, a broken glob or regex makes every other test in the file
    pass by finding nothing at all. (The previous check here compared a set to
    its own superset and a length to its own maximum - both tautologies.)"""
    sheets = [p for p in CSS_DIR.rglob("*.css") if ".min." not in p.name]
    assert len(sheets) > 20, f"only {len(sheets)} stylesheets found"

    used = _used()
    assert len(used) > 15, f"only {len(used)} distinct breakpoints found"
    # _parts/ is where the responsive rules live; a glob that misses it would
    # hide most of the debt, which is exactly what a non-recursive one did.
    assert any("_parts" in sheet for sheets_for_bp in used.values() for sheet in sheets_for_bp), (
        "no _parts/ stylesheet was scanned - the glob stopped being recursive"
    )


def test_retired_legacy_breakpoints_are_removed_from_the_list() -> None:
    """Keeps the debt list honest: once a value is gone from the CSS it must
    come off the list, so the number always reflects reality."""
    used = set(_used())
    stale = sorted(LEGACY_OFF_SYSTEM - used)
    assert not stale, (
        f"these are no longer used and should be deleted from LEGACY_OFF_SYSTEM: {stale}"
    )

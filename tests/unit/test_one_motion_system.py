"""The app has ONE animation system, and nothing is left over from the old ones.

Motion used to be 67 hand-written `@keyframes` spread across 25 stylesheets,
each with its own duration, easing and lifecycle. The same interaction animated
differently depending on the page: a badge popped on one easing in
`animations.css` and another in `sidebar.css`; "remove this row" existed four
times (`.fade-out` + a 300 ms timer, `.card-dismissing` + a 300 ms timer,
`collapseAndRemove`, and a bare `.remove()`); "highlight what changed" existed
six times, and the class it toggled had been reduced to
`background-color: transparent`, so live updates showed nothing at all.

Everything with a lifecycle now goes through `GP.motion`
(`static/js/motion.js`). These tests fail if a second implementation
of any of it grows back, or if the old classes are resurrected.

What deliberately stays in CSS is asserted too, so a future pass does not
"finish the migration" by moving it and regressing:

* hover/focus colour interpolation - the target values live in the stylesheets,
  which is what a hover rule IS;
* continuous loops (spinners, pulses) - they run on the compositor
  thread, and a spinner is on screen exactly when the main thread is busy. Half
  of them are on `::after`, which no JS library can target at all.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src" / "app" / "templates"
CSS = TEMPLATES / "static" / "css"
JS = TEMPLATES / "static" / "js"

MOTION_MODULE = JS / "motion.js"


def _css_files() -> list[Path]:
    return [p for p in CSS.rglob("*.css") if ".min." not in p.name]


def _js_sources() -> list[Path]:
    """Hand-written JS only - never the generated bundles."""
    out: list[Path] = []
    for p in JS.rglob("*.js"):
        if ".min." in p.name or p.name.endswith("bundle.js"):
            continue
        if "vendor" in p.parts:
            continue
        out.append(p)
    return out


def _strip_comments(css: str) -> str:
    """A rule is code; the prose describing why it was removed is not.

    Every earlier version of this suite matched its own explanatory comments and
    passed (or failed) on them.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _strip_js_comments(js: str) -> str:
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"^\s*//.*$", "", js, flags=re.M)


# --------------------------------------------------------------------------
# Nothing left over
# --------------------------------------------------------------------------


def test_no_orphaned_keyframes() -> None:
    """Every @keyframes is referenced by something."""
    defined: dict[str, list[str]] = {}
    used: set[str] = set()

    skip = {
        "none",
        "infinite",
        "linear",
        "ease",
        "ease-in",
        "ease-out",
        "ease-in-out",
        "forwards",
        "backwards",
        "both",
        "alternate",
        "reverse",
        "paused",
        "running",
        "!important",
    }

    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        for match in re.finditer(r"@keyframes\s+([A-Za-z0-9_-]+)", body):
            defined.setdefault(match.group(1), []).append(path.name)
        for match in re.finditer(r"animation(?:-name)?\s*:\s*([^;}]+)", body):
            for token in re.split(r"[,\s]+", match.group(1)):
                token = token.strip()
                if token and not token.startswith(("var(", "0", ".")) and token not in skip:
                    used.add(token)

    # An animation can also be driven by name from JS (`getAnimations()`), but
    # the reference has to be the WHOLE token: a plain substring search reports
    # `bounce` as live because the word appears inside `debounce`, which is how
    # a genuinely dead keyframe survived the first sweep.
    from_js = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in _js_sources())

    orphans = {
        name: files
        for name, files in defined.items()
        if name not in used and not re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", from_js)
    }
    assert not orphans, f"@keyframes defined but never used: {orphans}"


def test_retired_animation_classes_are_gone() -> None:
    """The classes GP.motion replaced must not come back.

    Each of these was a second (or fourth) implementation of something the
    motion module now owns, and each needed its own remove / force-reflow /
    re-add dance plus an `animationend` listener at every call site.
    """
    retired = {
        "badge-updated": "GP.motion.pop",
        "value-updated": "removed - a changed value no longer flashes",
        "cell-flash": "removed - a changed value no longer flashes",
        "fade-out": "GP.collapseAndRemove",
        "card-dismissing": "GP.collapseAndRemove",
        "gp-banner-animating": "GP.motion.disclose",
        "toast-paused .toast-progress-bar": "GP.motion.toastPause",
        "gp-btn-success": "GP.motion.pop",
        "gp-btn-error": "GP.motion.shake",
        "just-toggled": "GP.motion.pop",
        "diff-block-flash": "GP.motion.highlight",
        "mr-card-target-flash": "GP.motion.highlight",
        "member-row-highlight": "GP.motion.highlight",
        "gp-fade-in": "GP.motion.panelIn",
        "gp-tour-popover--initial": "GP.motion.popIn",
        "cookie-banner-hiding": "GP.motion.edgeOut",
        "is-dismissing": "GP.motion.edgeOut",
        "is-shaking": "GP.motion.shake",
    }
    offenders: list[str] = []

    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        for name in retired:
            if f".{name}" in body:
                offenders.append(f"{path.name}: .{name}")

    for path in _js_sources():
        body = _strip_js_comments(path.read_text(encoding="utf-8"))
        for name, replacement in retired.items():
            if f"'{name}'" in body or f'"{name}"' in body:
                offenders.append(f"{path.name}: '{name}' -> use {replacement}")

    assert not offenders, "retired motion classes are back:\n  " + "\n  ".join(offenders)


def test_one_rotation_keyframe() -> None:
    """Four near-identical rotations existed at three different durations."""
    rotations: list[str] = []
    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        # Brace-aware: a keyframe body contains nested `{ ... }` steps, so a
        # `[^}]*` scan only ever saw single-step definitions - it matched the
        # pull-to-refresh `ptr-spin` and never THE `spin` keyframe (from/to),
        # which meant deleting the duplicate made this test fail instead of pass.
        for match in re.finditer(r"@keyframes\s+([A-Za-z0-9_-]+)\s*\{", body):
            depth, i = 1, match.end()
            while i < len(body) and depth:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                i += 1
            if "rotate(360deg)" in body[match.end() : i]:
                rotations.append(f"{path.name}:{match.group(1)}")
    assert len(rotations) == 1, f"expected one shared rotation keyframe, found {rotations}"


# --------------------------------------------------------------------------
# One owner per interaction
# --------------------------------------------------------------------------


def test_motion_module_is_the_only_animation_owner() -> None:
    """No page or component JS starts its own tween."""
    offenders = []
    for path in _js_sources():
        if path == MOTION_MODULE:
            continue
        body = _strip_js_comments(path.read_text(encoding="utf-8"))
        for call in re.finditer(r"\bgsap\s*\.\s*(to|from|fromTo|timeline|set)\b", body):
            offenders.append(f"{path.name}: gsap.{call.group(1)}()")
    assert not offenders, (
        "GSAP is called outside the motion module - add a named contract to "
        "motion.js instead:\n  " + "\n  ".join(offenders)
    )


def test_gsap_loads_before_the_app_bundle() -> None:
    """Deferred scripts run in document order.

    A bundle that loaded first would find `window.gsap` undefined and silently
    fall back to the no-motion shim - the app would work and animate nothing,
    which is the hardest kind of regression to notice.
    """
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    gsap_at = base.find("gsap-3.15.0.min.js")
    bundle_at = base.find("js/core.bundle.js'")
    assert gsap_at != -1, "GSAP is not loaded in base.html"
    assert bundle_at != -1, "core.bundle.js is not loaded in base.html"
    assert gsap_at < bundle_at, "GSAP must be loaded before core.bundle.js"


def test_gsap_is_vendored_not_a_cdn() -> None:
    """The CSP has no external script host, so a CDN tag would simply be blocked."""
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "static_url('vendor/gsap-3.15.0.min.js')" in base
    assert (TEMPLATES / "static" / "vendor" / "gsap-3.15.0.min.js").exists()


def test_motion_module_reads_its_timings_from_tokens() -> None:
    """Durations must come from tokens.css, never be hard-coded in JS.

    Otherwise the stylesheet and the motion module drift apart and the app is
    back to two clocks.
    """
    body = MOTION_MODULE.read_text(encoding="utf-8")
    assert "--motion-duration-fast" in body
    assert "--motion-duration-normal" in body
    assert "--motion-duration-slow" in body


def test_reduced_motion_is_honoured() -> None:
    body = MOTION_MODULE.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in body
    assert "REDUCED" in body


def test_no_gsap_fallback_still_completes_every_lifecycle() -> None:
    """If the library 404s, callbacks must still fire.

    A modal that will not close and a toast that never leaves are far worse than
    an app without animation, so the shim lands each call on its END state
    immediately rather than dropping it.
    """
    body = MOTION_MODULE.read_text(encoding="utf-8")
    assert "const G = gsap || " in body, "the module must degrade without GSAP"
    assert "onComplete" in body


# --------------------------------------------------------------------------
# What stays in CSS, and why
# --------------------------------------------------------------------------


def test_continuous_loops_stay_in_css() -> None:
    """Spinners must not be moved onto the main thread.

    A rAF-driven spinner stutters exactly when it matters - while the main
    thread is busy, which is the only time a spinner is shown.
    """
    loaders = _strip_comments((CSS / "loaders.css").read_text(encoding="utf-8"))
    assert "animation: spin" in loaders
    assert "infinite" in loaders

    module = _strip_js_comments(MOTION_MODULE.read_text(encoding="utf-8"))
    assert "repeat: -1" not in module, (
        "an infinite tween in the motion module would also hold its target "
        "alive across an SPA content swap"
    )


def test_no_bare_attribute_selector_sets_a_transition() -> None:
    """A selector like `[data-team-id]` matches far more than its author meant.

    That exact rule matched the action BUTTONS inside a group-activity row, and
    because the `transition` shorthand replaces rather than merges, those
    buttons lost the button contract: they eased at half the speed of every
    other button and animated nothing but their background. Attribute selectors
    that carry motion must be anchored to a tag or class.
    """
    offenders: list[str] = []
    pattern = re.compile(r"(^|[,{}])\s*(\[[a-zA-Z-]+[^\]]*\])\s*(?::[a-z-]+)?\s*\{([^}]*)\}", re.S)

    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        for match in pattern.finditer(body):
            if "transition" in match.group(3):
                offenders.append(f"{path.name}: {match.group(2)}")

    assert not offenders, "unanchored attribute selectors carrying a transition:\n  " + "\n  ".join(
        offenders
    )


def test_hover_interpolation_stays_in_css() -> None:
    """One baseline rule eases every interactive surface on the motion tokens -
    a control's 200ms out-cubic (GlButton's $gl-transition-duration-medium)."""
    body = _strip_comments((CSS / "animations.css").read_text(encoding="utf-8"))
    assert "transition-property" in body
    assert "transition-duration: var(--motion-duration-normal)" in body
    assert "var(--motion-ease-standard)" in body


def test_jump_to_highlight_has_one_implementation() -> None:
    """ "Here is the thing you asked for" was written five times.

    Three of them were `:target` rules, which fire only on the FIRST arrival -
    following the same anchor twice, or arriving through the SPA content swap
    (where the fragment never changes), highlighted nothing at all. The other
    two were classes with their own 1400 / 1600 / 2000 ms cleanup timers.
    """
    offenders: list[str] = []
    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        for match in re.finditer(r"([^{}]*:target[^{}]*)\{([^}]*)\}", body):
            if "animation" in match.group(2):
                offenders.append(f"{path.name}: {match.group(1).strip()[:50]}")
    joined = "\n  ".join(offenders)
    assert not offenders, (
        "`:target` cannot be re-triggered - use GP.motion.highlight, which the "
        f"hashchange listener drives:\n  {joined}"
    )


def test_colour_fades_keep_their_hue() -> None:
    """Fading to `rgba(0,0,0,0)` interpolates towards BLACK.

    A blue ring or a green wash turns muddy grey on the way out. Every colour
    tween has to end on its OWN transparent form.
    """
    body = _strip_js_comments(MOTION_MODULE.read_text(encoding="utf-8"))
    assert "_fadeTo(" in body
    assert "rgba(0,0,0,0)'," not in body, (
        "a colour tween ends on transparent black - use _fadeTo(colour)"
    )


def test_a_refresh_keeps_what_is_on_screen() -> None:
    """Refreshing must not tear down readable content.

    The System Health card's "Check now" was the one refresh in the app that
    never made anything move: it keeps the rendered dashboard, marks it busy,
    and swaps it at the same size. Tables now follow the same contract - rows
    that are already there dim rather than being replaced by a placeholder,
    because throwing away a correct table to announce that it is being replaced
    is the churn people kept reporting.
    """
    helpers = (JS / "_parts" / "core" / "22-content-states.js").read_text(encoding="utf-8")
    body = _strip_js_comments(helpers)
    fn = body.split("function tableLoading(", 1)[1].split("GP.tableLoading", 1)[0]

    assert "is-refreshing" in fn, "existing rows are marked busy, not replaced"
    assert "aria-busy" in fn
    # The early return is what keeps the rows: reaching the innerHTML below it
    # would wipe them.
    assert fn.index("is-refreshing") < fn.index("innerHTML")
    assert "gl-table-" not in fn, "placeholder rows must stay gone"

    css = _strip_comments((CSS / "loaders.css").read_text(encoding="utf-8"))
    assert re.search(r"\.is-refreshing\s*\{[^}]*opacity: 0\.6", css)


def test_selectors_do_not_start_with_a_pseudo_class() -> None:
    """A selector beginning with a pseudo-class is dropped by the minifier.

    `:not(.d-none) + x` was written in tables.css and never reached the bundle:
    the rule read correctly in the source and did nothing in the browser. Anchor
    with an element or `*` so what ships is what was written.
    """
    offenders: list[str] = []
    for path in _css_files():
        body = _strip_comments(path.read_text(encoding="utf-8"))
        for block in re.finditer(r"(?:^|\})([^{}@]+)\{", body):
            for sel in block.group(1).split(","):
                sel = sel.strip()
                if sel.startswith(":") and not sel.startswith(("::", ":root", ":where", ":is")):
                    offenders.append(f"{path.name}: {sel[:60]}")
    joined = "\n  ".join(sorted(set(offenders))[:10])
    assert not offenders, (
        f"these are silently dropped when minified - anchor them with `*`:\n  {joined}"
    )

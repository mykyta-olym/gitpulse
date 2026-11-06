"""A disclosure slides open from nothing; it never flashes its full height first.

`<details>` is native, so the browser lays the panel out the instant `open`
flips. The handler used to let it do that and then measure a frame later, which
painted the panel at full size before GSAP collapsed it to zero to start the
slide. Measured in Chromium on the settings page's "Edit JSON Configuration":

    before   265, 0, 23, 72, 102, 144, ...
    after      0, 23, 38, 84, 129, 168, ...

One frame at 265px, then a snap to zero, then the slide - which is the jerk.
Two changes remove it: the handler opens the element itself in the same tick as
the collapse, and `disclose` measures the target and sets the collapsed box
explicitly instead of relying on `from()`, whose first render can land a frame
late.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOTION = REPO / "src/app/templates/static/js/motion.js"


def _handler() -> str:
    src = MOTION.read_text(encoding="utf-8")
    start = src.index("const details = summary.parentElement;")
    return src[start : src.index("\n  }\n", start)]


def test_the_handler_opens_the_details_itself() -> None:
    body = _handler()
    assert "details.open = true" in body, (
        "the browser is opening it again, which paints the expanded panel "
        "before the collapse can land"
    )
    assert "requestAnimationFrame" not in body, (
        "waiting a frame to start the slide is exactly what put a full-height frame on screen"
    )


def test_the_open_path_sets_the_collapsed_box_before_animating() -> None:
    src = MOTION.read_text(encoding="utf-8")
    body = src.split("function disclose(", 1)[1].split("\n  }", 1)[0]
    open_branch = body.split("if (open) {", 1)[1].split("} else {", 1)[0]
    assert "G.set(panel, BOX)" in open_branch, (
        "the collapsed state is no longer applied explicitly, so the first "
        "painted frame can be the expanded one again"
    )
    assert "getBoundingClientRect().height" in open_branch, (
        "the target height is no longer measured, so the slide has nothing to grow towards"
    )


def test_the_close_path_is_unchanged_in_shape() -> None:
    """Closing never had the problem - the panel is already laid out."""
    src = MOTION.read_text(encoding="utf-8")
    body = src.split("function disclose(", 1)[1].split("\n  }", 1)[0]
    assert "} else {" in body

"""A teleported modal must take its flatpickr calendar with it.

Reproduced in a browser by navigating the sidebar in laps: after three laps the
page held three copies of four ids (`courseSemesterStart-fp-0` and friends) and
DevTools reported duplicate form field ids. flatpickr appends its calendar to
<body>, BESIDE the modal rather than inside it, so removing the modal orphaned
the calendar and every navigation minted another set.
"""

from __future__ import annotations

from pathlib import Path

HELPERS = Path(__file__).resolve().parents[2] / "src/app/templates/static/js/_parts/core/36-boot.js"


def _drop_page_modals() -> str:
    src = HELPERS.read_text(encoding="utf-8")
    body = src.split("function _dropPageModals() {", 1)[1]
    return body[: body.index("\nGP.dropPageModals")]


def test_dropping_a_modal_destroys_its_flatpickr_instances() -> None:
    """`.remove()` alone leaks the calendar: destroy() is what takes it down."""
    body = _drop_page_modals()
    assert "_flatpickr.destroy()" in body
    destroy_at = body.index("_flatpickr.destroy()")
    remove_at = body.index("m.remove()")
    assert destroy_at < remove_at, "destroy must run while the input is still in the modal"


def test_card_blocks_are_separated_by_flex_gap_not_a_margin() -> None:
    """A `display: none` child takes no flex gap - a margin would leave dead space.

    The margin version left 8px under the header of every COLLAPSED card, because
    the body is hidden but still present, so the header was never `:last-child`.
    """
    css = (
        Path(__file__).resolve().parents[2] / "src/app/templates/static/css/cards.css"
    ).read_text(encoding="utf-8")
    block = css.split(".card {", 1)[1]
    block = block[: block.index("}")]
    assert "display: flex" in block
    assert "gap: var(--gl-spacing-2)" in block  # 4px = GitLab gl-p-2 on Pajamas scale
    assert "margin-bottom: var(--gl-spacing-2)" not in css.split(".card-footer", 1)[0], (
        "the header must not carry a margin; hidden bodies would reserve space for it"
    )

"""A table that fills itself after first paint holds its own height first.

`data_table(reserve_rows=N)` writes a min-height so rows land in space that was
already theirs. The arithmetic behind it was a flat 37px per row over a flat
40px head - and NO table in the app draws either. Measured in a browser: a
normal row is 57px over a 55px head, a compact row 40px over a 39px head. So
the Event Pipeline reserved 151px for rows that came to 226px and grew 75px
anyway, which is the jump the parameter exists to prevent.

The reservation has to be RIGHT rather than generous, which is the part that is
easy to get wrong: ClientPaginator locks the wrapper at whatever height it
finds and releases the lock a frame later, so an over-reservation collapses to
the content and drags the page UP - the same jump, in the other direction.
"""

from __future__ import annotations

from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"
_TABLES = _TEMPLATES / "components/tables.html"
_NAVBAR_CSS = _TEMPLATES / "static/css/navbar.css"


def test_the_reservation_asks_what_kind_of_row_it_is() -> None:
    macro = _TABLES.read_text(encoding="utf-8")
    assert "_row_px = reserve_row_px or (40 if compact else 57)" in macro, (
        "the per-row height is a flat guess again"
    )
    assert "_head_px = 39 if compact else 55" in macro
    assert "reserve_rows * _row_px + _head_px" in macro
    assert "reserve_rows * reserve_row_px + 40" not in macro


def test_server_rendered_checks_do_not_reserve_a_second_copy_of_their_height() -> None:
    checks = (_TEMPLATES / "partials/course_settings/_compliance_settings.html").read_text(
        encoding="utf-8"
    )
    assert 'include "partials/course_settings/_check_rows.html"' in checks
    assert "reserve_row_px=" not in checks
    assert "reserve_rows=" not in checks


def test_the_pagination_bar_is_born_the_height_it_ends_up() -> None:
    """It is born empty and becomes a bar with a 32px per-page control; the
    min-height keeps the footer where it is on every paginated page."""
    css = _NAVBAR_CSS.read_text(encoding="utf-8")
    block = css.split(".pagination-controls {", 1)[1].split("}", 1)[0]
    assert "min-height:" in block, (
        "the bar grows when the paginator draws it, taking the footer with it"
    )
    assert "32px" in block, "the reserved height no longer names the control it reserves for"


def test_the_health_card_is_server_rendered_without_a_placeholder_loader() -> None:
    system = (_TEMPLATES / "admin_system.html").read_text(encoding="utf-8")
    health = (_TEMPLATES / "partials/admin/_system_health.html").read_text(encoding="utf-8")
    assert "include 'partials/admin/_system_health.html'" in system
    assert "healthCheckLoading" not in system
    assert "block_loading" not in system
    assert "reserve_rows=" not in health


def test_the_clock_reserves_its_line_as_well_as_its_width() -> None:
    """The last thing on the page that still moved.

    `#topBarClockText` is written by JS after first paint. Its width was already
    reserved; empty, its box is still 0 high, so the `.gl-context-item` around it
    is only as tall as the clock icon and the whole item shifts ~4px the moment
    the text lands - on every page that draws a top bar.
    """
    css = (
        Path(__file__).resolve().parents[2] / "src/app/templates/static/css/topbar.css"
    ).read_text(encoding="utf-8")
    block = css.split("#topBarClockText {", 1)[1].split("}", 1)[0]
    assert "min-width" in block, "the clock's width reservation went"
    assert "min-height" in block, (
        "the clock reserves its width but not its line, so the top bar still "
        "settles when the time arrives"
    )

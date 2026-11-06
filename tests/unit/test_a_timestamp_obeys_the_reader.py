"""Preferences offers two settings about time. They reached one page.

"Time format" (12h/24h) and "Use relative times" are applied by
`static/js/localize-time.js`, to `time[data-localize-time]` and to nothing
else. Every other timestamp in the app was printed with `strftime` in a
template or `new Date(x).toLocaleString()` in page JS, so it ignored both
choices - the settings saved, came back, and changed nothing the reader could
see. One template in the whole app emitted the element they act on.

These are the source-level halves of that fix; the behaviour itself is measured
in the browser (the settings scenario). Together they say: there is ONE way to
print a moment, and the call sites use it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

import pytest

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO / "src/app/templates"
_JS = _TEMPLATES / "static/js"
_MACRO = _TEMPLATES / "components/time.html"
_LOCALIZER = _JS / "localize-time.js"
_HELPERS = _JS / "_parts/core/22-content-states.js"


def _code(path: Path) -> str:
    """The file with its comments removed - a scan must not read prose."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"^\s*//.*$", "", text, flags=re.M)


class TestThereIsOneWayToPrintAMoment:
    def test_the_macro_emits_the_element_the_localiser_looks_for(self) -> None:
        macro = _MACRO.read_text(encoding="utf-8")
        assert "data-localize-time" in macro
        assert "querySelectorAll('time[data-localize-time]')" in _LOCALIZER.read_text(
            encoding="utf-8"
        ), "the localiser stopped looking for the element the macro emits"

    def test_the_js_mirror_emits_the_same_element(self) -> None:
        """`GP.timeHtml` is to the macro what `GP.badgeHtml` is to `badge`."""
        helpers = _HELPERS.read_text(encoding="utf-8")
        assert "function timeHtml(iso, format, fallback)" in helpers
        assert "GP.timeHtml = timeHtml" in helpers
        assert "data-localize-time" in helpers

    def test_a_date_only_stamp_does_not_grow_a_clock(self) -> None:
        """The macro's `date_only` and the localiser's 'date' must agree, or a
        column of dates gains a 00:00 the moment the client takes over."""
        assert "date_only" in _MACRO.read_text(encoding="utf-8")
        assert "mode === 'date'" in _LOCALIZER.read_text(encoding="utf-8")

    def test_markup_built_by_page_js_is_localised_too(self) -> None:
        """There is no third path to remember.

        The localiser ran on DOMContentLoaded and on htmx swaps only, so a row
        built from fetched JSON was never converted unless its author remembered
        to ask. None of them did - they called `toLocaleString()` instead.
        """
        assert "MutationObserver" in _LOCALIZER.read_text(encoding="utf-8"), (
            "nothing watches for a <time> inserted by page JS, so GP.timeHtml is "
            "unsafe to use outside a template"
        )


class TestTheCallSitesUseIt:
    """A hand-rolled stamp is a setting that quietly stops working."""

    def test_no_template_formats_a_date_by_hand(self) -> None:
        offenders = []
        for path in _TEMPLATES.rglob("*.html"):
            if path == _MACRO:
                continue
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                # Machine-readable sorting keys do not format visible text.
                line = re.sub(r'\sdata-sort-value="[^"]*"', "", line)
                if "strftime" in line and "data-localize-time" not in line:
                    offenders.append(f"{path.relative_to(_TEMPLATES)}: {line.strip()[:80]}")
        assert not offenders, (
            "these print a date the reader's time settings cannot reach; "
            "use `localized_time` from components/time.html:\n  " + "\n  ".join(offenders)
        )

    # Two places may still format for themselves, and only these two:
    #   localize-time.js IS the formatter, and inside it `toLocaleString` is how
    #     the short month name is spelled in the reader's language;
    #   greeting-sync.js prints a long-form calendar date ("7. septembra") and
    #     no clock at all, so neither time setting has anything to act on.
    _MAY_FORMAT_THEMSELVES: ClassVar[set[str]] = {
        "localize-time.js",
        "greeting-sync.js",
    }

    @staticmethod
    def _scripts() -> list[Path]:
        """Every script a person WRITES.

        `pages/*.js` was missing from this list, which is most of the app's page
        code - and `pages/admin-events.js` was formatting its Received column
        with `toLocaleString()` the whole time this test was passing. A file
        under `pages/` is generated only when a `_parts/<name>/` directory
        builds it; the rest are written by hand and belong here.
        """
        parts = _JS / "_parts"
        generated = {d.name for d in parts.iterdir() if d.is_dir()}
        written = list(_JS.glob("*.js")) + list(parts.rglob("*.js"))
        written += [p for p in (_JS / "pages").glob("*.js") if p.stem not in generated]
        return written

    def test_no_page_script_formats_a_date_by_hand(self) -> None:
        offenders = []
        for path in self._scripts():
            if ".min." in path.name or "bundle" in path.name:
                continue
            if path.name in self._MAY_FORMAT_THEMSELVES:
                continue
            for i, line in enumerate(_code(path).splitlines(), 1):
                if re.search(r"\.toLocale(String|DateString|TimeString)\(", line):
                    offenders.append(f"{path.name}:{i}: {line.strip()[:80]}")
        assert not offenders, (
            "these format a moment themselves, so Time format and Use relative "
            "times do not apply to them; use `GP.timeHtml`:\n  " + "\n  ".join(offenders)
        )


def test_the_top_bar_clock_obeys_the_time_format() -> None:
    """It is on every page, so getting it wrong was the most visible hardcode.

    A live clock cannot be a `<time data-localize-time>` element - that is for a
    fixed instant - so it asks the same formatter those elements use. Built with
    `getHours()`, it showed 18:12 in the top bar of every page while the same
    moment in a table read 6:12 PM.
    """
    clock = _code(_JS / "header-clock.js")
    assert "window.formatClock" in clock, (
        "the top-bar clock no longer asks the shared formatter, so Time format does not reach it"
    )
    assert "window.formatClock = fmtClock" in _LOCALIZER.read_text(encoding="utf-8"), (
        "the shared clock formatter is not exported any more"
    )


@pytest.mark.parametrize(
    ("setting", "attribute"),
    [("time_format", "data-time-format"), ("use_relative_times", "data-absolute-times")],
)
def test_the_setting_is_carried_to_the_page(setting: str, attribute: str) -> None:
    """Server-side, on <html>, so the first paint already honours it."""
    base = (_TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert setting in base, f"base.html no longer carries {setting}"
    assert attribute in base, f"base.html no longer sets {attribute}"
    assert attribute in _LOCALIZER.read_text(encoding="utf-8"), (
        f"nothing reads {attribute}, so choosing it changes nothing"
    )

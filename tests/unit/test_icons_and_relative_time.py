"""Two things a reader recognised before any test did.

The close control carried the X (formerly Twitter) brand glyph. Eleven places
use that icon and every one of them means "close", "dismiss" or "remove", so a
social-media mark there reads as a link to a social network.

And the relative time was assembled by concatenation - `n + 's ' + t('ago')` -
which puts the translated word last. Slovak puts it FIRST, so a banner read
"11s pred": the number was right and the sentence was not.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_ICONS_JS = _REPO / "src/app/templates/static/js/icons.js"
_ICONS_HTML = _REPO / "src/app/templates/components/icons.html"
_SK = _REPO / "src/app/i18n/catalogs/sk.json"

# A fragment of the X/Twitter brand path. It is distinctive enough that its
# presence anywhere in the icon set means the mark came back.
_BRAND_GLYPH = "9.294 6.928"

_AGO_FORMATTERS = (_REPO / "src/app/templates/static/js/health-monitor.js",)

# Admin health uses GP.timeHtml; job rows use the server's local_time helper.
# Both emit the same localizable time component.
_DELEGATES_TO_THE_SHARED_TIME = (
    _REPO / "src/app/templates/static/js/_parts/admin-system/00-format-render.js",
    _REPO / "src/app/templates/static/js/_parts/admin-system/20-jobs.js",
)


@pytest.mark.parametrize("path", [_ICONS_JS, _ICONS_HTML])
def test_the_close_icon_is_not_a_brand_mark(path: Path) -> None:
    assert _BRAND_GLYPH not in path.read_text(encoding="utf-8"), (
        f"{path.name} draws the X brand glyph for a close control - every one of "
        "its callers means dismiss, remove or close"
    )


def test_both_icon_registries_draw_the_same_close_icon() -> None:
    """The set is defined twice, once for JavaScript and once for Jinja."""
    js = re.search(r"'x': \{ vb: '([^']+)', d: '(.*?)' \}", _ICONS_JS.read_text(encoding="utf-8"))
    assert js, "the 'x' icon is gone from icons.js"
    assert js.group(2) in _ICONS_HTML.read_text(encoding="utf-8"), (
        "icons.html draws a different 'x' than icons.js"
    )


@pytest.mark.parametrize("path", _AGO_FORMATTERS)
def test_relative_time_is_one_translatable_phrase(path: Path) -> None:
    """Not a number glued to a translated word - the order is the locale's."""
    text = path.read_text(encoding="utf-8")
    # Strip comments first: the fix is documented by quoting the broken form,
    # and a scan that reads its own explanation reports the defect it prevents.
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    code = re.sub(r"^\s*//.*$", "", code, flags=re.M)
    offenders = re.findall(r"\+\s*'[smhd] '\s*\+\s*t\('ago'\)", code)
    assert not offenders, f"{path.name} still concatenates the age: {offenders}"
    assert "'{n}s ago'" in text, f"{path.name} does not use the placeholder phrase"


@pytest.mark.parametrize("path", _DELEGATES_TO_THE_SHARED_TIME)
def test_admin_system_does_not_grow_its_own_clock_again(path: Path) -> None:
    """One mechanism owns "when": `<time data-localize-time>`.

    Preferences offers "Time format" and "Use relative times", and
    localize-time.js applies them to that element and to nothing else. A stamp
    written any other way ignores both, which is why those settings read as
    decorative.
    """
    code = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    code = re.sub(r"^\s*//.*$", "", code, flags=re.M)
    for call in ("toLocaleString(", "toLocaleDateString("):
        assert call not in code, (
            f"{path.name} formats a date itself again ({call}), so the reader's "
            "time settings do not reach it"
        )
    assert "function fmtAgo" not in code, (
        f"{path.name} grew a private relative-time formatter again; "
        "GP.timeHtml(iso, 'relative') is the one that obeys the preference"
    )


def test_the_catalogue_translates_every_age_shape() -> None:
    catalog = json.loads(_SK.read_text(encoding="utf-8"))
    for key in ("{n}s ago", "{n}m ago", "{n}h ago", "{n}d ago"):
        assert key in catalog, f"Slovak has no translation for {key!r}"
        assert "{n}" in catalog[key], f"the Slovak for {key!r} drops the number"
        assert catalog[key].startswith("pred "), (
            f"the Slovak for {key!r} should lead with 'pred' - that is the whole point"
        )

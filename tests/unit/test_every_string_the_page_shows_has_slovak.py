"""A string the app renders through t() has a Slovak translation, or it is
English on a Slovak page.

`scripts/find_missing_translations.py` reads templates and JavaScript. It never
reads Python - and the Configuration table renders `flag.description` for every
feature flag, which is a `description=` on a Pydantic field in `config.py`. So
three of them sat in English on the Slovak Configuration table and no scan,
gate or test had ever looked at them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import get_settings

_CATALOGS = Path(__file__).resolve().parents[2] / "src/app/i18n/catalogs"


@pytest.fixture(scope="module")
def slovak() -> dict[str, str]:
    return json.loads((_CATALOGS / "sk.json").read_text(encoding="utf-8"))


def _flag_descriptions() -> list[tuple[str, str]]:
    settings = get_settings()
    fields = type(settings).model_fields
    out = []
    for name in sorted(dir(settings)):
        if not name.startswith("feature_"):
            continue
        info = fields.get(name)
        text = (info.description if info else "") or ""
        if text:
            out.append((name, text))
    return out


def test_the_scan_finds_the_flags() -> None:
    assert len(_flag_descriptions()) >= 5, "no feature flags found - the scan is broken"


def test_every_feature_flag_description_is_translated(slovak: dict[str, str]) -> None:
    missing = [name for name, text in _flag_descriptions() if text not in slovak]
    assert not missing, (
        "these render in English on the Slovak Configuration table:\n  " + "\n  ".join(missing)
    )


def test_no_script_translates_a_string_with_line_breaks_inside(slovak: dict[str, str]) -> None:
    """``t('First.\n\nSecond?')`` is one catalogue key with the breaks in it.

    Nobody writes that key, so the whole paragraph stayed English - the
    semester-window warning and the "run a full sync?" prompt on the course
    settings page both did, and `find_missing_translations.py` did not see
    them. Translate each sentence and join them with the breaks outside t().
    """
    import re

    js_root = Path(__file__).resolve().parents[2] / "src/app/templates/static/js"
    call = re.compile(r"""\b(?:GP\.)?t\(\s*'((?:[^'\\]|\\.)*)'\s*\)""")
    offenders = []
    for path in js_root.rglob("*.js"):
        name = path.name
        if ".min." in name or "bundle" in name or "i18n-catalog" in name:
            continue
        if path.parent.name == "pages":
            continue
        for match in call.finditer(path.read_text(encoding="utf-8")):
            raw = match.group(1)
            if "\\n" not in raw:
                continue
            key = raw.replace("\\n", "\n").replace("\\'", "'")
            if key not in slovak:
                offenders.append(f"{name}: {raw[:70]}")
    assert not offenders, offenders

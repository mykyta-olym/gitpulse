"""The client translation catalogue ships as a file, not inside every page.

Inlined as a JSON island it was 205KB raw - about ninety per cent of what a
compressed page weighed - and it has no URL, so the browser had to take it
again on every full load even though it is byte-identical for every reader on
a locale and changes only when the translations do.

Two things have to stay true for that to keep working, and neither is visible
from reading a template: the generated file must contain exactly what the
server would have inlined, and every page that carries the config island must
also load the file - otherwise the island says "translate into Slovak" and
nothing has the Slovak.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.i18n import SOURCE_LOCALE, get_catalog
from tests.build_outputs import DIST, served

_REPO = Path(__file__).resolve().parents[2]
_CATALOGS = _REPO / "src" / "app" / "i18n" / "catalogs"


def _built(locale: str) -> dict[str, str]:
    text = served(f"js/i18n-catalog-{locale}.js").read_text(encoding="utf-8")
    payload = text.split("window.__GP_I18N_CATALOG__=", 1)[1].rsplit(";", 1)[0]
    parsed: dict[str, str] = json.loads(payload)
    return parsed


def _shipped_locales() -> list[str]:
    return sorted(
        p.stem for p in _CATALOGS.glob("*.json") if p.stem != SOURCE_LOCALE and p.stat().st_size > 2
    )


@pytest.mark.parametrize("locale", _shipped_locales())
def test_the_built_file_is_what_the_server_would_have_inlined(locale: str) -> None:
    """The build script re-implements `_canonical_text` because it runs in CI
    with no application environment. This is what stops the two drifting."""
    assert _built(locale) == get_catalog(locale), (
        f"the generated catalogue for {locale} differs from get_catalog() - "
        "run: python scripts/build_bundle.py"
    )


def test_the_source_locale_ships_no_file() -> None:
    """Phrases are authored in it, so there is nothing to translate into."""
    manifest = json.loads((DIST / "manifest.json").read_text(encoding="utf-8"))
    assert f"js/i18n-catalog-{SOURCE_LOCALE}.js" not in manifest


def test_the_island_no_longer_carries_the_catalogue() -> None:
    from app.i18n import _catalog_url

    assert (
        _catalog_url(
            "sk",
        )
        is not None
    ), "the sk catalogue has no URL to load"
    assert _catalog_url(SOURCE_LOCALE) is None, "the source locale should have no file"


_ISLAND = 'id="gp-i18n-config"'
_ISLAND_MACRO = "json_island(i18n_client_config"


def test_every_page_with_the_island_also_loads_the_catalogue() -> None:
    """The island alone is a locale with no words behind it."""
    templates = _REPO / "src" / "app" / "templates"
    offenders: list[str] = []
    for path in templates.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if _ISLAND not in text and _ISLAND_MACRO not in text:
            continue
        if "i18n_catalog_url" not in text:
            offenders.append(str(path.relative_to(_REPO)))
    assert not offenders, (
        "these pages carry the i18n config island but never load the catalogue "
        f"file, so JavaScript would render untranslated: {offenders}"
    )

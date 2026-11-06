"""The docs site states its default language in four places. They must agree.

Hugo's `defaultContentLanguage` decides which language owns the un-prefixed
URLs. Three other things have to know the same answer and none of them can read
Hugo's config:

  - `site.Params.defaultLang`, which the layouts ask instead of naming a language
  - `langDefault` in the Go metadata generator, which decides whose paths go
    unprefixed into `data/<lang>/page-metadata.json`
  - `defaultLocale` in `locales/index.js`, which the Vue sidebar and the client
    breadcrumb use to decide whether to add a prefix

When they disagreed - the engine shipped with all three saying "en-us" against a
Slovak default - the sidebar linked through a redirect on every click and the
English breadcrumb produced `/docs/en/en/...`, which 404s. Nothing failed at
build time; the links were simply wrong.
"""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs-site"
HUGO_CONFIG = DOCS / "config/_default/hugo.yaml"


def _hugo_default_language() -> str:
    text = HUGO_CONFIG.read_text(encoding="utf-8")
    m = re.search(r"^defaultContentLanguage:\s*(\S+)\s*$", text, re.M)
    assert m, "hugo.yaml has no defaultContentLanguage"
    return m.group(1).strip("\"'")


def test_hugo_param_matches_default_content_language() -> None:
    text = HUGO_CONFIG.read_text(encoding="utf-8")
    m = re.search(r"^\s+defaultLang:\s*(\S+)\s*$", text, re.M)
    assert m, "hugo.yaml params has no defaultLang"
    assert m.group(1).strip("\"'") == _hugo_default_language()


def test_go_metadata_generator_matches() -> None:
    go = (DOCS / "cmd/internal/build/build_page_metadata.go").read_text(encoding="utf-8")
    m = re.search(r'const langDefault = "([^"]+)"', go)
    assert m, "build_page_metadata.go has no langDefault"
    assert m.group(1) == _hugo_default_language()


def test_js_default_locale_matches() -> None:
    js = (DOCS / "locales/index.js").read_text(encoding="utf-8")
    m = re.search(r'export const defaultLocale = "([^"]+)"', js)
    assert m, "locales/index.js has no defaultLocale"
    assert m.group(1) == _hugo_default_language()


def test_every_published_language_has_a_message_catalogue_and_navigation() -> None:
    """A language Hugo publishes but `languages` omits silently loads another
    language's navigation tree and another language's labels."""
    text = HUGO_CONFIG.read_text(encoding="utf-8")
    block = re.search(r"^languages:\n((?:  \S.*\n|    .*\n|\n)*)", text, re.M)
    assert block, "hugo.yaml has no languages block"
    published = re.findall(r"^  ([\w-]+):\s*$", block.group(1), re.M)
    assert published, "no languages parsed out of hugo.yaml"

    js = (DOCS / "locales/index.js").read_text(encoding="utf-8")
    listed = set(re.findall(r"^  ([\w-]+),\s*$", js, re.M))
    assert set(published) == listed, (
        f"hugo publishes {sorted(published)} but locales/index.js lists {sorted(listed)}"
    )

    for lang in published:
        assert (DOCS / f"locales/{lang}.json").exists(), f"no locales/{lang}.json"
        assert (DOCS / f"data/{lang}/navigation.yaml").exists(), f"no data/{lang}/navigation.yaml"


def test_no_layout_names_a_default_language() -> None:
    """Layouts ask `site.Params.defaultLang`; a hardcoded code is the bug this
    file exists to catch, and it reappears whenever the upstream engine is
    re-pulled."""
    offenders = []
    for path in (DOCS / "themes/gitlab-docs/layouts").rglob("*.html"):
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith(("{{/*", "<!--", "*/}}")) or stripped.startswith("*"):
                continue
            if re.search(r'(eq|ne)\s+\$?\.?\w[\w.$]*\s+"(en-us|ja-jp)"', line):
                offenders.append(f"{path.name}:{i}")
    assert not offenders, f"layouts naming a language: {offenders}"

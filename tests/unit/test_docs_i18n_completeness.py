"""Every i18n key the docs reference must exist, in both languages.

The footer rendered blank labels - an empty logo ``alt``, no tagline, raw link
text - because it referenced keys (``footer.logoAlt``, ``footer.tagline``, the
link identifiers) that were never added to ``i18n/*.yaml``. Hugo's ``T`` returns
an empty string for a missing key, so nothing failed at build time; the labels
were simply gone.

This asks the question directly: gather every key a template renders - the
literal ``T "x"`` calls AND the ``identifier:`` values the menus render through
a variable - and assert each language file defines all of them. It also asserts
the two languages define the same keys, so one cannot drift ahead of the other.
"""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs-site"
LAYOUTS = DOCS / "themes/gitlab-docs/layouts"
HUGO_CONFIG = DOCS / "config/_default/hugo.yaml"
LANGS = ("sk", "en")

# A key may be quoted: `yes` and `no` are YAML booleans, so the yes/no
# shortcode's keys are written `"yes":` / `"no":`.
_KEY_RE = re.compile(r'^(\s*)"?([\w.-]+)"?:\s*(.*)$')


def _referenced_keys() -> set[str]:
    """Keys the site renders: literal ``T "x"`` in any layout, plus every
    ``identifier:`` value in the config (rendered via ``{{ T .identifier }}``)."""
    keys: set[str] = set()
    for path in LAYOUTS.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            keys.update(m.group(1) for m in re.finditer(r'T\s+"([^"]+)"', text))
    config = HUGO_CONFIG.read_text(encoding="utf-8")
    keys.update(m.group(1) for m in re.finditer(r"identifier:\s*([A-Za-z][\w.-]*)", config))

    # Keys built at render time from `printf "prefix.%sSuffix" $x` where $x
    # iterates a `slice "a" "b"` - the footer's `footer.docsTitle` /
    # `footer.legalTitle` headings. Neither a literal T "..." nor an identifier,
    # so they were invisible here until the legal column shipped with no heading.
    for path in LAYOUTS.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pm in re.finditer(r'printf\s+"([\w.]*)%s([\w.]*)"\s+\$\w+', text):
            prefix, suffix = pm.group(1), pm.group(2)
            # find a slice on the same line providing the iterated values
            line = text[text.rfind("\n", 0, pm.start()) + 1 : text.find("\n", pm.end())]
            for sm in re.finditer(r'slice\s+((?:"[^"]+"\s*)+)', line):
                for val in re.findall(r'"([^"]+)"', sm.group(1)):
                    keys.add(f"{prefix}{val}{suffix}")
    return keys


def _defined_keys(lang: str) -> set[str]:
    text = (DOCS / f"i18n/{lang}.yaml").read_text(encoding="utf-8")
    keys: set[str] = set()
    ns = ""
    for line in text.split("\n"):
        m = _KEY_RE.match(line)
        if not m:
            continue
        indent, key, value = m.groups()
        if not value.strip():
            ns = key
            continue
        keys.add(f"{ns}.{key}" if indent else key)
    return keys


def test_every_referenced_key_is_defined_in_both_languages() -> None:
    referenced = _referenced_keys()
    for lang in LANGS:
        missing = sorted(referenced - _defined_keys(lang))
        assert not missing, (
            f"i18n/{lang}.yaml is missing keys the layouts/config reference "
            f"(they render as empty strings): {missing}"
        )


def test_the_two_languages_define_the_same_keys() -> None:
    sk, en = _defined_keys("sk"), _defined_keys("en")
    assert not (sk - en), f"only in sk.yaml: {sorted(sk - en)}"
    assert not (en - sk), f"only in en.yaml: {sorted(en - sk)}"


def test_no_key_is_left_as_english_placeholder_in_slovak() -> None:
    """A Slovak value identical to the English one is an untranslated leftover.
    A short allowlist covers strings that are the same in both languages on
    purpose (proper nouns, "API")."""
    same_on_purpose = {"footer.linkApi", "landing-search.findGLAnswers"}

    def flat(lang: str) -> dict[str, str]:
        text = (DOCS / f"i18n/{lang}.yaml").read_text(encoding="utf-8")
        out: dict[str, str] = {}
        ns = ""
        for line in text.split("\n"):
            m = _KEY_RE.match(line)
            if not m:
                continue
            indent, key, value = m.groups()
            if not value.strip():
                ns = key
                continue
            out[f"{ns}.{key}" if indent else key] = value.strip().strip('"')
        return out

    sk, en = flat("sk"), flat("en")
    leftover = sorted(
        k
        for k, v in sk.items()
        if k in en and v == en[k] and len(v) > 3 and k not in same_on_purpose
    )
    assert not leftover, f"Slovak still equals English for: {leftover}"

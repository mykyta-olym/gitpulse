"""A setting the reader can choose has to change what the reader sees.

Two of them did not, and both failed silently - the value saved, came back on
the next request, and changed nothing.

**The highlight scheme could not reach a diff.** Preferences offers seven
schemes, and the palette they set was scoped to `.gl-desc-pre.highlight`:
markdown code fences. The diff cell rendered its line as plain text, so there
were no tokens for any palette to colour. Choosing Monokai on the page where a
reader actually looks at code did nothing at all.

**The diff colours were overridden by a copy of their own rule.** `.diff-add`
and `.diff-del` read the reader's colours in utilities.css, and a second
declaration in student.css set them to the stock green and red. Same
specificity, later in the cascade, so the copy won - on the student page,
which is the only page with diffs on it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.dashboard.students.diffs import _highlight_diff_line

_REPO = Path(__file__).resolve().parents[2]
_CSS = _REPO / "src" / "app" / "templates" / "static" / "css"


class TestADiffLineCarriesTokens:
    """Without tokens in the markup, no palette can change anything."""

    def test_a_known_language_is_tokenised(self) -> None:
        marked = _highlight_diff_line("    def compute(self, x):", "app/thing.py")
        assert marked is not None
        assert 'class="k"' in marked, f"no keyword token in {marked!r}"
        assert 'class="nf"' in marked, f"no function-name token in {marked!r}"

    def test_an_unknown_language_falls_back_to_plain_text(self) -> None:
        """The cell then renders `content`, auto-escaped, as it always did."""
        assert _highlight_diff_line("just words", "notes.unknownext") is None

    def test_a_blank_line_is_left_alone(self) -> None:
        assert _highlight_diff_line("   ", "app/thing.py") is None

    def test_the_source_is_escaped(self) -> None:
        """The template renders this unescaped, so Pygments must do the
        escaping - this is what makes that safe."""
        marked = _highlight_diff_line("x = '<script>alert(1)</script>'", "a.py")
        assert marked is not None
        assert "<script>" not in marked
        assert "&lt;script&gt;" in marked


class TestThePaletteReachesTheCode:
    def test_the_token_rules_cover_every_place_code_is_shown(self) -> None:
        """Three scopes: markdown fences, the review-comment diff context, and
        the Changes block.

        Changes is the full file diff under a merge request - the longest look
        at code the app offers - and it was the last place shipping code as
        plain escaped text, so the seven schemes in Preferences had nothing to
        colour there.
        """
        cards = (_CSS / "cards.css").read_text(encoding="utf-8")
        scope = ":is(.gl-desc-pre.highlight, .dn-code-text, .diff-line-content)"
        for surface in (".dn-code-text", ".diff-line-content"):
            assert surface in cards, (
                f"the syntax palette does not reach {surface}, so the highlight "
                "scheme cannot change what a reader sees there"
            )
        scoped = cards.count(scope)
        assert scoped > 30, f"only {scoped} token rules reach all three surfaces"

    def test_no_token_rule_was_left_behind(self) -> None:
        cards = (_CSS / "cards.css").read_text(encoding="utf-8")
        assert ".gl-desc-pre.highlight ." not in cards, (
            "a token rule still applies to markdown only - the two scopes have drifted apart again"
        )


def _files_declaring(selector: str) -> list[str]:
    """Every stylesheet that gives `selector` a colour."""
    found: list[str] = []
    pattern = re.compile(rf"^\s*{re.escape(selector)}\s*(?:,|\{{)", re.MULTILINE)
    for path in _CSS.rglob("*.css"):
        if ".min." in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            block = text[match.end() : text.find("}", match.end())]
            if "color" in block:
                found.append(path.name)
                break
    return sorted(set(found))


@pytest.mark.parametrize("selector", [".diff-add", ".diff-del"])
def test_the_diff_colour_is_declared_in_one_place(selector: str) -> None:
    """A second copy of the rule is how the preference stopped working: it did
    not override a fallback, it replaced the variable that reads the setting."""
    files = _files_declaring(selector)
    assert files == ["utilities.css"], (
        f"{selector} is coloured in {files} - whichever comes last in the "
        "cascade decides, and only utilities.css reads the reader's choice"
    )


@pytest.mark.parametrize("name", ["--gl-diff-color-added", "--gl-diff-color-removed"])
def test_the_chosen_diff_colour_is_actually_read(name: str) -> None:
    """base.html sets these on <html>; something has to consume them."""
    readers = [
        p.name
        for p in _CSS.rglob("*.css")
        if ".min." not in p.name and f"var({name}" in p.read_text(encoding="utf-8")
    ]
    assert readers, f"nothing reads {name} - the colour picker is decorative"

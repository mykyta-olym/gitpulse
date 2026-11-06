"""What the assistant writes in GitLab is Slovak, and says what it means to.

The comments are built from catalogue phrases in ``texts.py``. A phrase
missing from ``sk.json`` would land in a student's merge request in English;
a Slovak phrase that drops or renames a ``{placeholder}`` would make
``translate_text`` give up formatting and post the raw template. Neither shows
in any page scan - the text never reaches a template - so it is checked here,
over every phrase the module can write.
"""

from __future__ import annotations

import ast
import json
import string
from pathlib import Path

import pytest

from app.services.assistant import texts
from app.services.assistant.texts import Finding

ROOT = Path(__file__).resolve().parents[2]
SK = json.loads((ROOT / "src/app/i18n/catalogs/sk.json").read_text(encoding="utf-8"))
SOURCE = ROOT / "src/app/services/assistant/texts.py"


def _phrases() -> list[str]:
    """Every literal ``_t(...)`` is called with, and every value of the
    finding tables (which reach ``_t`` through a lookup)."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_t"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            found.append(node.args[0].value)
    for table in (texts._PUSH, texts._CONFLICT, texts._MR):
        found.extend(table.values())
    return found


def _fields(phrase: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(phrase) if name}


PHRASES = _phrases()


def test_the_scan_finds_the_phrases() -> None:
    assert len(PHRASES) >= 40, "the scan of texts.py found too little - is it broken?"


@pytest.mark.parametrize("phrase", PHRASES)
def test_every_phrase_has_slovak_with_the_same_placeholders(phrase: str) -> None:
    assert phrase in SK, f"no Slovak for: {phrase!r}"
    assert _fields(SK[phrase]) == _fields(phrase), (
        f"the Slovak changes the placeholders of {phrase!r}: {SK[phrase]!r}"
    )


class TestTheComments:
    def test_a_push_review_lists_what_is_wrong(self) -> None:
        body = texts.push_review(
            "main",
            [
                Finding("direct_push", {"branch": "main"}),
                Finding("web_editor_title", {"sha": "a1b2c3d4", "title": "Update README.md"}),
            ],
            new_branch=False,
        )
        assert body.startswith("Push do vetvy `main`:")
        assert "- Tento push išiel priamo do `main`" in body
        assert "„Update README.md“" in body
        assert "Maj to na pamäti" in body
        assert "{" not in body

    def test_a_new_clean_branch_is_encouraged(self) -> None:
        body = texts.push_review("feature-x", [], new_branch=True)
        assert "Dobrý začiatok: vetva `feature-x` je vytvorená." in body
        assert "Dobrá práca" in body

    def test_a_resolved_conflict_is_praised_and_an_unresolved_one_explained(self) -> None:
        assert "je vyriešený" in texts.conflict_review("README.md", [])
        body = texts.conflict_review(
            "README.md",
            [Finding("conflict_markers"), Finding("own_line_missing", {"line": "Name: Jana"})],
        )
        assert body.startswith("Riešenie konfliktu v súbore `README.md`:")
        assert "`<<<<<<<`" in body
        assert "`Name: Jana`" in body
        assert "pozriem sa ešte raz" in body

    def test_a_review_names_the_issue_and_every_finding(self) -> None:
        body = texts.mr_review(
            7,
            [
                Finding("missing_issue_link", {"issue": 7}),
                Finding("placeholder_left", {"file": "ulohy/jana.txt", "placeholder": "???"}),
            ],
        )
        assert body.startswith("Review tohto merge requestu k tiketu #7:")
        assert "`Closes #7`" in body
        assert "V súbore `ulohy/jana.txt` ostalo `???`" in body
        assert "{" not in body

    def test_the_colleague_line_carries_its_token(self) -> None:
        line = texts.colleague_line("GP-ABC123")
        assert "(GP-ABC123)" in line
        assert "\n" not in line


class TestTheExercise:
    def test_the_file_has_what_the_student_replaces(self) -> None:
        content = texts.exercise_file("jana.nova")
        assert content.startswith("Súbor k úlohe pre @jana.nova\n")
        assert content.count(texts.PLACEHOLDER) == 2
        assert content.endswith("\n")

    def test_the_issue_explains_the_steps_and_hides_its_marker(self) -> None:
        body = texts.exercise_issue_description("ulohy/jana.txt", "main", "gitpulse-assistant:x")
        assert body.startswith("Tvoja úloha, krok za krokom:")
        assert "1. Vytvor si vlastnú vetvu z `main`." in body
        assert "5. Merge request skontrolujem" in body
        assert "Zlúčiš ho potom ty." in body, "the student merges unless the course says not"
        assert "pravidlu kurzu" not in body
        assert "sekcie" not in body
        assert body.endswith("<!-- gitpulse-assistant:x -->")

    def test_the_issue_says_what_the_review_will_ask_for(self) -> None:
        """A course that grades branch names and description sections has the
        review ask for them - so the issue says so first (a real GitLab run
        showed a review demanding sections the issue never mentioned)."""
        body = texts.exercise_issue_description(
            "ulohy/jana.txt",
            "main",
            "gitpulse-assistant:x",
            bot_merges=True,
            branch_rule="^issue-[0-9]+",
            sections=("## Description", "## Testing"),
        )
        assert "Jej názov musí zodpovedať pravidlu kurzu `^issue-[0-9]+`." in body
        assert "Popis musí mať aj sekcie `## Description`, `## Testing`." in body
        assert "schválim ho a zlúčim." in body

    def test_a_quoted_line_is_not_followed_by_a_second_full_stop(self) -> None:
        line = "Tento riadok upravil kolega (GP-ABC123)."
        body = texts.conflict_review("README.md", [Finding("control_line_missing", {"line": line})])
        assert f"`{line}`" in body
        assert f"`{line}`." not in body


class TestTheCoursesLanguage:
    def test_an_english_course_gets_english(self) -> None:
        with texts.speaking("en"):
            body = texts.mr_review(7, [Finding("missing_issue_link", {"issue": 7})])
        assert body.startswith("Review of this merge request for issue #7:")
        assert "Add `Closes #7` to it." in body

    def test_the_language_is_the_courses_only_while_it_speaks(self) -> None:
        with texts.speaking("en"):
            pass
        assert texts.mr_approved_merge_it().startswith("Všetko je v poriadku")

    def test_a_language_the_app_does_not_speak_falls_back(self) -> None:
        with texts.speaking("de"):
            assert texts.colleague_line("GP-1").startswith("Tento riadok")

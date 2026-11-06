"""The colleague's commit conflicts with the student's branch - in real git.

The merge-conflict exercise only works if merging the student's branch after
the colleague's commit actually stops with a conflict. "It edits the same
lines" is the argument; these tests run git on it: a base file, the student's
branch, the colleague's commit built by ``plant`` on the default branch, and
``git merge`` - which has to fail with a conflict, every way the student can
change the file (edit a line, insert lines, delete lines, append at the end)
and also when the default branch moved on after the student branched off.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.assistant.diffing import (
    Text,
    first_change,
    has_conflict_markers,
    map_index,
    missing_lines,
    plant,
    written_lines,
)

BASE = "# Exercise\n\nName: ???\nGroup: ???\nFavourite command: ???\n"
LINE = "A colleague changed this line at the same time (GP-ABC123) - keep it."


class TestTheFirstChange:
    def test_an_edited_line(self) -> None:
        hunk = first_change(["a", "b", "c"], ["a", "B", "c"])
        assert hunk is not None
        assert (hunk.base_start, hunk.base_end, hunk.branch_start, hunk.branch_end) == (1, 2, 1, 2)

    def test_inserted_lines(self) -> None:
        hunk = first_change(["a", "c"], ["a", "b1", "b2", "c"])
        assert hunk is not None
        assert (hunk.base_start, hunk.base_end, hunk.branch_start, hunk.branch_end) == (1, 1, 1, 3)

    def test_a_deleted_line(self) -> None:
        hunk = first_change(["a", "b", "c"], ["a", "c"])
        assert hunk is not None
        assert (hunk.base_start, hunk.base_end, hunk.branch_start, hunk.branch_end) == (1, 2, 1, 1)

    def test_no_change_is_none(self) -> None:
        assert first_change(["a", "b"], ["a", "b"]) is None

    def test_only_the_first_block_counts(self) -> None:
        hunk = first_change(["a", "b", "c", "d"], ["A", "b", "c", "D"])
        assert hunk is not None
        assert (hunk.base_start, hunk.base_end) == (0, 1)


class TestMappingOntoAMovedDefaultBranch:
    def test_unchanged_lines_keep_their_index(self) -> None:
        assert map_index(["a", "b", "c"], ["a", "b", "c"], 1) == 1

    def test_lines_added_above_shift_it(self) -> None:
        assert map_index(["a", "b", "c"], ["x", "y", "a", "b", "c"], 1) == 3

    def test_a_rewritten_region_maps_to_its_start(self) -> None:
        assert map_index(["a", "b", "c"], ["a", "Z", "c"], 1) == 1

    def test_the_end_maps_to_the_end(self) -> None:
        assert map_index(["a", "b"], ["a", "b", "c"], 2) == 3


class TestPlanting:
    def test_an_edit_is_replaced_by_the_line(self) -> None:
        base = ["a", "b", "c"]
        hunk = first_change(base, ["a", "B", "c"])
        assert hunk is not None
        assert plant(base, base, hunk, "X") == ["a", "X", "c"]

    def test_an_insertion_is_answered_at_the_same_place(self) -> None:
        base = ["a", "c"]
        hunk = first_change(base, ["a", "b", "c"])
        assert hunk is not None
        assert plant(base, base, hunk, "X") == ["a", "X", "c"]

    def test_what_the_student_wrote_is_remembered(self) -> None:
        branch = ["a", "  mine  ", "", "c"]
        hunk = first_change(["a", "c"], branch)
        assert hunk is not None
        assert written_lines(branch, hunk) == ["mine"]


class TestTheFileKeepsItsShape:
    def test_crlf_and_the_trailing_newline_survive(self) -> None:
        text = Text.parse("a\r\nb\r\n")
        assert text.render(["a", "X"]) == "a\r\nX\r\n"

    def test_no_trailing_newline_stays_so(self) -> None:
        text = Text.parse("a\nb")
        assert text.render(["a", "X"]) == "a\nX"


class TestTheResolutionCheck:
    def test_markers_are_found_only_at_a_line_start(self) -> None:
        assert has_conflict_markers("a\n<<<<<<< HEAD\nb\n=======\nc\n>>>>>>> main\n")
        assert not has_conflict_markers("a\nthe text <<<<<<< in a sentence\n")
        assert not has_conflict_markers("Title\n=====\n")

    def test_a_kept_line_may_share_its_line_with_another(self) -> None:
        content = "Name: Jana - " + LINE + "\n"
        assert missing_lines(content, [LINE, "Name: Jana"]) == []
        assert missing_lines(content, ["Group: 3"]) == ["Group: 3"]


# -- Real git -------------------------------------------------------------------

_GIT = shutil.which("git")
needs_git = pytest.mark.skipif(_GIT is None, reason="git is not installed")


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    assert _GIT is not None
    return subprocess.run(  # noqa: S603 - a fixed git binary on a temp repo
        [_GIT, "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _commit(repo: Path, content: str, message: str) -> None:
    (repo / "README.md").write_text(content, encoding="utf-8", newline="")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", message)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "core.autocrlf", "false")
    _commit(repo, BASE, "base")
    return repo


def _merge_conflicts(tmp_path: Path, student: str, *, main_moved_to: str | None = None) -> bool:
    """Branch, let the student edit, plant on main, merge: did git conflict?"""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "work")
    _commit(repo, student, "the student's change")
    _git(repo, "checkout", "-q", "main")
    if main_moved_to is not None:
        _commit(repo, main_moved_to, "main moved on")

    base, mine = Text.parse(BASE), Text.parse(student)
    current = Text.parse((repo / "README.md").read_text(encoding="utf-8"))
    hunk = first_change(base.lines, mine.lines)
    assert hunk is not None
    _commit(repo, current.render(plant(base.lines, current.lines, hunk, LINE)), "colleague")

    _git(repo, "checkout", "-q", "work")
    merge = _git(repo, "merge", "--no-edit", "main", check=False)
    conflicted = merge.returncode != 0 and "CONFLICT" in (merge.stdout + merge.stderr)
    if conflicted:
        assert has_conflict_markers((repo / "README.md").read_text(encoding="utf-8"))
    return conflicted


@needs_git
@pytest.mark.parametrize(
    "student",
    [
        pytest.param(BASE.replace("Name: ???", "Name: Jana Nova"), id="edits-a-line"),
        pytest.param(BASE.replace("Group: ???\n", "Group: ???\nNotes: mine\n"), id="inserts"),
        pytest.param(BASE.replace("Group: ???\n", ""), id="deletes-a-line"),
        pytest.param(BASE + "Appended by me\n", id="appends-at-the-end"),
        pytest.param(BASE.replace("???", "x"), id="edits-several-lines"),
    ],
)
def test_merging_the_branch_conflicts(tmp_path: Path, student: str) -> None:
    assert _merge_conflicts(tmp_path, student)


@needs_git
def test_it_still_conflicts_when_main_moved_on(tmp_path: Path) -> None:
    moved = "Intro added later\n" + BASE
    student = BASE.replace("Group: ???", "Group: 3")
    assert _merge_conflicts(tmp_path, student, main_moved_to=moved)

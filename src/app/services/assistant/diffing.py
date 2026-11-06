"""Line arithmetic for the merge-conflict exercise - pure, no GitLab.

Git reports a conflict when both sides of a merge change the same lines of the
merge base, or insert at the same place. So the colleague's commit does exactly
that: it finds the first lines the student's branch changed relative to the
merge base and replaces the same lines on the default branch with a line of
its own. Whatever the student wrote there, the two edits overlap.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# A line git writes into a file it could not merge.
_CONFLICT_MARKER = re.compile(r"^(<{7}|={7}|>{7})(\s|$)")


@dataclass(frozen=True)
class Text:
    """A file as lines, remembering how it ended them."""

    lines: list[str]
    newline: str
    trailing_newline: bool

    @classmethod
    def parse(cls, content: str) -> "Text":
        newline = "\r\n" if "\r\n" in content else "\n"
        return cls(content.splitlines(), newline, content.endswith(("\n", "\r")))

    def render(self, lines: list[str]) -> str:
        """``lines`` written back the way this file writes them."""
        body = self.newline.join(lines)
        return body + self.newline if lines and self.trailing_newline else body


@dataclass(frozen=True)
class Hunk:
    """The first change: base lines ``[base_start, base_end)`` became the
    branch's lines ``[branch_start, branch_end)``."""

    base_start: int
    base_end: int
    branch_start: int
    branch_end: int


def first_change(base: list[str], branch: list[str]) -> Hunk | None:
    """The first block the branch changed, or None when it changed nothing."""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, base, branch, autojunk=False).get_opcodes():
        if tag != "equal":
            return Hunk(i1, i2, j1, j2)
    return None


def map_index(base: list[str], current: list[str], index: int) -> int:
    """Where base line ``index`` is in ``current`` - the default branch, which
    may have moved on since the student branched off.

    A line inside a block the default branch itself rewrote maps to that
    block's start: the colleague's edit then still lands in the same region.
    """
    for tag, i1, i2, j1, _j2 in SequenceMatcher(None, base, current, autojunk=False).get_opcodes():
        if i1 <= index < i2:
            return j1 + (index - i1) if tag == "equal" else j1
    return len(current)


def plant(base: list[str], current: list[str], hunk: Hunk, line: str) -> list[str]:
    """``current`` with the hunk's base lines replaced by ``line``."""
    start = map_index(base, current, hunk.base_start)
    end = map_index(base, current, hunk.base_end) if hunk.base_end > hunk.base_start else start
    return [*current[:start], line, *current[max(end, start) :]]


def written_lines(branch: list[str], hunk: Hunk) -> list[str]:
    """What the student wrote in the hunk, for checking it survives the merge."""
    return [ln.strip() for ln in branch[hunk.branch_start : hunk.branch_end] if ln.strip()]


def has_conflict_markers(content: str) -> bool:
    return any(_CONFLICT_MARKER.match(ln) for ln in content.splitlines())


def missing_lines(content: str, expected: list[str]) -> list[str]:
    """Which of ``expected`` no line of ``content`` contains. Contains, not
    equals: joining your line and the colleague's into one keeps both."""
    lines = content.splitlines()
    return [want for want in expected if not any(want in line for line in lines)]

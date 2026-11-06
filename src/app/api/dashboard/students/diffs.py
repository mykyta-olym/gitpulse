"""Diff rendering for the student page: per-file line stats, the file views
and tree the MR cards show, the syntax highlight of a diff line and the code
context a review note is anchored to."""

import re
from functools import lru_cache
from typing import Any

from app.models.mr_diff import MergeRequestDiff


def _diff_line_stats(text: str | None) -> tuple[int, int]:
    """Count added/removed lines in a unified diff (excluding the +++/--- headers).

    Lets the MR diff viewer show GitLab-style per-file +adds / -dels without
    storing them - the raw unified diff already encodes them.
    """
    if not text:
        return 0, 0
    adds = dels = 0
    for line in text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
    return adds, dels


def _build_diff_views(diffs: list[MergeRequestDiff]) -> list[dict[str, Any]]:
    """Shape MR diff rows into render-ready dicts (with per-file +/- counts).

    Ordered like GitLab's changes view: deleted last, otherwise by path, so the
    file tree reads predictably.
    """
    views: list[dict[str, Any]] = []
    for d in diffs:
        adds, dels = _diff_line_stats(d.diff)
        if d.new_file:
            change = "new"
        elif d.deleted_file:
            change = "deleted"
        elif d.renamed_file or (d.old_path and d.old_path != d.file_path):
            change = "renamed"
        else:
            change = "modified"
        views.append(
            {
                "file_path": d.file_path,
                "old_path": d.old_path,
                "diff": d.diff,
                # Rows, highlighted per line, so the template renders code as
                # code. `diff` stays for anything that still wants the raw text.
                "lines": _diff_rows(d.diff, d.file_path),
                "new_file": d.new_file,
                "deleted_file": d.deleted_file,
                "renamed_file": d.renamed_file,
                "change": change,
                "additions": adds,
                "deletions": dels,
            }
        )
    views.sort(key=lambda v: (v["change"] == "deleted", v["file_path"]))
    # Stable 1-based index links a tree entry to its diff block (diff-file-N).
    for i, v in enumerate(views, start=1):
        v["idx"] = i
    return views


def _diff_rows(diff_text: str | None, path: str) -> list[dict[str, Any]]:
    """One row per diff line: what kind of line it is, and its code as tokens.

    The page used to ship the whole diff as text and let JS split it, escape it
    and colour the row. That gave a reader added/removed backgrounds and no
    syntax highlighting at all - so the highlight scheme in Preferences had
    nothing to colour, on the one surface where it matters most.

    `_highlight_diff_line` is the same function the review-comment context uses,
    and it escapes what it returns (Pygments does), which is what makes `html`
    safe to render unescaped. A line it cannot lex comes back as None and the
    template falls back to the plain text, escaped by Jinja.
    """
    if not diff_text:
        return []
    rows: list[dict[str, Any]] = []
    for raw in diff_text.split("\n"):
        if raw.startswith("@@"):
            kind = "hunk"
        elif raw.startswith("+") and not raw.startswith("+++"):
            kind = "add"
        elif raw.startswith("-") and not raw.startswith("---"):
            kind = "del"
        else:
            kind = "ctx"
        # The marker is the row's business, not the code's: highlighting a line
        # that still carries its leading +/- lexes that character as an operator
        # and colours it as part of the statement.
        code = raw[1:] if kind in ("add", "del") and raw else raw
        rows.append(
            {
                "kind": kind,
                "marker": {"add": "+", "del": "-"}.get(kind, ""),
                "text": code,
                # A hunk header is not source, so it is never lexed.
                "html": None if kind == "hunk" else _highlight_diff_line(code, path),
            }
        )
    return rows


def _scope_diff_views(views: list[dict[str, Any]], scope: str) -> None:
    """Give every diff block an id unique to the MR/review card that owns it."""
    scope_id = _dom_id(scope, "diff")
    for view in views:
        view["anchor"] = f"{scope_id}-diff-file-{view.get('idx') or 0}"


def _build_diff_tree(views: list[dict[str, Any]]) -> dict[str, Any]:
    """Group flat diff views into a nested folder tree (GitLab changes view).

    Each node is ``{"dirs": {name: node}, "files": [view, ...]}``. Single-child
    directory chains are collapsed into one ``a/b/c`` row, exactly like GitLab,
    so deep paths don't waste horizontal space.
    """
    root: dict[str, Any] = {"dirs": {}, "files": []}
    for v in views:
        parts = v["file_path"].split("/")
        node = root
        for part in parts[:-1]:
            node = node["dirs"].setdefault(part, {"dirs": {}, "files": []})
        node["files"].append(v)

    def _collapse(node: dict[str, Any]) -> dict[str, Any]:
        node["dirs"] = {name: _collapse(child) for name, child in node["dirs"].items()}
        # Merge a folder that has exactly one sub-folder and no files of its own.
        merged: dict[str, Any] = {}
        for name, child in node["dirs"].items():
            label = name
            cur = child
            while not cur["files"] and len(cur["dirs"]) == 1:
                ((sub_name, sub_node),) = cur["dirs"].items()
                label = f"{label}/{sub_name}"
                cur = sub_node
            merged[label] = cur
        node["dirs"] = merged
        return node

    return _collapse(root)


_DIFF_HUNK_RE = re.compile(r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")


@lru_cache(maxsize=64)
def _lexer_for_path(path: str) -> Any | None:
    """A Pygments lexer chosen from the file's name, or None if it has none.

    Cached because one diff asks for the same path on every line, and choosing
    a lexer walks Pygments' whole filename table.
    """
    try:
        from pygments.lexers import get_lexer_for_filename  # type: ignore[import-untyped]
        from pygments.util import ClassNotFound  # type: ignore[import-untyped]

        try:
            return get_lexer_for_filename(path, stripnl=False)
        except ClassNotFound:
            return None
    except Exception:  # Pygments missing or broken - the diff still renders
        return None


def _highlight_diff_line(text: str, path: str) -> str | None:
    """Token markup for one diff line, or None to fall back to plain text.

    Preferences offers seven highlight schemes and the diff honoured none of
    them: the cell rendered `row.content` as plain text, so there were no
    tokens for the palette to colour and the setting could not change what a
    reader was actually looking at.

    Highlighted per LINE rather than per hunk. Pygments emits spans that may
    contain newlines for a multi-line construct, so splitting a highlighted
    hunk back into rows would cut those spans in half and hand the page broken
    markup. A line on its own can misread the inside of a multi-line string;
    that costs one line its colour, which is the cheaper failure.

    Pygments escapes the source itself, which is what makes the result safe to
    render unescaped.
    """
    lexer = _lexer_for_path(path)
    if lexer is None or not text.strip():
        return None
    try:
        from pygments import highlight  # type: ignore[import-untyped]
        from pygments.formatters import HtmlFormatter  # type: ignore[import-untyped]

        marked = highlight(text, lexer, HtmlFormatter(nowrap=True, classprefix=""))
        return marked.rstrip("\n") or None
    except Exception:
        return None


def _diff_context_for_note(
    note: Any,
    diff_views: list[dict[str, Any]],
    context: int = 6,
) -> dict[str, Any] | None:
    """Return a small GitLab-like code context block for an inline DiffNote."""
    if note.note_type != "DiffNote" or not note.position_path:
        return None
    target_new = note.position_new_line
    target_old = note.position_old_line
    if target_new is None and target_old is None:
        return None

    diff = next(
        (
            d
            for d in diff_views
            if d.get("file_path") == note.position_path or d.get("old_path") == note.position_path
        ),
        None,
    )
    if not diff or not diff.get("diff"):
        return None

    old_line: int | None = None
    new_line: int | None = None
    hunk_idx = -1
    rows: list[dict[str, Any]] = []
    for raw in str(diff["diff"]).splitlines():
        hunk = _DIFF_HUNK_RE.match(raw)
        if hunk:
            old_line = int(hunk.group("old"))
            new_line = int(hunk.group("new"))
            hunk_idx += 1
            continue
        if old_line is None or new_line is None:
            continue
        if raw.startswith("\\ No newline"):
            continue

        kind = "context"
        old_num: int | None = old_line
        new_num: int | None = new_line
        content = raw[1:] if raw and raw[0] in "+- " else raw
        if raw.startswith("+") and not raw.startswith("+++"):
            kind = "add"
            old_num = None
            new_num = new_line
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            kind = "del"
            old_num = old_line
            new_num = None
            old_line += 1
        else:
            old_line += 1
            new_line += 1

        row = {
            "kind": kind,
            "old_line": old_num,
            "new_line": new_num,
            "content": content,
            # Token markup for the reader's highlight scheme, or None when the
            # file has no lexer - the cell then renders `content` escaped, as
            # it always did.
            "content_html": _highlight_diff_line(content, str(note.position_path)),
            "marker": "+" if kind == "add" else ("-" if kind == "del" else ""),
            "is_target": False,
            "hunk": hunk_idx,
        }
        rows.append(row)

    def _target_candidates() -> list[int]:
        preferred: list[int] = []
        secondary: list[int] = []
        for idx, row in enumerate(rows):
            new_match = target_new is not None and row["new_line"] == target_new
            old_match = target_old is not None and row["old_line"] == target_old

            if target_new is not None and target_old is not None:
                if new_match and old_match:
                    preferred.append(idx)
                elif (new_match and row["kind"] != "del") or (old_match and row["kind"] != "add"):
                    secondary.append(idx)
            elif target_new is not None:
                if new_match and row["kind"] in {"add", "context"}:
                    preferred.append(idx)
                elif new_match:
                    secondary.append(idx)
            elif target_old is not None:
                if old_match and row["kind"] in {"del", "context"}:
                    preferred.append(idx)
                elif old_match:
                    secondary.append(idx)
        return preferred or secondary

    candidates = _target_candidates()
    if not candidates:
        return None

    target_idx = candidates[0]
    # Stay within the target's own hunk - crossing a hunk boundary makes the
    # snippet show discontiguous lines (e.g. 29 -> 49) that bleed into the next
    # function, which is confusing and unlike GitLab.
    target_hunk = rows[target_idx].get("hunk")
    h_start = target_idx
    while h_start > 0 and rows[h_start - 1].get("hunk") == target_hunk:
        h_start -= 1
    h_end = target_idx
    while h_end + 1 < len(rows) and rows[h_end + 1].get("hunk") == target_hunk:
        h_end += 1
    # Compact hunk (a single small function/block): show it whole, like GitLab
    # showing the entire added construct the comment refers to. Larger hunks fall
    # back to a leading window so we never dump a huge file.
    start = h_start if (h_end - h_start) <= 24 else max(h_start, target_idx - max(context, 10))
    # Only a few trailing lines past the commented line, never into the next hunk.
    end = min(h_end + 1, target_idx + 4)
    if end <= target_idx:
        end = target_idx + 1
    snippet = [dict(row) for row in rows[start:end]]
    snippet[target_idx - start]["is_target"] = True
    side = "new" if target_new is not None else "old"
    display_line = target_new if target_new is not None else target_old
    side_key = "new_line" if side == "new" else "old_line"
    visible_lines = [row[side_key] for row in snippet if row.get(side_key) is not None]
    line_start = visible_lines[0] if visible_lines else display_line
    line_end = visible_lines[-1] if visible_lines else display_line
    return {
        "path": diff.get("file_path") or note.position_path,
        "old_path": diff.get("old_path"),
        "diff_anchor": diff.get("anchor")
        or (f"diff-file-{diff.get('idx')}" if diff.get("idx") else None),
        "new_line": target_new,
        "old_line": target_old,
        "side": side,
        "display_line": display_line,
        "line_start": line_start,
        "line_end": line_end,
        "rows": snippet,
    }


def _attach_note_code_context(
    note_views: list[dict[str, Any]],
    diff_views: list[dict[str, Any]],
) -> None:
    for view in note_views:
        view["code_context"] = _diff_context_for_note(view["note"], diff_views)


def _dom_id(value: object, fallback: str = "item") -> str:
    """Turn database/GitLab identifiers into stable, CSS-safe fragment ids."""
    raw = str(value or fallback)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-")
    return safe or fallback

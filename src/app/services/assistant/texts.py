"""What the assistant writes in GitLab - comments, issues, the colleague's line.

Every sentence is an English catalogue phrase, translated into the language the
course chose for its assistant (``CourseAssistant.comment_language``, Slovak
unless a teacher picks English), so the Slovak text lives in
``i18n/catalogs/sk.json`` next to the rest of the app's. Students read these in
GitLab, from a colleague: short, concrete, one thing to do per point.

The language is set once per job with :func:`speaking`, not passed to every
sentence: everything the job writes for one course speaks the same language.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from app.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, translate_text

_language: ContextVar[str] = ContextVar("assistant_language", default=DEFAULT_LOCALE)


@contextmanager
def speaking(language: str) -> Iterator[None]:
    """Write in ``language`` (the default language when it is not supported)."""
    token = _language.set(language if language in SUPPORTED_LOCALES else DEFAULT_LOCALE)
    try:
        yield
    finally:
        _language.reset(token)


#: What the exercise file asks the student to replace.
PLACEHOLDER = "???"


@dataclass(frozen=True)
class Finding:
    """One thing a review found, with what its sentence needs."""

    code: str
    params: dict[str, Any] = field(default_factory=dict)

    def signature(self) -> str:
        return self.code + ":" + ",".join(f"{k}={self.params[k]}" for k in sorted(self.params))


def _t(text: str, **params: Any) -> str:
    return translate_text(_language.get(), text, **params)


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def _comment(intro: str, points: list[str], closing: str = "") -> str:
    parts = [intro, _bullets(points)] if points else [intro]
    if closing:
        parts.append(closing)
    return "\n\n".join(parts)


def short_sha(sha: str) -> str:
    return sha[:8]


# -- Push review --------------------------------------------------------------

_PUSH = {
    "direct_push": (
        "This push went straight to `{branch}`, the default branch. Work on a branch of "
        "your own and bring the change in through a merge request."
    ),
    "web_editor_title": (
        "Commit {sha} has the message “{title}”, which the GitLab web editor wrote. "
        "Say what you changed and why."
    ),
    "short_title": (
        "Commit {sha} has the message “{title}”, which does not say what changed. "
        "Write at least {min} characters."
    ),
    "branch_name": "The branch name `{branch}` does not follow the course's rule `{pattern}`.",
}


def push_review(branch: str, findings: list[Finding], new_branch: bool) -> str:
    points = [_t(_PUSH[f.code], **f.params) for f in findings]
    if new_branch and not any(f.code in ("direct_push", "branch_name") for f in findings):
        points.insert(0, _t("Good start: the branch `{branch}` is created.", branch=branch))
    if not findings:
        points.append(_t("The commit messages say what changed. Good work."))
    closing = _t("Keep this in mind for the next commits.") if findings else ""
    return _comment(_t("Push to the branch `{branch}`:", branch=branch), points, closing)


# -- Merge conflict -----------------------------------------------------------

_CONFLICT = {
    "conflict_markers": (
        "The file still contains conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). "
        "Remove them and keep the text that belongs there."
    ),
    # No full stop after a quoted line: it often ends with one of its own.
    "control_line_missing": (
        "A merge keeps both changes, and the line your colleague added is gone: `{line}`"
    ),
    "own_line_missing": "Your own change is gone: `{line}`",
}


def colleague_line(token: str) -> str:
    """The line the colleague's commit writes over the student's lines."""
    return _t(
        "A colleague changed this line at the same time ({token}) - keep it when you "
        "resolve the conflict.",
        token=token,
    )


def colleague_commit_message(file_path: str) -> str:
    return _t("A colleague's edit of {file}", file=file_path)


def conflict_review(file_path: str, findings: list[Finding]) -> str:
    if not findings:
        return _t(
            "The conflict in `{file}` is resolved: no conflict markers, and both your change "
            "and your colleague's line are kept. Well done!",
            file=file_path,
        )
    return _comment(
        _t("How the conflict in `{file}` is resolved:", file=file_path),
        [_t(_CONFLICT[f.code], **f.params) for f in findings],
        _t("Fix it, commit and push again - I will check once more."),
    )


# -- Issues and merge requests ------------------------------------------------

_MR = {
    "source_is_default": (
        "The merge request comes from `{branch}`, the default branch. Create a branch of "
        "your own, commit the change there and open the merge request from it."
    ),
    "target_not_default": "The merge request targets `{target}`. Point it at `{default}`.",
    "missing_issue_link": (
        "The description does not mention issue #{issue}. Add `Closes #{issue}` to it."
    ),
    "not_the_assignee": (
        "Issue #{issue} is assigned to @{assignee}. Work on the issue assigned to you."
    ),
    "file_untouched": "The merge request does not change `{file}`, the file the issue is about.",
    "extra_files": (
        "The merge request also changes files the issue does not ask for: {files}. "
        "Leave only `{file}`."
    ),
    "placeholder_left": (
        "`{file}` still contains `{placeholder}`. Replace every `{placeholder}` as the issue asks."
    ),
    "draft": "The merge request is still a draft. Mark it as ready once the work is done.",
    "has_conflicts": "The merge request has conflicts with `{default}`. Resolve them.",
    "unresolved_threads": "Some threads are not resolved yet. Resolve them before merging.",
    "branch_name": "The branch name `{branch}` does not follow the course's rule `{pattern}`.",
    "template_sections": (
        "The description is missing the sections the course asks for: {sections}."
    ),
    "pipeline_failed": "The pipeline of this merge request failed. Fix it and push again.",
}


def mr_review(issue_iid: int, findings: list[Finding]) -> str:
    return _comment(
        _t("Review of this merge request for issue #{issue}:", issue=issue_iid),
        [_t(_MR[f.code], **f.params) for f in findings],
        _t("Fix it and push, or write a comment here - I will check again."),
    )


def mr_approved_merge_it() -> str:
    return _t("Everything is in order - approved. Merge the merge request now.")


def mr_approved_waiting() -> str:
    return _t("Everything is in order - approved. It merges once the pipeline passes.")


def mr_merge_refused(reason: str) -> str:
    return _t(
        "Approved, but GitLab did not let me merge it ({reason}). Your teacher will have a look.",
        reason=reason,
    )


def mr_praise(issue_iid: int) -> str:
    return _t(
        "Everything is in order: approved and merged, issue #{issue} is closed. Great work!",
        issue=issue_iid,
    )


def mr_merged_unreviewed() -> str:
    return _t(
        "This merge request was merged before the review finished. Next time wait for the approval."
    )


# -- The exercise the assistant prepares --------------------------------------


def exercise_file(username: str) -> str:
    lines = [
        _t("Exercise file of @{username}", username=username),
        "",
        _t("Full name: {placeholder}", placeholder=PLACEHOLDER),
        _t("Favourite Git command: {placeholder}", placeholder=PLACEHOLDER),
    ]
    return "\n".join(lines) + "\n"


def exercise_files_commit_message() -> str:
    return _t("Exercise files for the issues and merge requests exercise")


def exercise_issue_title(file_path: str) -> str:
    return _t("Fill in the file {file}", file=file_path)


def exercise_issue_description(
    file_path: str,
    default_branch: str,
    marker: str,
    *,
    bot_merges: bool = False,
    branch_rule: str = "",
    sections: tuple[str, ...] = (),
) -> str:
    """The steps, with what the review will ask for besides them: the
    course's own branch rule and description sections, when it has them."""
    branch_step = _t("Create a branch of your own from `{default}`.", default=default_branch)
    if branch_rule:
        branch_step += " " + _t(
            "Its name must match the course rule `{pattern}`.", pattern=branch_rule
        )
    mr_step = _t(
        "Open a merge request into `{default}` and write `Closes #N` in its description, "
        "where N is the number of this issue.",
        default=default_branch,
    )
    if sections:
        named = ", ".join(f"`{section}`" for section in sections)
        mr_step += " " + _t("The description also needs the sections {sections}.", sections=named)
    steps = [
        branch_step,
        _t(
            "In `{file}`, replace every `{placeholder}` with your answer.",
            file=file_path,
            placeholder=PLACEHOLDER,
        ),
        _t("Commit the change with a message that says what you did, and push the branch."),
        mr_step,
        _t("I will review the merge request; once it is in order, I approve and merge it.")
        if bot_merges
        else _t(
            "I will review the merge request; once it is in order, I approve it and you merge it."
        ),
    ]
    numbered = "\n".join(f"{n}. {step}" for n, step in enumerate(steps, start=1))
    # The marker finds this issue again if the run stops before it is recorded.
    return f"{_t('Your task, step by step:')}\n\n{numbered}\n\n<!-- {marker} -->"

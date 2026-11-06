"""Push review - a comment on a student's pushed commit about how it was pushed.

It reads and comments; it never changes the repository. What it looks at is
what the version-control exercise teaches: work happens on a branch, not on
the default one, and a commit message says what changed - not the title the
GitLab web editor writes, and not "fix". A course that grades branch names
(R02) also has a new branch's name checked against its rule.

A clean push to a branch that already existed gets no comment: a colleague
does not answer every push. A new branch gets a word of encouragement with
its first commits; a branch created with none is not the student's work yet.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import TOOL_PUSH_REVIEW
from app.models.student import Student
from app.services.assistant import texts
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.tasks import (
    NEEDS_WORK,
    PASSED,
    Context,
    find_task,
    finish,
    is_transient,
    lock,
    new_task,
    record,
    refused,
)
from app.services.assistant.texts import Finding
from app.services.gitlab.client_types import GitLabAPIError
from app.utils.gitlab_patterns import is_web_editor_commit, validate_branch_name

ZERO_SHA = "0" * 40
_BRANCH_REF = "refs/heads/"
# GitLab holds a merge request "locked" while it merges it.
_MERGING = frozenset({"merged", "locked"})


def pushed_branch(payload: dict[str, Any]) -> str | None:
    """The branch a push updated - None for a tag, or a branch deleted."""
    ref = payload.get("ref") or ""
    after = payload.get("after") or ""
    if not ref.startswith(_BRANCH_REF) or not after or after == ZERO_SHA:
        return None
    return ref[len(_BRANCH_REF) :]


def _title(commit: dict[str, Any]) -> str:
    title = commit.get("title") or (commit.get("message") or "").split("\n", 1)[0]
    return str(title).strip()


def findings(
    branch: str,
    default_branch: str,
    commits: list[dict[str, Any]],
    min_title_length: int,
    *,
    new_branch: bool = False,
    branch_rule: str = "",
) -> list[Finding]:
    """What is wrong with this push, in the order the comment lists it.

    The branch name is judged once, when the branch gets its first commits -
    not on every later push to it.
    """
    found: list[Finding] = []
    if branch == default_branch:
        found.append(Finding("direct_push", {"branch": branch}))
    elif new_branch and branch_rule and not validate_branch_name(branch, branch_rule):
        found.append(Finding("branch_name", {"branch": branch, "pattern": branch_rule}))
    for commit in commits:
        title = _title(commit)
        # Git writes a merge commit's message; it is not the student's to word.
        if title.startswith("Merge "):
            continue
        sha = texts.short_sha(str(commit.get("id") or ""))
        if is_web_editor_commit(title):
            found.append(Finding("web_editor_title", {"sha": sha, "title": title}))
        elif len(title) < min_title_length:
            found.append(
                Finding("short_title", {"sha": sha, "title": title, "min": min_title_length})
            )
    return found


async def _merged_through_a_merge_request(ctx: Context, bot: BotGitLabClient, sha: str) -> bool:
    """Whether this push to the default branch is GitLab merging a merge
    request: GitLab pushes the merge as the student who clicked Merge, and
    its commits were reviewed on their own branch."""
    return any(
        mr.get("target_branch") == ctx.default_branch and mr.get("state") in _MERGING
        for mr in await bot.merge_requests_of_commit(ctx.gitlab_id, sha)
    )


async def _first_commits(ctx: Context, bot: BotGitLabClient, branch: str, before: str) -> bool:
    """Whether this push brings the branch its first commits: pushed new, or
    created in GitLab earlier and still pointing into the default branch."""
    if before == ZERO_SHA:
        return True
    if branch == ctx.default_branch:
        return False
    return await bot.is_ancestor(ctx.gitlab_id, before, ctx.default_branch)


async def handle(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    payload: dict[str, Any],
    student: Student,
) -> None:
    branch = pushed_branch(payload)
    commits = list(payload.get("commits") or [])
    # A branch created in GitLab, with nothing committed to it yet, is a push
    # of no commits: its head is someone else's commit - main's, a teacher's.
    if branch is None or not commits:
        return
    after = str(payload["after"])
    try:
        if branch == ctx.default_branch and await _merged_through_a_merge_request(ctx, bot, after):
            return
        new_branch = await _first_commits(ctx, bot, branch, str(payload.get("before") or ""))
    except GitLabAPIError as exc:
        if is_transient(exc):
            raise
        new_branch = False
    found = findings(
        branch,
        ctx.default_branch,
        commits,
        ctx.assistant.min_commit_title_length,
        new_branch=new_branch,
        branch_rule=ctx.branch_rule,
    )
    if not found and not new_branch:
        return

    await lock(session, ctx.project.id, TOOL_PUSH_REVIEW, after)
    if await find_task(session, ctx.project.id, TOOL_PUSH_REVIEW, after) is not None:
        return  # this push was reviewed already (a redelivered webhook)
    result = NEEDS_WORK if found else PASSED
    task = new_task(
        ctx,
        TOOL_PUSH_REVIEW,
        after,
        result,
        student_id=student.id,
        student_username=student.gitlab_username,
        branch=branch,
        commit_sha=after,
        detail={"findings": [f.code for f in found]},
    )
    session.add(task)
    try:
        await bot.comment_on_commit(
            ctx.gitlab_id, after, texts.push_review(branch, found, new_branch)
        )
    except GitLabAPIError as exc:
        if is_transient(exc):
            raise
        refused(task, exc)
    else:
        finish(task, result)
        record(task, "commented", url=ctx.commit_url(after))
    await session.commit()

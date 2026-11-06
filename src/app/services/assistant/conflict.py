"""Merge conflict - a colleague's commit that conflicts with a student's branch.

The exercise names one file. The first time a student's branch changes it, a
"colleague" (the bot) commits to the default branch an edit of the very lines
the student changed - a line of its own, with a token in it. When the student
then merges, the conflict is waiting.

Each later push to that branch is checked once the colleague's commit is in
its history (the student merged or rebased): no conflict markers left, the
colleague's line kept, the student's own lines kept. The result goes to the
branch's merge request, or to the pushed commit when there is none.

One exercise per student and project: the first branch that edits the file.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import TOOL_CONFLICT, AssistantTask
from app.models.student import Student
from app.services.assistant import texts
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.diffing import (
    Text,
    first_change,
    has_conflict_markers,
    missing_lines,
    plant,
    written_lines,
)
from app.services.assistant.push_review import pushed_branch
from app.services.assistant.tasks import (
    FINISHED,
    NEEDS_WORK,
    PASSED,
    PLANTED,
    WAITING,
    Context,
    find_task,
    finish,
    is_transient,
    lock,
    new_task,
    record,
    refused,
    set_detail,
)
from app.services.assistant.texts import Finding
from app.services.gitlab.client_types import GitLabAPIError

#: How many of the student's own missing lines one comment lists.
_LIST_AT_MOST = 3


def control_token(task: AssistantTask) -> str:
    """The short id that makes the colleague's line this task's own."""
    return f"GP-{task.id.hex[:6].upper()}"


def resolution_findings(content: str, control_line: str, own_lines: list[str]) -> list[Finding]:
    """What is wrong with how the conflict was resolved."""
    found: list[Finding] = []
    if has_conflict_markers(content):
        found.append(Finding("conflict_markers"))
    if missing_lines(content, [control_line.strip()]):
        found.append(Finding("control_line_missing", {"line": control_line.strip()}))
    for line in missing_lines(content, own_lines)[:_LIST_AT_MOST]:
        found.append(Finding("own_line_missing", {"line": line}))
    return found


async def handle(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    payload: dict[str, Any],
    student: Student,
) -> None:
    branch = pushed_branch(payload)
    if branch is None or branch == ctx.default_branch:
        return
    head = str(payload["after"])
    key = f"student:{student.id}"
    await lock(session, ctx.project.id, TOOL_CONFLICT, key)
    task = await find_task(session, ctx.project.id, TOOL_CONFLICT, key)
    if task is None:
        task = new_task(
            ctx,
            TOOL_CONFLICT,
            key,
            WAITING,
            student_id=student.id,
            student_username=student.gitlab_username,
        )
        session.add(task)
        await session.flush()  # the token is made from the id
    if task.state in FINISHED or (task.commit_sha and task.branch != branch):
        return
    try:
        if task.commit_sha is None:
            await _plant(ctx, bot, task, branch, head)
        else:
            await _check(ctx, bot, task, head)
    except GitLabAPIError as exc:
        if is_transient(exc):
            raise
        refused(task, exc)
    await session.commit()


async def _plant(
    ctx: Context, bot: BotGitLabClient, task: AssistantTask, branch: str, head: str
) -> None:
    """Commit the colleague's edit, once the branch has changed the file."""
    path = ctx.assistant.conflict_file_path
    task.file_path = path
    task.branch = branch
    base_sha = await bot.merge_base(ctx.gitlab_id, ctx.default_branch, head)
    base_text = await bot.file_text(ctx.gitlab_id, path, base_sha) if base_sha else None
    branch_text = await bot.file_text(ctx.gitlab_id, path, head)
    current = await bot.file_revision(ctx.gitlab_id, path, ctx.default_branch)
    if base_text is None or branch_text is None or current is None:
        task.state = WAITING
        set_detail(task, waiting_for="file")
        return
    base, mine = Text.parse(base_text), Text.parse(branch_text)
    hunk = first_change(base.lines, mine.lines)
    if hunk is None:
        task.state = WAITING
        set_detail(task, waiting_for="edit")
        return

    current_text, last_commit_id = current
    on_default = Text.parse(current_text)
    line = texts.colleague_line(control_token(task))
    commit = await bot.commit(
        ctx.gitlab_id,
        ctx.default_branch,
        texts.colleague_commit_message(path),
        [
            {
                "action": "update",
                "file_path": path,
                "content": on_default.render(plant(base.lines, on_default.lines, hunk, line)),
                "last_commit_id": last_commit_id,
            }
        ],
    )
    task.state = PLANTED
    task.commit_sha = str(commit["id"])
    set_detail(task, control_line=line, own_lines=written_lines(mine.lines, hunk), waiting_for=None)
    record(task, "planted", url=commit.get("web_url") or ctx.commit_url(task.commit_sha))


async def _check(ctx: Context, bot: BotGitLabClient, task: AssistantTask, head: str) -> None:
    """Review the resolution - once the branch contains the colleague's commit."""
    if not (task.commit_sha and task.file_path and task.branch):
        return
    if not await bot.is_ancestor(ctx.gitlab_id, task.commit_sha, head):
        return  # not merged or rebased yet
    content = await bot.file_text(ctx.gitlab_id, task.file_path, head) or ""
    detail = task.detail or {}
    found = resolution_findings(
        content, str(detail.get("control_line", "")), list(detail.get("own_lines") or [])
    )
    signature = head + "|" + ",".join(f.signature() for f in found)
    if signature == detail.get("signature"):
        return
    body = texts.conflict_review(task.file_path, found)
    mr = await bot.open_merge_request_for(ctx.gitlab_id, task.branch)
    if mr:
        note = await bot.comment_on_merge_request(ctx.gitlab_id, int(mr["iid"]), body)
        task.mr_iid = int(mr["iid"])
        url = f"{ctx.merge_request_url(task.mr_iid)}#note_{note.get('id')}"
    else:
        await bot.comment_on_commit(ctx.gitlab_id, head, body)
        url = ctx.commit_url(head)
    set_detail(task, signature=signature)
    record(task, "commented", url=url)
    if found:
        task.state = NEEDS_WORK
    else:
        finish(task, PASSED)

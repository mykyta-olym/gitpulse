"""Issues and merge requests - the review of the merge request a student opens
for the issue the assistant assigned them (``exercise.py`` assigns them).

A finite state machine over the events GitLab already sends, deterministic,
no LLM:

* a merge request opens or changes (a push, an edited description): review
  it. Something missing - one comment that asks for exactly that. Nothing
  missing - approve it, and either ask the student to merge (the default: R10
  counts a merge by a bot as not the student's) or merge it, when the course
  chose that.
* the student comments on it: review again, and answer even if nothing moved.
* it is merged: close the issue and say well done - or, when it was merged
  before the review approved it, say that instead.
* it is closed unmerged: the exercise lets go of it, so the next merge request
  the student opens for the issue is reviewed from the start.

The review asks only what the course itself grades, besides the exercise:
the course's branch-naming rule (R02) and MR template sections (R05) when the
course has those checks on.

A review is posted only when it would say something new (another commit or
other findings), so editing labels does not repeat it. The merge itself is
finished from GitLab's merge event, never from the request that asked for the
merge: that event comes whether the merge happened at once or when the
pipeline passed, and only one place then closes the issue.
"""

from collections.abc import Awaitable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import TOOL_MR_REVIEW, AssistantTask
from app.models.student import Student
from app.services.assistant import texts
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.tasks import (
    APPROVED,
    ASSIGNED,
    FAILED,
    FINISHED,
    MERGED_UNREVIEWED,
    NEEDS_WORK,
    PASSED,
    Context,
    acting_student,
    finish,
    is_transient,
    lock,
    record,
    refused,
    set_detail,
)
from app.services.assistant.texts import PLACEHOLDER, Finding
from app.services.gitlab.client_types import GitLabAPIError
from app.utils.gitlab_patterns import (
    check_template_sections,
    extract_linked_issue_iids,
    primary_linked_issue_iid,
    validate_branch_name,
)

# A head pipeline in one of these will still decide; the merge waits for it.
_PIPELINE_PENDING = frozenset(
    {"created", "waiting_for_resource", "preparing", "pending", "running", "scheduled"}
)
#: How many unrelated files one comment names.
_LIST_AT_MOST = 5


def review_findings(
    ctx: Context, task: AssistantTask, mr: dict[str, Any], paths: list[str], content: str | None
) -> list[Finding]:
    """What the merge request still lacks, in the order the comment lists it.

    ``content`` is the assigned file at the merge request's head (None when the
    merge request does not touch it).
    """
    found: list[Finding] = []
    default = ctx.default_branch
    source = str(mr.get("source_branch") or "")
    if source == default:
        found.append(Finding("source_is_default", {"branch": default}))
    elif ctx.branch_rule and not validate_branch_name(source, ctx.branch_rule):
        found.append(Finding("branch_name", {"branch": source, "pattern": ctx.branch_rule}))
    if mr.get("target_branch") != default:
        found.append(
            Finding("target_not_default", {"target": mr.get("target_branch"), "default": default})
        )
    issue = task.issue_iid
    if issue not in extract_linked_issue_iids(mr.get("description")):
        found.append(Finding("missing_issue_link", {"issue": issue}))
    if ctx.required_sections:
        _, missing = check_template_sections(mr.get("description"), list(ctx.required_sections))
        if missing:
            named = ", ".join(f"`{section}`" for section in missing)
            found.append(Finding("template_sections", {"sections": named}))
    file_path = task.file_path
    if file_path not in paths:
        found.append(Finding("file_untouched", {"file": file_path}))
    extra = [p for p in paths if p != file_path]
    if extra:
        named = ", ".join(f"`{p}`" for p in extra[:_LIST_AT_MOST])
        found.append(Finding("extra_files", {"files": named, "file": file_path}))
    if content is not None and PLACEHOLDER in content:
        found.append(Finding("placeholder_left", {"file": file_path, "placeholder": PLACEHOLDER}))
    if mr.get("draft") or mr.get("work_in_progress"):
        found.append(Finding("draft"))
    if mr.get("has_conflicts"):
        found.append(Finding("has_conflicts", {"default": default}))
    if mr.get("blocking_discussions_resolved") is False:
        found.append(Finding("unresolved_threads"))
    if (mr.get("head_pipeline") or {}).get("status") == "failed":
        found.append(Finding("pipeline_failed"))
    return found


async def _task_for(
    session: AsyncSession, ctx: Context, mr: dict[str, Any], *, linked_only: bool
) -> AssistantTask | None:
    """The exercise this merge request belongs to: the one already linked to
    it; else (``linked_only`` off) the issue it names, or its author's open one."""
    base = select(AssistantTask).where(
        AssistantTask.project_id == ctx.project.id, AssistantTask.tool == TOOL_MR_REVIEW
    )
    iid = int(mr["iid"])
    task = (await session.execute(base.where(AssistantTask.mr_iid == iid))).scalars().first()
    if task is not None or linked_only:
        return task
    issue_iid = primary_linked_issue_iid(mr.get("description"), mr.get("source_branch"))
    if issue_iid is not None:
        stmt = base.where(AssistantTask.issue_iid == issue_iid, AssistantTask.mr_iid.is_(None))
        task = (await session.execute(stmt)).scalars().first()
        if task is not None:
            return task
    author = await acting_student(session, ctx.project, mr.get("author_id"), None)
    if author is None:
        return None
    stmt = base.where(
        AssistantTask.student_id == author.id,
        AssistantTask.mr_iid.is_(None),
        AssistantTask.state.not_in(FINISHED),
    )
    return (await session.execute(stmt)).scalars().first()


async def _locked(session: AsyncSession, task: AssistantTask) -> AssistantTask:
    """The task, locked and re-read: another event may have moved it."""
    await lock(session, task.project_id, task.tool, task.key)
    await session.refresh(task)
    return task


async def on_merge_request(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    payload: dict[str, Any],
    *,
    by_bot: bool,
) -> None:
    mr = payload.get("object_attributes") or {}
    if not mr.get("iid"):
        return
    action = mr.get("action")
    if action == "merge":
        # Only the merge request the exercise is following counts here: the
        # author merging some other merge request is not this one.
        task = await _task_for(session, ctx, mr, linked_only=True)
        if task is not None:
            task = await _locked(session, task)
            await _guard(session, task, _on_merged(ctx, bot, task))
        return
    if action == "close":
        task = await _task_for(session, ctx, mr, linked_only=True)
        if task is not None:
            task = await _locked(session, task)
            _let_go(task)
            await session.commit()
        return
    if by_bot:
        return
    task = await _task_for(session, ctx, mr, linked_only=False)
    if task is None:
        return
    task = await _locked(session, task)
    if task.state not in FINISHED:
        await _guard(session, task, _review(session, ctx, bot, task, int(mr["iid"]), answer=False))


async def on_note(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    payload: dict[str, Any],
    student: Student,
) -> None:
    """The student commented on their merge request: look again, and answer."""
    note = payload.get("object_attributes") or {}
    mr = payload.get("merge_request") or {}
    if note.get("noteable_type") != "MergeRequest" or note.get("system") or not mr.get("iid"):
        return
    task = await _task_for(session, ctx, mr, linked_only=False)
    if task is None or task.student_id != student.id:
        return
    task = await _locked(session, task)
    if task.state not in FINISHED:
        # GitLab's note ids only grow: a review comment newer than this one
        # already answered it (another event's review got there first).
        note_id, last_id = note.get("id"), (task.detail or {}).get("last_note_id")
        answered = isinstance(note_id, int) and isinstance(last_id, int) and note_id <= last_id
        await _guard(
            session, task, _review(session, ctx, bot, task, int(mr["iid"]), answer=not answered)
        )


def _let_go(task: AssistantTask) -> None:
    """The merge request was closed unmerged: the next one starts afresh."""
    if task.state in FINISHED:
        return
    task.mr_iid = None
    task.state = ASSIGNED
    set_detail(task, signature=None, approved=False)
    record(task, "mr_closed")


async def _guard(session: AsyncSession, task: AssistantTask, step: Awaitable[None]) -> None:
    """Run one step; a refusal from GitLab is recorded, a GitLab outage retried."""
    try:
        await step
    except GitLabAPIError as exc:
        if is_transient(exc):
            raise
        refused(task, exc)
    await session.commit()


async def _review(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    task: AssistantTask,
    iid: int,
    *,
    answer: bool,
) -> None:
    mr = await bot.merge_request(ctx.gitlab_id, iid)
    if mr is None or mr.get("state") != "opened":
        return
    if task.state == APPROVED and mr.get("merge_when_pipeline_succeeds"):
        return  # approved; GitLab merges it once the pipeline passes
    author_id = (mr.get("author") or {}).get("id")
    assignee_id = (task.detail or {}).get("assignee_id")
    if author_id != assignee_id:
        await _not_the_assignee(ctx, bot, task, iid)
        return
    task.mr_iid = iid
    task.branch = mr.get("source_branch")
    paths = await bot.changed_paths(ctx.gitlab_id, iid)
    content = None
    if task.file_path in paths:
        content = await bot.file_text(ctx.gitlab_id, str(task.file_path), str(mr["sha"])) or ""
    found = review_findings(ctx, task, mr, paths, content)
    signature = str(mr["sha"]) + "|" + ",".join(f.signature() for f in found)
    # The signature is kept once the review reached its outcome, so a step
    # that GitLab failed is taken again when the job is retried.
    if signature == (task.detail or {}).get("signature") and not answer:
        return
    if found:
        note = await bot.comment_on_merge_request(
            ctx.gitlab_id, iid, texts.mr_review(int(task.issue_iid or 0), found)
        )
        task.state = NEEDS_WORK
        # A new commit can undo what was approved: a merge now would not be
        # the one the review approved.
        set_detail(task, signature=signature, approved=False, last_note_id=note.get("id"))
        record(task, "commented", url=_note_url(ctx, iid, note))
        return
    await _approve_and_merge(session, ctx, bot, task, mr, signature)


async def _not_the_assignee(
    ctx: Context, bot: BotGitLabClient, task: AssistantTask, iid: int
) -> None:
    """Someone else's merge request names this issue: tell them, once."""
    told = list((task.detail or {}).get("told_mrs") or [])
    if iid in told:
        return
    finding = Finding(
        "not_the_assignee", {"issue": task.issue_iid, "assignee": task.student_username}
    )
    await bot.comment_on_merge_request(
        ctx.gitlab_id, iid, texts.mr_review(int(task.issue_iid or 0), [finding])
    )
    set_detail(task, told_mrs=[*told, iid])


async def _approve_and_merge(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    task: AssistantTask,
    mr: dict[str, Any],
    signature: str,
) -> None:
    iid, sha = int(mr["iid"]), str(mr["sha"])
    try:
        await bot.approve(ctx.gitlab_id, iid, sha)
    except GitLabAPIError as exc:
        # Already approved, or approvals not offered: the merge is what counts.
        if is_transient(exc):
            raise
    task.state = APPROVED
    set_detail(task, approved=True)
    record(task, "approved", url=ctx.merge_request_url(iid))
    if not ctx.assistant.mr_bot_merges:
        # The student merges; GitLab's merge event then finishes the exercise.
        note = await bot.comment_on_merge_request(ctx.gitlab_id, iid, texts.mr_approved_merge_it())
        set_detail(task, signature=signature, last_note_id=note.get("id"))
        record(task, "commented", url=_note_url(ctx, iid, note))
        return
    # Committed BEFORE the merge: GitLab's merge event can be handled while the
    # merge request is still being answered, and it finishes the exercise only
    # for a task it finds linked and approved.
    await session.commit()
    pipeline = (mr.get("head_pipeline") or {}).get("status")
    try:
        merged = await bot.merge(
            ctx.gitlab_id, iid, sha, when_pipeline=pipeline in _PIPELINE_PENDING
        )
    except GitLabAPIError as exc:
        if is_transient(exc):
            raise
        task = await _locked(session, task)
        await bot.comment_on_merge_request(ctx.gitlab_id, iid, texts.mr_merge_refused(str(exc)))
        task.state = FAILED
        set_detail(task, signature=signature)
        record(task, "error", str(exc))
        return
    # Merged at once, the merge event (maybe already handled) finishes it.
    task = await _locked(session, task)
    set_detail(task, signature=signature)
    if merged.get("state") != "merged" and task.state == APPROVED:
        note = await bot.comment_on_merge_request(ctx.gitlab_id, iid, texts.mr_approved_waiting())
        set_detail(task, last_note_id=note.get("id"))
        record(task, "merge_scheduled", url=_note_url(ctx, iid, note))


async def _on_merged(ctx: Context, bot: BotGitLabClient, task: AssistantTask) -> None:
    """GitLab merged the merge request: close the issue and say well done."""
    iid = int(task.mr_iid or 0)
    if task.state in FINISHED:
        return
    if not (task.detail or {}).get("approved"):
        note = await bot.comment_on_merge_request(ctx.gitlab_id, iid, texts.mr_merged_unreviewed())
        finish(task, MERGED_UNREVIEWED)
        record(task, "commented", url=_note_url(ctx, iid, note))
        return
    issue_iid = int(task.issue_iid or 0)
    issue = await bot.issue(ctx.gitlab_id, issue_iid)
    if issue and issue.get("state") == "opened":
        await bot.close_issue(ctx.gitlab_id, issue_iid)
        record(task, "closed_issue")
    note = await bot.comment_on_merge_request(ctx.gitlab_id, iid, texts.mr_praise(issue_iid))
    finish(task, PASSED)
    record(task, "merged", url=_note_url(ctx, iid, note))


def _note_url(ctx: Context, iid: int, note: dict[str, Any]) -> str:
    return f"{ctx.merge_request_url(iid)}#note_{note.get('id')}"

"""Prepare the issues and merge requests exercise - a teacher's one-off action.

For every chosen project: a text file for each student of its team, in one
commit on the default branch, and an issue assigned to each student asking
them to fill it in through a branch and a merge request (``mr_review.py``
reviews that merge request).

Running it again is safe and is how a student added later gets their issue:
students who already have one are skipped, and a file that already exists is
left as it is.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import TOOL_MR_REVIEW, AssistantTask, CourseAssistant
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team_member import TeamMember
from app.services.assistant import texts
from app.services.assistant.client import BotGitLabClient
from app.services.assistant.tasks import (
    ASSIGNED,
    Context,
    branch_rule_to_name,
    counted_member,
    course_rules,
    new_task,
    record,
)
from app.services.audit import write_audit
from app.services.gitlab.client_types import GitLabAPIError

logger = logging.getLogger(__name__)

USERNAME_FIELD = "{username}"


def exercise_path(template: str, username: str) -> str:
    return template.replace(USERNAME_FIELD, username)


def _marker(task: AssistantTask) -> str:
    return f"gitpulse-assistant:{task.id}"


async def _students(session: AsyncSession, project: GitLabProject) -> tuple[list[Student], int]:
    """The team's students GitLab can assign an issue to - and how many it
    cannot: a roster import parks a placeholder (negative) GitLab id until the
    student is synced, and an issue cannot be assigned to that."""
    stmt = (
        select(Student)
        .join(TeamMember, TeamMember.student_id == Student.id)
        .where(TeamMember.team_id == project.team_id, *counted_member())
        .order_by(Student.gitlab_username)
    )
    students = list((await session.execute(stmt)).scalars().all())
    assignable = [s for s in students if (s.gitlab_user_id or 0) > 0]
    return assignable, len(students) - len(assignable)


async def prepare(
    session: AsyncSession,
    course: Course,
    assistant: CourseAssistant,
    bot: BotGitLabClient,
    projects: list[GitLabProject],
    *,
    actor: str,
    gitlab_url: str,
    progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """Prepare every project; one project failing does not stop the others.
    ``progress(done, total)`` hears after each project (the top bar)."""
    results: list[dict[str, Any]] = []
    for done, project in enumerate(projects, start=1):
        result: dict[str, Any] = {"path": project.gitlab_project_path, "created": 0, "skipped": 0}
        try:
            await _prepare_project(session, course, assistant, bot, project, result, gitlab_url)
        except GitLabAPIError as exc:
            # GitLab refused; what was recorded before that is committed.
            result["error"] = str(exc)
            logger.warning("assistant_exercise_failed project=%s", project.id, exc_info=True)
        results.append(result)
        if progress is not None:
            progress(done, len(projects))
    assistant.last_exercise_run = {
        "at": datetime.now(UTC).isoformat(),
        "by": actor,
        "projects": results,
    }
    await write_audit(
        session,
        action="assistant.exercise_prepared",
        actor=actor,
        entity_type="course",
        entity_id=course.id,
        detail={
            "summary": ", ".join(str(r["path"]) for r in results),
            "created": sum(int(r.get("created") or 0) for r in results),
            "refused": [r["path"] for r in results if r.get("error")],
        },
    )
    await session.commit()
    return results


async def _prepare_project(
    session: AsyncSession,
    course: Course,
    assistant: CourseAssistant,
    bot: BotGitLabClient,
    project: GitLabProject,
    result: dict[str, Any],
    gitlab_url: str,
) -> None:
    info = await bot.project(project.gitlab_project_id)
    if info is None:
        raise GitLabAPIError(404, "the bot account cannot see this project")
    default_branch = str(info.get("default_branch") or project.default_branch)
    branch_rule, sections = course_rules(course.settings)
    ctx = Context(
        course,
        project,
        assistant,
        default_branch,
        web_url=f"{gitlab_url.rstrip('/')}/{project.gitlab_project_path}",
        branch_rule=branch_rule,
        required_sections=sections,
    )
    existing = {
        t.student_id: t
        for t in (
            await session.execute(
                select(AssistantTask).where(
                    AssistantTask.project_id == project.id,
                    AssistantTask.tool == TOOL_MR_REVIEW,
                )
            )
        ).scalars()
    }
    students, result["unassignable"] = await _students(session, project)
    todo = [s for s in students if _needs_issue(existing.get(s.id))]
    result["skipped"] = len(existing) - sum(1 for t in existing.values() if _needs_issue(t))
    if not todo:
        return

    template = assistant.exercise_file_template
    actions = []
    for student in todo:
        path = exercise_path(template, student.gitlab_username)
        if await bot.file_text(project.gitlab_project_id, path, default_branch) is None:
            actions.append(
                {
                    "action": "create",
                    "file_path": path,
                    "content": texts.exercise_file(student.gitlab_username),
                }
            )
    if actions:
        await bot.commit(
            project.gitlab_project_id,
            default_branch,
            texts.exercise_files_commit_message(),
            actions,
        )

    for student in todo:
        await _assign(session, ctx, bot, student, existing.get(student.id), template)
        result["created"] += 1


def _needs_issue(task: AssistantTask | None) -> bool:
    return task is None or task.issue_iid is None


async def _assign(
    session: AsyncSession,
    ctx: Context,
    bot: BotGitLabClient,
    student: Student,
    task: AssistantTask | None,
    template: str,
) -> None:
    """Open the student's issue - the task row first, so a run that stops
    between the two finds the issue again by the marker in its description."""
    # A task recorded by an earlier run keeps the file it was given then.
    path = (task.file_path if task else None) or exercise_path(template, student.gitlab_username)
    issue = None
    if task is None:
        task = new_task(
            ctx,
            TOOL_MR_REVIEW,
            f"student:{student.id}",
            ASSIGNED,
            student_id=student.id,
            student_username=student.gitlab_username,
            file_path=path,
            detail={"assignee_id": student.gitlab_user_id},
        )
        session.add(task)
        await session.commit()
    else:
        issue = await bot.find_issue(ctx.gitlab_id, _marker(task))
    if issue is None:
        # Step 1 already asks for a branch of one's own: the default rule
        # goes without saying.
        description = texts.exercise_issue_description(
            path,
            ctx.default_branch,
            _marker(task),
            bot_merges=ctx.assistant.mr_bot_merges,
            branch_rule=branch_rule_to_name(ctx.branch_rule),
            sections=ctx.required_sections,
        )
        issue = await bot.create_issue(
            ctx.gitlab_id,
            texts.exercise_issue_title(path),
            description,
            int(student.gitlab_user_id or 0),
        )
    task.issue_iid = int(issue["iid"])
    record(task, "issue_created", url=issue.get("web_url"))
    await session.commit()

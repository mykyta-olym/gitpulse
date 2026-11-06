"""The course's Assistant page - the classroom assistant, for teachers only.

Students never see a page of it; they meet the bot in GitLab. Here a teacher
connects the bot's token, chooses its tools, prepares the issues exercise and
follows what the bot did. The page reads only what is stored: every GitLab
call is an explicit action (connecting the token) or a background job.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select

from app.api.dashboard._access import _membership_role, _runs_course
from app.api.dashboard._helpers import (
    _csrf_token,
    _feature_disabled_response,
    _not_found_response,
    _role_context,
    _templates,
    logger,
)
from app.config import get_settings
from app.dependencies import CSRFCheck, DbSession, RateLimitDep, TeacherAuth
from app.i18n import LOCALE_LABELS, SUPPORTED_LOCALES, resolve_locale, translate_text
from app.models.assistant import TOOLS
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.user import User
from app.services.assistant import account
from app.services.assistant.tasks import branch_rule_to_name, course_rules
from app.services.courses import ensure_course_active
from app.services.events import enqueue_assistant_exercise
from app.services.webhook_activity import compute_webhook_activity

router = APIRouter()


def _actor(auth: dict[str, str]) -> str:
    return auth.get("gitlab_username") or auth.get("user") or "teacher"


def _refusal(error: str, status_code: int) -> JSONResponse:
    return JSONResponse({"ok": False, "error": error}, status_code=status_code)


async def _course_for_write(
    db: DbSession, course_id: uuid.UUID, auth: dict[str, str]
) -> Course | JSONResponse:
    """The course a write is for - or the JSON refusal when there is none to
    write to (the feature off, no such course, not one the caller runs)."""
    if not get_settings().feature_classroom_assistant:
        return _refusal("feature_disabled", 404)
    course = await db.get(Course, course_id)
    if course is None or not _runs_course(auth, await _membership_role(db, course_id, auth)):
        return _refusal("not_found", 404)
    return course


async def _activity_context(db: DbSession, course: Course) -> dict[str, Any]:
    """What the activity card renders from - the page and the card alone."""
    activity = await account.activity(db, course.id)
    ids = {row["student_gitlab_id"] for row in activity if row["student_gitlab_id"]}
    avatars: dict[int | None, str | None] = {}
    if ids:
        result = await db.execute(
            select(User.gitlab_user_id, User.avatar_url).where(User.gitlab_user_id.in_(ids))
        )
        avatars = dict(result.tuples().all())
    for row in activity:
        row["avatar_url"] = avatars.get(row["student_gitlab_id"]) or ""
    return {"activity": activity, "activity_limit": account.ACTIVITY_LIMIT, "tool_names": TOOLS}


@router.get("/courses/{course_id}/assistant", response_class=HTMLResponse)
async def course_assistant_page(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    course = await db.get(Course, course_id)
    # The course's owner and teachers (and admins) only - not everyone who
    # can see the course: the page holds the bot that writes to GitLab.
    course_role = await _membership_role(db, course_id, _auth) if course else None
    if not course or not _runs_course(_auth, course_role):
        return _not_found_response(request, "Course")
    if not get_settings().feature_classroom_assistant:
        locale = resolve_locale(request)
        return _feature_disabled_response(
            request,
            translate_text(locale, "Classroom Assistant"),
            translate_text(locale, "The classroom assistant is turned off on this server."),
            "FEATURE_CLASSROOM_ASSISTANT=true",
            **_role_context(_auth),
        )
    assistant = await account.assistant_for(db, course.id)
    branch_rule, required_sections = course_rules(course.settings)
    webhooks = await compute_webhook_activity(db, [course.id])
    return _templates(request).TemplateResponse(
        request,
        "course_assistant.html",
        {
            "request": request,
            "course": course,
            "course_role": course_role,
            "assistant": assistant,
            "can_act": assistant is not None and assistant.can_act(datetime.now(UTC)),
            "problems": account.problems(assistant),
            "branch_rule": branch_rule_to_name(branch_rule),
            "required_sections": required_sections,
            "has_webhook": webhooks.has_webhook(course.id),
            "webhook_silent": course.id in webhooks.silent,
            "languages": [(code, LOCALE_LABELS.get(code, code)) for code in SUPPORTED_LOCALES],
            "exercise_run": account.last_exercise_run(assistant),
            "tools": account.tools_of(assistant),
            "projects": await account.course_projects(db, course.id),
            **await _activity_context(db, course),
            "csrf_token": _csrf_token(_auth),
            **_role_context(_auth),
        },
    )


@router.get("/courses/{course_id}/assistant/activity", response_class=HTMLResponse)
async def course_assistant_activity(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """The activity card alone, for what redraws it: its Refresh, the end of a
    Prepare exercise run and the course's live stream when the bot acts."""
    course = await db.get(Course, course_id)
    if (
        not get_settings().feature_classroom_assistant
        or course is None
        or not _runs_course(_auth, await _membership_role(db, course_id, _auth))
    ):
        return _not_found_response(request, "Course")
    html = (
        _templates(request)
        .get_template("partials/course/_assistant_activity.html")
        .render(
            {
                "request": request,
                "course": course,
                **await _activity_context(db, course),
                **_role_context(_auth),
            }
        )
    )
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@router.post("/courses/{course_id}/assistant/token")
async def course_assistant_connect(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    """Connect the bot account: GitLab confirms the token before it is kept."""
    course = await _course_for_write(db, course_id, _auth)
    if isinstance(course, JSONResponse):
        return course
    # An archived course is read-only, its assistant included.
    await ensure_course_active(db, course_id)
    form = await request.form()
    try:
        assistant = await account.connect(
            db, course.id, str(form.get("token") or ""), actor=_actor(_auth)
        )
    except account.TokenRejectedError as exc:
        return _refusal(exc.reason, 422)
    logger.info("assistant_connected", course_id=str(course_id), bot=assistant.bot_username)
    return JSONResponse({"ok": True, "bot_username": assistant.bot_username})


@router.post("/courses/{course_id}/assistant/disconnect")
async def course_assistant_disconnect(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    course = await _course_for_write(db, course_id, _auth)
    if isinstance(course, JSONResponse):
        return course
    # An archived course is read-only, its assistant included.
    await ensure_course_active(db, course_id)
    assistant = await account.assistant_for(db, course.id)
    if assistant is not None and assistant.is_connected:
        await account.disconnect(db, assistant, actor=_actor(_auth))
    logger.info("assistant_disconnected", course_id=str(course_id))
    return JSONResponse({"ok": True})


@router.post("/courses/{course_id}/assistant/tools")
async def course_assistant_tools(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    course = await _course_for_write(db, course_id, _auth)
    if isinstance(course, JSONResponse):
        return course
    # An archived course is read-only, its assistant included.
    await ensure_course_active(db, course_id)
    tools = account.read_tools(await request.form())
    errors = tools.errors()
    if errors:
        return JSONResponse({"ok": False, "error": "invalid", "fields": errors}, status_code=422)
    assistant = await account.ensure_assistant(db, course.id)
    await account.save_tools(db, assistant, tools, actor=_actor(_auth))
    return JSONResponse({"ok": True})


@router.post("/courses/{course_id}/assistant/exercise")
async def course_assistant_exercise(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    """Queue "Prepare exercise" for the chosen projects of this course."""
    course = await _course_for_write(db, course_id, _auth)
    if isinstance(course, JSONResponse):
        return course
    # An archived course is read-only, its assistant included.
    await ensure_course_active(db, course_id)
    assistant = await account.assistant_for(db, course.id)
    if assistant is None or not assistant.is_connected:
        return _refusal("not_connected", 409)
    if not assistant.can_act(datetime.now(UTC)):
        return _refusal("token_unusable", 409)
    if not assistant.mr_review_enabled:
        return _refusal("tool_off", 409)
    run = account.last_exercise_run(assistant)
    if run is not None and run["state"] == "running":
        return _refusal("already_running", 409)
    known = {p["id"] for p in await account.course_projects(db, course.id)}
    chosen: list[Any] = (await request.form()).getlist("project_ids")
    project_ids = [str(p) for p in chosen if str(p) in known]
    if not project_ids:
        return _refusal("no_projects", 422)
    # A BackgroundJob like a sync's: the top bar follows it to its end, and
    # Admin > System's Job History lists it with its duration.
    job = BackgroundJob(job_type="assistant_exercise", course_id=course.id)
    db.add(job)
    await db.flush()
    previous = await account.start_exercise_run(db, assistant, actor=_actor(_auth))
    rq_job_id = enqueue_assistant_exercise(str(course.id), project_ids, _actor(_auth), str(job.id))
    if rq_job_id is None:
        assistant.last_exercise_run = previous
        job.status = "failed"
        job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.commit()
        return _refusal("queue_unavailable", 503)
    job.rq_job_id = rq_job_id
    await db.commit()
    return JSONResponse({"ok": True, "projects": len(project_ids), "job_id": str(job.id)})

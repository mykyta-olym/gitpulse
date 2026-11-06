"""Course settings and configuration import/export routes."""

import json as json_module
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.background import BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dashboard._access import _can_manage_course, _membership_role
from app.api.dashboard._helpers import (
    _R_CHECK_CATEGORIES,
    _R_CHECK_DESCRIPTIONS,
    _R_CHECK_WEIGHT_FIELDS,
    CHECK_DEFS,
    _conflict_redirect,
    _csrf_token,
    _not_found_response,
    _role_context,
    _templates,
    logger,
)
from app.api.dashboard.courses.settings_config import (
    _import_config_create_course_impl,
    apply_config_sections,
    apply_course_section,
    check_weight_warning,
    parse_config_json,
    read_config_text,
)
from app.api.dashboard.courses.settings_form import configuration_from_form
from app.api.dashboard.courses.settings_view import build_semester_status
from app.compliance.patterns import resolve_patterns
from app.config import get_settings
from app.dependencies import (
    CSRFCheck,
    DbSession,
    RateLimitDep,
    TeacherAuth,
)
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.schemas.courses import CourseConfigurationUpdate
from app.services import course_settings as configuration
from app.services.assistant import account as assistant_account
from app.utils.http_headers import content_disposition_attachment

if TYPE_CHECKING:
    pass

router = APIRouter()

# -- Truncation / cardinality limits (route-local; config-import limits live
#    in course_settings_config) --


# -- Route handlers --


@router.get("/semester-presets")
async def semester_presets(
    _auth: TeacherAuth,
) -> JSONResponse:
    """List built-in semester calendar presets (TUKE FEI / Informatika)."""
    from app.utils.semester_presets import get_presets

    return JSONResponse({"presets": get_presets()})


@router.get("/courses/{course_id}/webhooks/table", response_class=HTMLResponse)
async def webhook_table(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Refresh the webhook rows using the initial page's projection."""
    course = await db.get(Course, course_id)
    if not course or not await _can_manage_course(course, _auth, db):
        return _not_found_response(request, "Course")
    from app.api.webhook_configs import build_webhook_configs_payload

    payload = await build_webhook_configs_payload(db, course_id, request)
    return _templates(request).TemplateResponse(
        request,
        "partials/course_settings/_webhook_rows.html",
        {"course": course, "webhook_configs": payload.configurations},
    )


@router.get("/courses/{course_id}/settings", response_class=HTMLResponse)
async def course_settings_page(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    course = await db.get(Course, course_id)
    if not course:
        return _not_found_response(request, "Course")

    # Access control: only admin/teacher with course access
    if not await _can_manage_course(course, _auth, db):
        return _not_found_response(request, "Course", message="Access denied.")

    if not course.settings:
        # A course with no settings row simply has none YET. This used to answer
        # 404 with "This course needs to be configured. Go to course settings to
        # set it up" - telling an admin to open the page they had just opened,
        # from the one page that could have created it. Every column on the model
        # has a default, and the import path already creates a bare row exactly
        # this way, so create it and render the page it was asking for.
        # Anyone reaching this line is an admin or a teacher with access to the
        # course: `TeacherAuth` and `_can_manage_course` have both passed above.
        settings_row = CourseSettings(course_id=course.id)
        settings_row.course = course
        db.add(settings_row)
        await db.commit()
        await db.refresh(course)

    # -- Cache settings once for optional integrations (was called 7x) --
    _s = get_settings()
    multi_tenant_enabled = _s.feature_multi_tenant
    llm_enabled = _s.llm_analysis_enabled
    llm_api_key_configured = bool(_s.llm_api_key)

    from app.services.llm.service import PROMPT_PRESETS

    # LLM / AI analysis config
    llm_resource_urls = getattr(course.settings, "llm_resource_urls", []) or []
    llm_custom_prompt = getattr(course.settings, "llm_custom_prompt", None) or ""

    semester_status = build_semester_status(
        course,
        grace_days=int(getattr(_s, "semester_grace_days", 14)),
        default_length_weeks=int(getattr(_s, "semester_default_length_weeks", 14)),
    )

    # Active groups for the "Transfer to new semester" wizard's selective mode.
    from app.models.team import Team as _Team

    _transfer_teams_q = (
        select(_Team)
        .where(_Team.course_id == course.id, _Team.is_active.is_(True))
        .order_by(_Team.name)
    )
    transfer_teams = (await db.scalars(_transfer_teams_q)).all()

    # Render both tables on the server; refreshes use the same row templates.
    from app.api.webhook_configs import build_webhook_configs_payload
    from app.services.course_checks import build_checks_payload

    checks_first_json = await build_checks_payload(course, db)
    webhook_configs = (await build_webhook_configs_payload(db, course_id, request)).configurations
    course_role = await _membership_role(db, course_id, _auth)
    active_check_filter = request.query_params.get("check_filter", "all")
    if active_check_filter not in {"all", "builtin", "custom", *_R_CHECK_CATEGORIES.values()}:
        active_check_filter = "all"

    return _templates(request).TemplateResponse(
        request,
        "course_settings.html",
        {
            "request": request,
            "course": course,
            "course_role": course_role,
            "settings": course.settings,
            "checks_first_json": checks_first_json,
            "active_check_filter": active_check_filter,
            "webhook_configs": webhook_configs,
            "csrf_token": _csrf_token(_auth),
            "multi_tenant_enabled": multi_tenant_enabled,
            "transfer_teams": transfer_teams,
            "llm_enabled": llm_enabled,
            "llm_api_key_configured": llm_api_key_configured,
            "llm_resource_urls": llm_resource_urls,
            "llm_custom_prompt": llm_custom_prompt,
            "llm_prompt_presets": PROMPT_PRESETS,
            "semester_status": semester_status,
            **_role_context(_auth),
        },
    )


@router.post("/courses/{course_id}/settings")
async def course_settings_save(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    course = await db.get(Course, course_id)
    if not course or not course.settings:
        return _not_found_response(request, "Course")
    if not await _can_manage_course(course, _auth, db):
        return _not_found_response(request, "Course", message="Access denied.")
    enhanced = "application/json" in request.headers.get("content-type", "")
    if not course.is_active:
        if enhanced:
            raise HTTPException(409, "This course is archived and is read-only.")
        return _conflict_redirect(f"/dashboard/courses/{course_id}/settings")
    try:
        data = (
            CourseConfigurationUpdate.model_validate(await request.json())
            if enhanced
            else configuration_from_form(await request.form())
        )
    except (ValidationError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result = await configuration.save_configuration(
            db, course, data, actor=str(_auth.get("user_id", ""))
        )
    except HTTPException as exc:
        if not enhanced and exc.status_code == 409:
            await db.rollback()
            return _conflict_redirect(f"/dashboard/courses/{course_id}/settings")
        raise
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            409, "A course with this code and academic period already exists."
        ) from exc
    if enhanced:
        return JSONResponse(result)
    return Response(
        status_code=303, headers={"Location": f"/dashboard/courses/{course_id}/settings"}
    )


@router.post("/courses/import-config")
async def import_config_create_course(
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
    background_tasks: BackgroundTasks,
) -> Response:
    """Import a full course configuration, creating the course if needed.

    This is the dashboard-level entry point that allows teachers to create
    a fully-configured course from a single JSON file.  If a course with
    the same (code, academic_year, semester) already exists, it is updated
    in-place.  Otherwise a new Course + CourseSettings row is created first.
    """
    try:
        actor = _auth.get("user", "system")
        return await _import_config_create_course_impl(
            request,
            db,
            actor=actor,
            background_tasks=background_tasks,
        )
    except Exception as exc:
        logger.exception("import_config_crash: %s", exc)
        return JSONResponse(
            {"error": "Internal error during configuration import. Check server logs for details."},
            status_code=500,
        )


@router.get("/courses/{course_id}/settings/full-config")
async def full_config_export(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Export complete course configuration as a single JSON file.

    Includes: course metadata, all settings, enabled_checks, check_configs,
    built-in checks with weights/configs, custom checks with provenance,
    and weekly deadlines.
    """
    course = await db.get(Course, course_id)
    if not course or not course.settings:
        return JSONResponse({"error": "Course not found"}, status_code=404)
    if not await _can_manage_course(course, _auth, db):
        return JSONResponse({"error": "Access denied"}, status_code=403)

    cs = course.settings
    enabled = set(cs.enabled_checks or [])
    check_cfgs: dict[str, dict[str, Any]] = cs.check_configs or {}

    # -- Built-in checks --
    builtin_checks: list[dict[str, Any]] = []
    for _, code, label in CHECK_DEFS:
        weight_field = _R_CHECK_WEIGHT_FIELDS.get(code, "")
        weight = getattr(cs, weight_field, 0.0) if weight_field else 0.0
        cfg = check_cfgs.get(code, {})
        entry: dict[str, Any] = {
            "check_code": code,
            "name": cfg.get("_name", label),
            "description": cfg.get(
                "_description",
                _R_CHECK_DESCRIPTIONS.get(code, ""),
            ),
            "category": cfg.get(
                "_category",
                _R_CHECK_CATEGORIES.get(code, "custom"),
            ),
            "weight": round(weight, 4),
            "is_active": code in enabled,
        }
        params_cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
        if params_cfg:
            entry["check_config"] = params_cfg
        builtin_checks.append(entry)

    # -- Custom checks --
    from app.models.custom_check import CustomCheck

    stmt = (
        select(CustomCheck)
        .where(CustomCheck.course_id == course_id)
        .order_by(CustomCheck.sort_order, CustomCheck.check_code)
    )
    result = await db.execute(stmt)
    customs = result.scalars().all()
    custom_checks: list[dict[str, Any]] = [
        {
            "check_code": cc.check_code,
            "name": cc.name,
            "description": cc.description or "",
            "category": cc.category,
            "evaluation_rule": cc.evaluation_rule,
            "weight": round(cc.weight, 4),
            "is_active": cc.is_active,
            "sort_order": cc.sort_order,
            "created_by": cc.created_by,
        }
        for cc in customs
    ]

    # -- Load teacher usernames from CourseMembership for export --
    from app.models.course_membership import CourseMembership as _ExpCM
    from app.models.user import User as _ExpUser

    _exp_instr_stmt = (
        select(_ExpUser.username)
        .join(_ExpCM, _ExpCM.user_id == _ExpUser.id)
        .where(
            _ExpCM.course_id == course.id,
            _ExpCM.role.in_(("owner", "teacher")),
        )
    )
    _exp_instr_rows = await db.execute(_exp_instr_stmt)
    _exported_teachers = sorted(u for (u,) in _exp_instr_rows.all() if u)
    _exported_patterns = resolve_patterns(cs)

    # -- Build config object --
    config: dict[str, Any] = {
        "$schema": "gitpulse/full-config/v2",
        "exported_at": datetime.now(UTC).isoformat(),
        "source_course": {
            "code": course.code,
            "academic_year": course.academic_year,
            "semester": course.semester,
        },
        "course": {
            "code": course.code,
            "name": course.name,
            "academic_year": course.academic_year,
            "semester": course.semester,
            "description": course.description or "",
            "is_active": course.is_active,
            "teacher_usernames": _exported_teachers,
        },
        "settings": {
            # Emitted from the resolver, not the raw columns: patterns now live
            # in check_configs (exported below) and a course edited since the
            # move would otherwise export stale column values. Older importers
            # still read these keys, so both shapes stay in the file.
            "branch_pattern": _exported_patterns.branch_pattern,
            "mr_template_required_sections": _exported_patterns.required_sections,
            "test_file_patterns": _exported_patterns.test_file_patterns,
            "enabled_checks": cs.enabled_checks or [],
            "check_configs": cs.check_configs or {},
            "min_reviews_per_mr": cs.min_reviews_per_mr,
            "min_review_word_count": cs.min_review_word_count,
            "min_distinct_mrs_reviewed": cs.min_distinct_mrs_reviewed,
            "green_threshold": cs.green_threshold,
            "yellow_threshold": cs.yellow_threshold,
            "mr_creation_deadline": (
                cs.mr_creation_deadline.isoformat() if cs.mr_creation_deadline else None
            ),
            "merge_deadline": (cs.merge_deadline.isoformat() if cs.merge_deadline else None),
            "semester_start_date": (
                cs.semester_start_date.isoformat() if cs.semester_start_date else None
            ),
            "semester_end_date": (
                cs.semester_end_date.isoformat() if cs.semester_end_date else None
            ),
            "skip_auto_archive": bool(getattr(cs, "skip_auto_archive", False)),
            "gitlab_group_path": cs.gitlab_group_path,
            "llm_course_type": cs.llm_course_type or "default",
            "llm_resource_urls": cs.llm_resource_urls or [],
            "llm_custom_prompt": cs.llm_custom_prompt or "",
        },
        "builtin_checks": builtin_checks,
        "custom_checks": custom_checks,
        "weekly_deadlines": cs.weekly_deadlines or [],
    }
    # The classroom assistant's tool settings - never its bot or token.
    assistant = await assistant_account.assistant_for(db, course_id)
    if assistant is not None:
        config["assistant"] = assistant_account.tools_config(assistant)

    content = json_module.dumps(config, indent=2, ensure_ascii=False)
    filename = f"full-config-{course.code}-{course.academic_year}.json"

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": content_disposition_attachment(filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


async def _enrich_course_teachers(db: DbSession, course_id: uuid.UUID) -> None:
    """The course's owners and teachers, with their avatar and name from GitLab."""
    try:
        from app.api.course_import import _enrich_teacher_users
        from app.models.course_membership import CourseMembership as _EnrCM
        from app.models.user import User as _EnrUser

        _t_stmt = (
            select(_EnrUser.username)
            .join(_EnrCM, _EnrCM.user_id == _EnrUser.id)
            .where(
                _EnrCM.course_id == course_id,
                _EnrCM.role.in_(("owner", "teacher")),
            )
        )
        _t_names = [u for (u,) in (await db.execute(_t_stmt)).all() if u]
        if _t_names:
            await _enrich_teacher_users(db, _t_names)
    except Exception:
        logger.debug("teacher_enrich_full_config_failed", exc_info=True)


@router.post("/courses/{course_id}/settings/full-config")
async def full_config_import(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Import a full course configuration from a single JSON file.

    Applies all configuration aspects at once.  Each top-level key is
    optional - only sections present in the JSON are applied.
    Sections: course, settings, builtin_checks, custom_checks,
    weekly_deadlines.
    """
    course = await db.get(Course, course_id)
    if not course or not course.settings:
        return JSONResponse({"error": "Course not found"}, status_code=404)
    if not await _can_manage_course(course, _auth, db):
        return JSONResponse({"error": "Access denied"}, status_code=403)

    # Archived courses are read-only - same rule the settings-save endpoint
    # applies. Exporting the config stays allowed; importing one does not.
    if not course.is_active:
        return JSONResponse(
            {"error": "This course is archived and is read-only. Reactivate it to make changes."},
            status_code=409,
        )

    try:
        raw_json = await read_config_text(request)
    except UnicodeDecodeError as exc:
        return JSONResponse({"error": f"Invalid JSON: {exc}"}, status_code=400)
    config = parse_config_json(raw_json)
    if isinstance(config, JSONResponse):
        return config

    errors: list[str] = []
    applied: list[str] = []
    cs = course.settings
    await apply_course_section(db, course, config, errors, applied)
    if "course" in applied and config.get("course", {}).get("teacher_usernames"):
        await _enrich_course_teachers(db, course_id)
    await apply_config_sections(db, cs, course_id, config, errors, applied)
    if "builtin_checks" in applied or "settings" in applied:
        warning = await check_weight_warning(db, cs, course_id)
        if warning:
            errors.append(warning)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        detail = str(exc.orig) if exc.orig else str(exc)
        if "uq_courses_code_year_semester" in detail:
            return JSONResponse(
                {"error": ("A course with the same code, year, and semester already exists")},
                status_code=409,
            )
        return JSONResponse({"error": f"Database error: {detail}"}, status_code=500)

    logger.info(
        "full_config_imported",
        course_id=str(course_id),
        sections_applied=applied,
        error_count=len(errors),
    )

    # Write audit log entry so it appears in "Follow the latest updates"
    try:
        from app.services.audit import write_audit

        await write_audit(
            db,
            action="course.update",
            actor=_auth.get("user", "system"),
            entity_type="course",
            entity_id=course_id,
            detail={
                "summary": f"Full config imported for {course.code} ({len(applied)} sections)",
                "sections": applied,
                "warnings": len(errors),
            },
        )
    except Exception:
        logger.debug("audit_log write failed during full_config_import")

    return JSONResponse(
        {
            "success": True,
            "applied": applied,
            "errors": errors,
            "message": (
                f"Configuration applied ({len(applied)} sections)"
                + (f" with {len(errors)} warnings" if errors else "")
            ),
        }
    )

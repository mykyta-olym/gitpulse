"""Full course-configuration import/apply logic.

Extracted from ``course_settings.py`` so the route module owns only HTTP
handling while this module owns the single responsibility of validating and
applying an imported configuration document (the full config sections) to a
``Course`` / ``CourseSettings`` aggregate.

This module must never import from ``course_settings`` (the route module
imports *from here*); doing so would create a circular import.
"""

import json
import re
import secrets as _sec
import uuid
from contextlib import suppress
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from fastapi import Request, Response
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy import func as sa_func
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.api.dashboard._helpers import (
    _DEFAULT_GREEN_THRESHOLD,
    _DEFAULT_YELLOW_THRESHOLD,
    _MAX_CONFIG_IMPORT_BYTES,
    _R_CHECK_WEIGHT_FIELDS,
    CHECK_DEFS,
    logger,
)
from app.config import get_settings
from app.models.course import Course
from app.services.assistant import account as assistant_account
from app.utils.academic_period import normalize_academic_year, normalize_semester
from app.utils.constants import (
    DEFAULT_CUSTOM_CHECK_WEIGHT,
    DEFAULT_MR_TEMPLATE_SECTIONS,
    DEFAULT_TEST_FILE_PATTERNS,
)
from app.utils.semester import (
    SemesterDateError,
    validate_semester_window,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# -- Truncation / cardinality limits --
_MAX_COURSE_CODE_LEN = 20
_MAX_COURSE_NAME_LEN = 200
_MAX_ACADEMIC_YEAR_LEN = 10
_MAX_DESCRIPTION_LEN = 2000
_MAX_LIST_ENTRIES = 100
_MAX_CHECK_ENTRIES = 20
_MAX_CHECKS = 50
_MAX_WEEKLY_ENTRIES = 52
_MAX_LABEL_LEN = 100
_MAX_EXPECTED_CHECKS = 30
_MAX_JSON_NESTING_DEPTH = 20

# -- Full Course Configuration Import / Export --

_VALID_CATEGORIES = {"issue", "mr", "review", "ci", "commit", "custom"}
_VALID_RULE_TYPES = {"count", "field_check", "ratio", "word_count", "avg_word_count"}


def _check_json_depth(obj: object, max_depth: int = _MAX_JSON_NESTING_DEPTH) -> bool:
    """Return True if *obj* nesting depth is within *max_depth* (iterative)."""
    stack: list[tuple[object, int]] = [(obj, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            return False
        if isinstance(current, dict):
            stack.extend((v, depth + 1) for v in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return True


# -- Private helper functions --


async def read_config_text(request: Request) -> str:
    """The posted configuration: a JSON body, or a form's ``config_json`` field.

    ``request.body()`` returns the body whether or not the CSRF check read it
    first. The import into an existing course looked for a body cached by
    that check instead - and the check reads no body when the token comes in
    the X-CSRF-Token header, which is how the page sends it - so every import
    from the Settings page answered "No configuration provided".
    """
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.body()
        return body.decode("utf-8") if body else ""
    form = await request.form()
    return str(form.get("config_json", ""))


def parse_config_json(raw_json: str) -> dict[str, Any] | JSONResponse:
    """A posted course configuration as a dict, or the 4xx answer to it.

    Both imports - into an existing course and creating one - take the same
    file and validate it the same way; the import into an existing course
    skipped the nesting-depth limit.
    """
    try:
        if len(raw_json.encode("utf-8")) > _MAX_CONFIG_IMPORT_BYTES:
            return JSONResponse(
                {"error": "Configuration file too large (max 2 MB)"},
                status_code=413,
            )
        if not raw_json.strip():
            return JSONResponse({"error": "No configuration provided"}, status_code=400)
        config = json.loads(raw_json)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return JSONResponse({"error": f"Invalid JSON: {exc}"}, status_code=400)
    if not isinstance(config, dict):
        return JSONResponse({"error": "Configuration must be a JSON object"}, status_code=400)
    if not _check_json_depth(config):
        return JSONResponse(
            {"error": f"JSON nesting too deep (max {_MAX_JSON_NESTING_DEPTH} levels)"},
            status_code=400,
        )
    # Auto-tag $schema if missing (export always includes it, but manual configs may not)
    if not config.get("$schema"):
        config["$schema"] = "gitpulse/full-config/v2"
    return config


async def apply_course_section(
    db: "AsyncSession",
    course: Course,
    config: dict[str, Any],
    errors: list[str],
    applied: list[str],
) -> None:
    """The config's ``course`` section: metadata and the teacher roster."""
    course_meta = config.get("course")
    if not isinstance(course_meta, dict):
        return
    _apply_course_metadata(course, course.id, db, course_meta, errors)
    applied.append("course")
    if "teacher_usernames" in course_meta:
        await _sync_teacher_memberships(db, course.id, course_meta["teacher_usernames"], errors)


async def apply_config_sections(
    db: "AsyncSession",
    cs: Any,
    course_id: uuid.UUID,
    config: dict[str, Any],
    errors: list[str],
    applied: list[str],
) -> None:
    """The config's settings, built-in checks, custom checks, weekly
    deadlines and the assistant's tools - each only when present."""
    settings_data = config.get("settings")
    if isinstance(settings_data, dict):
        _apply_settings_from_config(cs, settings_data, errors)
        applied.append("settings")

    builtin_list = config.get("builtin_checks")
    if isinstance(builtin_list, list):
        _apply_builtin_checks_from_config(cs, builtin_list, errors)
        applied.append("builtin_checks")

    custom_list = config.get("custom_checks")
    if isinstance(custom_list, list):
        await _apply_custom_checks_from_config(db, course_id, custom_list, errors)
        applied.append("custom_checks")

    weekly = config.get("weekly_deadlines")
    if isinstance(weekly, list):
        _apply_weekly_deadlines(cs, weekly, errors)
        applied.append("weekly_deadlines")

    # Skipped while the feature is off, as the import preview says.
    assistant_data = config.get("assistant")
    if isinstance(assistant_data, dict) and get_settings().feature_classroom_assistant:
        bad = await assistant_account.import_tools(db, course_id, assistant_data)
        if bad:
            errors.append("assistant: invalid " + ", ".join(bad) + " - not applied")
        else:
            applied.append("assistant")


async def check_weight_warning(db: "AsyncSession", cs: Any, course_id: uuid.UUID) -> str | None:
    """A warning when the active checks - built-in and custom - weigh nothing
    together, so no score can be computed (any positive total is fine: the
    score divides by it)."""
    from app.models.custom_check import CustomCheck as CCheck

    enabled = set(cs.enabled_checks or [])
    total_w = 0.0
    for _, code, _ in CHECK_DEFS:
        wf = _R_CHECK_WEIGHT_FIELDS.get(code, "") if code in enabled else ""
        if wf:
            total_w += getattr(cs, wf, 0.0)
    stmt = select(sa_func.coalesce(sa_func.sum(CCheck.weight), 0.0)).where(
        CCheck.course_id == course_id, CCheck.is_active.is_(True)
    )
    total_w += float((await db.execute(stmt)).scalar() or 0.0)
    if total_w <= 0:
        return "The active checks have no weight, so no score can be computed."
    return None


async def _import_config_create_course_impl(
    request: Request,
    db: "AsyncSession",
    *,
    actor: str = "system",
    background_tasks: BackgroundTasks | None = None,
) -> Response:
    """Implementation extracted for cleaner error handling."""
    try:
        raw_json = await read_config_text(request)
    except UnicodeDecodeError as exc:
        return JSONResponse({"error": f"Invalid JSON: {exc}"}, status_code=400)
    config = parse_config_json(raw_json)
    if isinstance(config, JSONResponse):
        return config

    found = await _find_or_create_course(db, config, actor)
    if isinstance(found, JSONResponse):
        return found
    course, cs, created = found

    errors: list[str] = []
    applied: list[str] = []
    await apply_course_section(db, course, config, errors, applied)
    await _ensure_admin_users(db)
    await apply_config_sections(db, cs, course.id, config, errors, applied)
    errors.extend(await _dangling_check_references(db, cs, course.id, config))
    if "builtin_checks" in applied or "settings" in applied:
        warning = await check_weight_warning(db, cs, course.id)
        if warning:
            errors.append(warning)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        detail = str(exc.orig) if exc.orig else str(exc)
        return JSONResponse({"error": f"Database error: {detail}"}, status_code=500)

    logger.info(
        "config_import_with_create",
        course_id=str(course.id),
        created=created,
        sections_applied=applied,
        error_count=len(errors),
    )

    # Write audit log entry so it appears in "Follow the latest updates"
    try:
        from app.services.audit import write_audit

        action = "course.create" if created else "course.update"
        await write_audit(
            db,
            action=action,
            actor=actor,
            entity_type="course",
            entity_id=course.id,
            detail={
                "summary": (
                    f"{'Course created' if created else 'Course updated'}"
                    f" from JSON import: {course.code}"
                    f" ({len(applied)} sections)"
                ),
                "sections": applied,
                "warnings": len(errors),
            },
        )
    except Exception:
        logger.debug("audit_log write failed during config_import_create")

    if not created:
        await _refresh_after_import(db, course)
    enrich_started, enrich_total = (
        await _start_enrichment(db, background_tasks, course)
        if background_tasks is not None
        else (False, 0)
    )

    return JSONResponse(
        {
            "success": True,
            "course_id": str(course.id),
            "created": created,
            "applied": applied,
            "errors": errors,
            "enrich_started": enrich_started,
            "enrich_total": enrich_total,
            "message": (
                ("Course created" if created else "Course updated")
                + f" - {len(applied)} sections applied"
                + (f" with {len(errors)} warnings" if errors else "")
            ),
        }
    )


async def _find_or_create_course(
    db: "AsyncSession", config: dict[str, Any], actor: str
) -> tuple[Course, Any, bool] | JSONResponse:
    """The course the config names (by code, year and semester) with its
    settings - created, with the importing user as owner, when it is new."""
    course_meta = config.get("course") or config.get("source_course") or {}
    code = str(course_meta.get("code", "")).strip()[:_MAX_COURSE_CODE_LEN]
    name = str(course_meta.get("name", code)).strip()[:_MAX_COURSE_NAME_LEN]
    raw_year = str(course_meta.get("academic_year", "")).strip()[:_MAX_ACADEMIC_YEAR_LEN]
    raw_semester = str(course_meta.get("semester", "winter"))

    if not code:
        return JSONResponse(
            {"error": "course.code is required to create or find the course"},
            status_code=400,
        )
    if not raw_year:
        return JSONResponse(
            {"error": "course.academic_year is required"},
            status_code=400,
        )
    # The one spelling every other way in accepts - a config that created a
    # "2026/2028" course would put it in no period at all.
    try:
        academic_year = normalize_academic_year(raw_year)
        semester = normalize_semester(raw_semester)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    from app.models.course_settings import CourseSettings

    stmt = select(Course).where(
        Course.code == code,
        Course.academic_year == academic_year,
        Course.semester == semester,
    )
    course = (await db.execute(stmt)).scalar_one_or_none()
    if course is not None:
        if course.settings:
            return course, course.settings, False
        cs = CourseSettings(course_id=course.id)
        cs.course = course  # link via relationship so course.settings is set
        db.add(cs)
        await db.flush()
        return course, cs, False

    course = Course(
        code=code,
        name=name,
        description=str(course_meta.get("description", ""))[:_MAX_DESCRIPTION_LEN],
        academic_year=academic_year,
        semester=semester,
    )
    db.add(course)
    await db.flush()

    cs = CourseSettings(
        course_id=course.id,
        mr_template_required_sections=list(DEFAULT_MR_TEMPLATE_SECTIONS),
        test_file_patterns=list(DEFAULT_TEST_FILE_PATTERNS),
    )
    cs.course = course  # link via relationship so course.settings is set
    db.add(cs)
    await db.flush()

    # Auto-add the creating user as course owner
    try:
        from app.models.user import User
        from app.security.course_roles import set_course_membership

        creator_stmt = (
            select(User)
            .where(
                User.is_active.is_(True),
                (User.gitlab_username == actor) | (User.username == actor),
            )
            .limit(1)
        )
        creator = (await db.execute(creator_stmt)).scalar_one_or_none()
        if creator:
            await set_course_membership(db, creator.id, course.id, "owner")
    except Exception:
        logger.warning("auto_owner_import_failed", course_id=str(course.id), exc_info=True)

    logger.info(
        "course_created_from_import",
        course_id=str(course.id),
        code=code,
    )
    return course, cs, True


async def _ensure_admin_users(db: "AsyncSession") -> None:
    """A User with the admin role for each of GITLAB_ADMIN_USERNAMES.

    Teacher details (avatar, name, email) are NOT fetched here: the GitLab
    group import that follows fetches the members anyway, and skipping the
    sequential API calls cut ~10 s from a config import.
    """
    try:
        from app.models.user import User as _IUser

        for _admin_uname in get_settings().gitlab_admin_usernames or []:
            _au = (_admin_uname or "").strip()
            if not _au:
                continue
            _au_stmt = (
                select(_IUser)
                .where((_IUser.gitlab_username == _au) | (_IUser.username == _au))
                .limit(1)
            )
            _existing_admin = (await db.execute(_au_stmt)).scalar_one_or_none()
            if _existing_admin:
                if _existing_admin.role != "admin":
                    _existing_admin.role = "admin"
            else:
                db.add(
                    _IUser(
                        username=_au,
                        gitlab_username=_au,
                        email="PRIVATE",
                        password_hash=f"gitlab-import:{_sec.token_hex(32)}",
                        role="admin",
                        is_active=True,
                    )
                )
        await db.flush()
    except Exception:
        logger.warning("admin_enrich_config_import_failed", exc_info=True)


async def _dangling_check_references(
    db: "AsyncSession", cs: Any, course_id: uuid.UUID, config: dict[str, Any]
) -> list[str]:
    """Warnings for weekly deadlines that expect a check the course lacks."""
    weekly = config.get("weekly_deadlines")
    if not isinstance(weekly, list):
        return []
    from app.models.custom_check import CustomCheck as CCheck

    known: set[str] = set(cs.enabled_checks or [])
    cc_res = await db.execute(select(CCheck.check_code).where(CCheck.course_id == course_id))
    known.update(row[0] for row in cc_res.all())
    warnings = []
    for wk_entry in weekly:
        if not isinstance(wk_entry, dict):
            continue
        for ec in wk_entry.get("expected_checks", []):
            if str(ec) not in known:
                warnings.append(
                    f"weekly_deadlines[week {wk_entry.get('week', '?')}]: "
                    f"references unknown check '{ec}'"
                )
    return warnings


async def _refresh_after_import(db: "AsyncSession", course: Course) -> None:
    """Recompute every active group's metrics and drop the course's cached
    pages, so the new configuration - and semester scope - show at once."""
    try:
        from app.models.team import Team as _Team
        from app.services.events import enqueue_metrics_refresh

        t_stmt = select(_Team.id).where(_Team.course_id == course.id, _Team.is_active.is_(True))
        for (tid,) in (await db.execute(t_stmt)).all():
            enqueue_metrics_refresh(str(tid))
    except Exception:
        logger.debug("auto_metrics_after_config_import skipped (non-critical)")
    try:
        from app.services.page_cache import invalidate_cascade as _inv_cache

        _inv_cache(course_id=course.id)
    except Exception:
        logger.debug(
            "page_cache_invalidate_failed",
            course_id=str(course.id),
            exc_info=True,
        )


async def _start_enrichment(
    db: "AsyncSession", background_tasks: BackgroundTasks, course: Course
) -> tuple[bool, int]:
    """Start the GitLab enrichment of users still missing their details;
    whether it started and for how many."""
    enrich_total = 0
    try:
        from app.api.dashboard._helpers import (
            _clear_enrichment_status,
            _set_enrichment_status,
            _try_start_enrichment,
        )
        from app.models.background_job import BackgroundJob
        from app.models.user import User as _EUser

        settings = get_settings()
        if not (settings.gitlab_api_token and _try_start_enrichment()):
            return False, 0
        e_stmt = select(_EUser).where(
            or_(
                _EUser.email.is_(None),
                _EUser.email == "PRIVATE",
                _EUser.full_name.is_(None),
                _EUser.gitlab_user_id.is_(None),
            ),
        )
        enrich_total = len(list((await db.execute(e_stmt)).scalars().all()))
        if enrich_total == 0:
            _clear_enrichment_status()
            return False, 0
        _set_enrichment_status(
            status="running",
            message="Starting GitLab enrichment...",
            total=enrich_total,
            processed=0,
        )
        bg_job = BackgroundJob(
            job_type="enrichment",
            status="running",
            started_at=datetime.now(UTC),
        )
        db.add(bg_job)
        await db.flush()
        job_id = str(bg_job.id)
        await db.commit()

        from app.api.dashboard.admin.enrichment import _run_gitlab_enrichment

        background_tasks.add_task(
            _run_gitlab_enrichment,
            settings.gitlab_url,
            settings.gitlab_api_token,
            settings.gitlab_api_timeout_seconds,
            job_id,
        )
        logger.info(
            "auto_enrich_after_import",
            total=enrich_total,
            course_id=str(course.id),
        )
        return True, enrich_total
    except Exception:
        logger.debug("auto_enrich_after_import_failed", exc_info=True)
        return False, enrich_total


def _apply_course_metadata(
    course: Any,
    course_id: uuid.UUID,
    db: Any,
    data: dict[str, Any],
    errors: list[str],
) -> None:
    """Apply course-level metadata with validation."""
    if data.get("code"):
        course.code = str(data["code"]).strip()[:_MAX_COURSE_CODE_LEN]
    if data.get("name"):
        course.name = str(data["name"]).strip()[:_MAX_COURSE_NAME_LEN]
    # A value that is not a period is reported and NOT written. It used to be
    # reported and written anyway (the year), or silently turned into winter
    # (the semester) - either way the course left the period it was in.
    if data.get("academic_year"):
        try:
            course.academic_year = normalize_academic_year(str(data["academic_year"]))
        except ValueError as exc:
            errors.append(str(exc))
    if data.get("semester"):
        try:
            course.semester = normalize_semester(str(data["semester"]))
        except ValueError as exc:
            errors.append(str(exc))
    if data.get("description") is not None:
        course.description = str(data["description"])[:_MAX_DESCRIPTION_LEN]
    if "is_active" in data:
        course.is_active = bool(data["is_active"])


async def _sync_teacher_memberships(
    db: "AsyncSession",
    course_id: uuid.UUID,
    teacher_usernames: Any,
    errors: list[str],
) -> None:
    """Sync teacher_usernames from config JSON to CourseMembership rows.

    Behaviour:
    - Creates User records for teacher usernames that don't exist yet
      (pre-provisioned with role='teacher', same pattern as admin
      user creation from GITLAB_ADMIN_USERNAMES).
    - Creates new CourseMembership(role='teacher') for users without a
      membership for this course.
    - Upgrades existing 'student' memberships to 'teacher'.
    - Never downgrades: existing 'owner' or 'teacher' memberships are
      left as-is.
    - Never removes memberships.
    - Elevates User.role from 'student' to 'teacher' when the user is
      not role_locked.
    - Skips usernames that belong to admin users (admins are managed
      separately via GITLAB_ADMIN_USERNAMES).
    """
    if not isinstance(teacher_usernames, list):
        errors.append("teacher_usernames must be an array of strings")
        return

    from app.models.course_membership import COURSE_ROLE_WEIGHT, CourseMembership
    from app.models.user import User

    _app_cfg = get_settings()
    _admin_set = {
        (a or "").strip().lower()
        for a in (_app_cfg.gitlab_admin_usernames or [])
        if (a or "").strip()
    }

    added = 0
    upgraded = 0
    user_role_elevated = 0
    users_created = 0

    for raw in teacher_usernames:
        username = str(raw).strip() if raw else ""
        if not username:
            continue

        # Skip admin usernames - they are managed separately
        if username.lower() in _admin_set:
            continue

        # -- Find or create user --
        user_stmt = (
            select(User)
            .where(
                or_(
                    User.gitlab_username == username,
                    User.username == username,
                )
            )
            .limit(1)
        )
        user = (await db.execute(user_stmt)).scalar_one_or_none()
        if not user:
            from app.services.gitlab_import.service import is_bot_user

            user = User(
                username=username,
                gitlab_username=username,
                email="PRIVATE",
                password_hash=f"gitlab-import:{_sec.token_hex(32)}",
                role="teacher",
                is_active=True,
                is_bot=is_bot_user(username),
            )
            db.add(user)
            await db.flush()
            users_created += 1

        # -- Elevate User.role if needed (student -> teacher) --
        if user.role == "student" and not user.role_locked:
            user.role = "teacher"
            user_role_elevated += 1

        # -- Check existing CourseMembership --
        existing_stmt = select(CourseMembership).where(
            CourseMembership.user_id == user.id,
            CourseMembership.course_id == course_id,
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()

        if existing:
            # Upgrade student -> teacher; never downgrade owner/teacher
            if existing.role == "student" and COURSE_ROLE_WEIGHT.get(
                "teacher", 0
            ) > COURSE_ROLE_WEIGHT.get(existing.role, 0):
                existing.role = "teacher"
                upgraded += 1
            # owner or teacher - leave as-is
            continue

        # -- Create new membership --
        db.add(
            CourseMembership(
                user_id=user.id,
                course_id=course_id,
                role="teacher",
            )
        )
        added += 1

    if added or upgraded or user_role_elevated or users_created:
        await db.flush()
        logger.info(
            "teacher_memberships_synced",
            course_id=str(course_id),
            added=added,
            upgraded=upgraded,
            user_role_elevated=user_role_elevated,
            users_created=users_created,
        )


def _apply_settings_from_config(
    cs: Any,
    data: dict[str, Any],
    errors: list[str],
) -> None:
    """Apply settings fields from config dict with full validation."""
    # -- String fields --
    str_fields = {"branch_pattern": 200, "gitlab_group_path": 300}
    for field, maxlen in str_fields.items():
        if field in data and data[field] is not None:
            setattr(cs, field, str(data[field])[:maxlen])

    # -- Validate branch_pattern as regex --
    bp = data.get("branch_pattern")
    if bp:
        try:
            re.compile(str(bp))
        except re.error as exc:
            errors.append(f"Invalid branch_pattern regex: {exc}")

    # -- Array of strings --
    array_fields = (
        "mr_template_required_sections",
        "test_file_patterns",
        "enabled_checks",
    )
    for field in array_fields:
        val = data.get(field)
        if isinstance(val, list):
            setattr(cs, field, [str(x).strip() for x in val[:_MAX_LIST_ENTRIES] if x])

    # -- Integer fields (clamped 1..100) --
    int_fields = (
        "min_reviews_per_mr",
        "min_review_word_count",
        "min_distinct_mrs_reviewed",
    )
    for field in int_fields:
        val = data.get(field)
        if val is not None:
            try:
                ival = max(1, min(int(val), 100))
                setattr(cs, field, ival)
                if int(val) != ival:
                    errors.append(f"{field} clamped to {ival} (original: {val})")
            except (ValueError, TypeError):
                errors.append(f"{field}: invalid integer value '{val}'")

    # -- Float fields 0.0-1.0 --
    float01_fields = ("green_threshold", "yellow_threshold")
    for field in float01_fields:
        val = data.get(field)
        if val is not None:
            try:
                fval = max(0.0, min(float(val), 1.0))
                setattr(cs, field, fval)
            except (ValueError, TypeError):
                errors.append(f"{field}: invalid float value '{val}'")

    # -- Threshold sanity check --
    g = getattr(cs, "green_threshold", _DEFAULT_GREEN_THRESHOLD)
    y = getattr(cs, "yellow_threshold", _DEFAULT_YELLOW_THRESHOLD)
    if g <= y:
        errors.append(f"green_threshold ({g:.2f}) must be > yellow_threshold ({y:.2f})")

    # -- Date field --
    # We parse into locals first, run cross-field validation (range + ordering)
    # and only commit to the model if every guard passes. This prevents a
    # half-applied window where `start` lands but `end` is rejected.
    _parsed_start: date | None = cs.semester_start_date
    _parsed_end: date | None = cs.semester_end_date
    _start_provided = False
    _end_provided = False

    ssd = data.get("semester_start_date")
    if ssd:
        _start_provided = True
        try:
            _parsed_start = date.fromisoformat(str(ssd)[:10])
        except ValueError:
            errors.append(f"Invalid semester_start_date: '{ssd}' (expected YYYY-MM-DD)")
            _parsed_start = cs.semester_start_date
    elif ssd is None and "semester_start_date" in data:
        _start_provided = True
        _parsed_start = None

    sed = data.get("semester_end_date")
    if sed:
        _end_provided = True
        try:
            _parsed_end = date.fromisoformat(str(sed)[:10])
        except ValueError:
            errors.append(f"Invalid semester_end_date: '{sed}' (expected YYYY-MM-DD)")
            _parsed_end = cs.semester_end_date
    elif sed is None and "semester_end_date" in data:
        _end_provided = True
        _parsed_end = None

    if _start_provided or _end_provided:
        try:
            validate_semester_window(
                _parsed_start,
                _parsed_end,
                stored_start=cs.semester_start_date,
                stored_end=cs.semester_end_date,
            )
        except SemesterDateError as exc:
            errors.append(str(exc))
        else:
            if _start_provided:
                cs.semester_start_date = _parsed_start
            if _end_provided:
                cs.semester_end_date = _parsed_end

    # -- Boolean: skip_auto_archive --
    if "skip_auto_archive" in data:
        cs.skip_auto_archive = bool(data.get("skip_auto_archive"))

    # -- Datetime fields --
    for field in ("mr_creation_deadline", "merge_deadline"):
        val = data.get(field)
        if val:
            try:
                setattr(cs, field, datetime.fromisoformat(str(val)))
            except ValueError:
                errors.append(f"Invalid {field}: '{val}' (expected ISO 8601 datetime)")
        elif val is None and field in data:
            setattr(cs, field, None)

    # -- JSONB fields (direct) --
    jsonb_fields = ("check_configs",)
    for field in jsonb_fields:
        if field in data and isinstance(data[field], dict):
            setattr(cs, field, data[field])

    # -- LLM configuration --
    llm_ct = data.get("llm_course_type")
    if isinstance(llm_ct, str) and llm_ct.lower() in ("default", "zsi", "devops"):
        cs.llm_course_type = llm_ct.lower()

    llm_prompt = data.get("llm_custom_prompt")
    if isinstance(llm_prompt, str):
        cs.llm_custom_prompt = llm_prompt.strip() or None

    llm_urls = data.get("llm_resource_urls")
    if isinstance(llm_urls, list):
        sanitized: list[dict[str, str]] = []
        for entry in llm_urls:
            if isinstance(entry, dict):
                url = str(entry.get("url", "")).strip()[:500]
                label = str(entry.get("label", "")).strip()[:100]
                if url and url.startswith(("https://", "http://")):
                    sanitized.append({"url": url, "label": label})
        cs.llm_resource_urls = sanitized


def _apply_builtin_checks_from_config(
    cs: Any,
    checks: list[dict[str, Any]],
    errors: list[str],
) -> None:
    """Apply built-in check weights, configs, and enabled state."""
    enabled: list[str] = list(cs.enabled_checks or [])
    check_configs: dict[str, dict[str, Any]] = dict(cs.check_configs or {})

    valid_codes = {code for _, code, _ in CHECK_DEFS}

    for entry in checks[:_MAX_CHECK_ENTRIES]:
        code = str(entry.get("check_code", "")).strip()
        if not code.startswith("R") or code not in valid_codes:
            if code:
                errors.append(f"Unknown built-in check code: '{code}'")
            continue

        # -- Weight --
        weight_field = _R_CHECK_WEIGHT_FIELDS.get(code)
        if weight_field:
            w = entry.get("weight")
            if w is not None:
                try:
                    wval = max(0.0, min(float(w), 1.0))
                    setattr(cs, weight_field, wval)
                except (ValueError, TypeError):
                    errors.append(f"{code}: invalid weight '{w}'")

        # -- Active state --
        is_active = entry.get("is_active")
        if is_active is True and code not in enabled:
            enabled.append(code)
        elif is_active is False and code in enabled:
            enabled.remove(code)

        # -- Per-check config --
        cfg = entry.get("check_config")
        if isinstance(cfg, dict):
            existing = check_configs.get(code, {})
            existing.update(cfg)
            check_configs[code] = existing

        # -- Name / description / category overrides --
        name = entry.get("name")
        desc = entry.get("description")
        cat = entry.get("category")
        if name:
            check_configs.setdefault(code, {})["_name"] = str(name)[:_MAX_COURSE_NAME_LEN]
        if desc is not None:
            check_configs.setdefault(code, {})["_description"] = str(desc)
        if cat:
            cat_s = str(cat)
            if cat_s not in _VALID_CATEGORIES:
                errors.append(f"{code}: invalid category '{cat_s}'")
            else:
                check_configs.setdefault(code, {})["_category"] = cat_s

    cs.enabled_checks = enabled
    cs.check_configs = check_configs


async def _apply_custom_checks_from_config(
    db: Any,
    course_id: uuid.UUID,
    checks: list[dict[str, Any]],
    errors: list[str],
) -> None:
    """Create or update custom checks from config."""
    from app.models.custom_check import CustomCheck

    if len(checks) > 50:
        errors.append("Too many custom checks (max 50)")
        checks = checks[:_MAX_CHECKS]

    imported_codes: set[str] = set()

    for entry in checks:
        code = str(entry.get("check_code", "")).strip()
        name = str(entry.get("name", "")).strip()
        if not code or not name:
            errors.append(f"Custom check missing code or name: '{code}'")
            continue

        # -- Code format validation --
        if not code.startswith("C") or not code[1:].isdigit():
            errors.append(
                f"Invalid custom check code: '{code}' (must be C followed by digits, e.g. C01)"
            )
            continue

        if code in imported_codes:
            errors.append(f"Duplicate custom check code: '{code}'")
            continue
        imported_codes.add(code)

        # -- Category validation --
        category = str(entry.get("category", "custom"))
        if category not in _VALID_CATEGORIES:
            errors.append(f"{code}: invalid category '{category}' - defaulting to 'custom'")
            category = "custom"

        # -- Evaluation rule validation --
        rule = entry.get("evaluation_rule", {})
        if not isinstance(rule, dict):
            rule = {}
            errors.append(f"{code}: evaluation_rule must be an object")

        rule_type = rule.get("type", "")
        if rule_type and rule_type not in _VALID_RULE_TYPES:
            errors.append(
                f"{code}: invalid rule type '{rule_type}'"
                f" (valid: {', '.join(sorted(_VALID_RULE_TYPES))})"
            )
            continue

        # -- Deep rule validation --
        if rule_type == "count":
            for req in ("entity", "operator", "threshold"):
                if req not in rule:
                    errors.append(f"{code}: count rule missing '{req}'")
        elif rule_type == "field_check":
            for req in ("entity", "field", "expected"):
                if req not in rule:
                    errors.append(f"{code}: field_check rule missing '{req}'")
            if rule.get("match_mode") and rule["match_mode"] not in ("any", "all"):
                errors.append(f"{code}: field_check match_mode must be 'any' or 'all'")
        elif rule_type == "ratio":
            _ratio_req = (
                "entity",
                "numerator_filter",
                "denominator_filter",
                "operator",
                "threshold",
            )
            for req in _ratio_req:
                if req not in rule:
                    errors.append(f"{code}: ratio rule missing '{req}'")
        elif rule_type in ("word_count", "avg_word_count"):
            if "entity" not in rule:
                errors.append(f"{code}: {rule_type} rule missing 'entity'")
            if "min_avg_words" not in rule and "threshold" not in rule:
                errors.append(f"{code}: {rule_type} rule missing 'min_avg_words' or 'threshold'")

        # -- Weight --
        weight = DEFAULT_CUSTOM_CHECK_WEIGHT
        try:
            weight = max(0.0, min(float(entry.get("weight", DEFAULT_CUSTOM_CHECK_WEIGHT)), 1.0))
        except (ValueError, TypeError):
            errors.append(f"{code}: invalid weight")

        # -- Sort order --
        sort_order = 0
        with suppress(ValueError, TypeError):
            sort_order = int(entry.get("sort_order", 0))

        # -- Provenance --
        created_by = str(entry.get("created_by", "import"))
        if created_by not in ("manual", "import", "llm"):
            created_by = "import"

        # -- Upsert --
        stmt = select(CustomCheck).where(
            CustomCheck.course_id == course_id,
            CustomCheck.check_code == code,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = name[:_MAX_COURSE_NAME_LEN]
            existing.description = str(entry.get("description", ""))
            existing.category = category
            existing.evaluation_rule = rule
            existing.weight = weight
            existing.is_active = bool(entry.get("is_active", True))
            existing.sort_order = sort_order
        else:
            new_check = CustomCheck(
                course_id=course_id,
                check_code=code,
                name=name[:_MAX_COURSE_NAME_LEN],
                description=str(entry.get("description", "")),
                category=category,
                evaluation_rule=rule,
                weight=weight,
                is_active=bool(entry.get("is_active", True)),
                sort_order=sort_order,
                created_by=created_by,
            )
            db.add(new_check)


def _apply_weekly_deadlines(
    cs: Any,
    weekly: list[Any],
    errors: list[str],
) -> None:
    """Validate and apply weekly deadlines."""
    validated: list[dict[str, Any]] = []
    seen_weeks: set[int] = set()

    for i, item in enumerate(weekly[:_MAX_WEEKLY_ENTRIES]):
        if not isinstance(item, dict):
            errors.append(f"weekly_deadlines[{i}]: not an object")
            continue

        week = item.get("week")
        if week is None or not isinstance(week, int | float):
            errors.append(f"weekly_deadlines[{i}]: missing or invalid 'week' (must be integer)")
            continue
        week = int(week)

        if week < 1 or week > 52:
            errors.append(f"weekly_deadlines[{i}]: week {week} out of range (1-52)")
            continue

        if week in seen_weeks:
            errors.append(f"weekly_deadlines[{i}]: duplicate week {week}")
            continue
        seen_weeks.add(week)

        label = str(item.get("label", f"Week {week}"))
        expected = item.get("expected_checks", [])
        if not isinstance(expected, list):
            errors.append(f"weekly_deadlines[{i}]: expected_checks must be an array")
            expected = []

        entry: dict[str, Any] = {
            "week": week,
            "label": label[:_MAX_LABEL_LEN],
            "expected_checks": [str(c) for c in expected[:_MAX_EXPECTED_CHECKS]],
        }
        # Preserve optional per-week deadlines (validate ISO format)
        for dl_key in ("mr_deadline", "merge_deadline"):
            if dl_key in item:
                dl_val = item[dl_key]
                if dl_val is not None:
                    try:
                        datetime.fromisoformat(str(dl_val))
                        entry[dl_key] = str(dl_val)
                    except (ValueError, TypeError):
                        errors.append(
                            f"weekly_deadlines[{i}].{dl_key}: invalid datetime '{dl_val}'"
                        )
                else:
                    entry[dl_key] = None

        validated.append(entry)

    cs.weekly_deadlines = sorted(validated, key=lambda x: x["week"])

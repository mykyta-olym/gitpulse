"""Check configuration and custom check management routes."""

import json
import json as json_module
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dashboard._access import _can_manage_course
from app.api.dashboard._helpers import (
    _MAX_CONFIG_IMPORT_BYTES,
    _R_CHECK_CATEGORIES,
    _R_CHECK_CONFIGURABLE,
    _R_CHECK_DESCRIPTIONS,
    _R_CHECK_WEIGHT_FIELDS,
    CHECK_DEFS,
    CHECK_DEFS_MAP,
    _templates,
    logger,
)
from app.api.dashboard.courses.settings_config import check_weight_warning
from app.dependencies import (
    CSRFCheck,
    DbSession,
    RateLimitDep,
    TeacherAuth,
)
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.schemas.custom_check import CheckUpdate
from app.services.course_checks import build_checks_payload, save_check
from app.utils.constants import DEFAULT_CUSTOM_CHECK_WEIGHT
from app.utils.http_headers import content_disposition_attachment

router = APIRouter()

_MAX_IMPORT_ITEMS = 100  # safety cap
_VALID_CATEGORIES = {"issue", "mr", "review", "ci", "commit", "custom"}


async def _load_course(
    course_id: uuid.UUID,
    _auth: dict[str, str],
    db: DbSession,
    *,
    require_settings: bool = True,
    mask_denial: bool = False,
) -> Course | JSONResponse:
    """Load a course and authorize the caller, or return the refusal.

    Nine endpoints in this module opened with the same four lines, in three
    variants that had drifted apart: four required ``course.settings`` before
    answering 404, three did not, and two answered 404 "Check not found" for a
    denial instead of 403. Same question, three answers - and the kind of
    difference that turns into an information leak when someone copies the
    wrong one. The variants are arguments now.

    ``mask_denial`` is the deliberate one: the per-check endpoints refuse to
    confirm that a check exists in a course the caller cannot see, so a denial
    and a miss are indistinguishable from outside.
    """
    course = await db.get(Course, course_id)
    miss = JSONResponse(
        {"error": "Check not found" if mask_denial else "Course not found"},
        status_code=404,
    )
    if not course or (require_settings and not course.settings):
        return miss
    if not await _can_manage_course(course, _auth, db):
        return miss if mask_denial else JSONResponse({"error": "Access denied"}, status_code=403)
    return course


async def _load_course_settings(
    course_id: uuid.UUID,
    _auth: dict[str, str],
    db: DbSession,
) -> tuple[Course, "CourseSettings"] | JSONResponse:
    """``_load_course`` for the endpoints that go straight on to read settings.

    ``_load_course(require_settings=True)`` already refused the request when
    there are none, but that guarantee is not in its return type, so every one
    of those callers still had to re-handle a ``None`` the helper had made
    impossible. Handing back both makes the guarantee the type.
    """
    loaded = await _load_course(course_id, _auth, db)
    if isinstance(loaded, JSONResponse):
        return loaded
    settings = loaded.settings
    if settings is None:  # pragma: no cover - _load_course already refused this
        return JSONResponse({"error": "Course not found"}, status_code=404)
    return loaded, settings


def _archived_block(course: "Course") -> JSONResponse | None:
    """409 when a course is archived, so its checks stay read-only.

    The settings-save endpoint already rejects archived courses; the check
    mutation endpoints did not, which left an archived course's checks editable
    through the API even though the UI dims the buttons. Reactivation is a
    separate endpoint, so this never blocks bringing a course back.
    """
    if not course.is_active:
        return JSONResponse(
            {"error": "This course is archived and is read-only. Reactivate it to make changes."},
            status_code=409,
        )
    return None


@router.get("/courses/{course_id}/checks")
async def list_all_checks(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Return a unified view of all checks (built-in R01-R13 + custom) for a course.

    Each item has a consistent shape:
    {
        "check_code": "R01",
        "name": "Issue Assigned",
        "description": "...",
        "category": "issue",
        "weight": 0.08,
        "is_active": true,
        "is_builtin": true,
        "check_config": {"min_issues": 1},
        "configurable_params": [...],
        "evaluation_rule": null,
        "sort_order": 0,
        "created_by": "system",
        "id": null
    }
    """
    _loaded = await _load_course(course_id, _auth, db)
    if isinstance(_loaded, JSONResponse):
        return _loaded

    return JSONResponse(await build_checks_payload(_loaded, db))


@router.get("/courses/{course_id}/checks/export")
async def export_checks_config(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Export all check configurations as a portable JSON file.

    The format is self-contained and can be imported into another course.
    """
    _loaded = await _load_course_settings(course_id, _auth, db)
    if isinstance(_loaded, JSONResponse):
        return _loaded
    course, cs = _loaded

    enabled = set(cs.enabled_checks or [])
    check_cfgs: dict[str, dict[str, Any]] = cs.check_configs or {}

    builtin_checks: list[dict[str, Any]] = []
    for _, code, label in CHECK_DEFS:
        weight_field = _R_CHECK_WEIGHT_FIELDS.get(code, "")
        weight = getattr(cs, weight_field, 0.0) if weight_field else 0.0
        cfg = check_cfgs.get(code, {})
        entry: dict[str, Any] = {
            "check_code": code,
            "name": cfg.get("_name", label),
            "description": cfg.get("_description", _R_CHECK_DESCRIPTIONS.get(code, "")),
            "category": cfg.get("_category", _R_CHECK_CATEGORIES.get(code, "custom")),
            "weight": round(weight, 4),
            "is_active": code in enabled,
        }
        # Only include non-default config params
        params_cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
        if params_cfg:
            entry["check_config"] = params_cfg
        builtin_checks.append(entry)

    # Custom checks
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
        }
        for cc in customs
    ]

    config = {
        "$schema": "gitpulse/check-config/v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "source_course": {
            "code": course.code,
            "academic_year": course.academic_year,
            "semester": course.semester,
        },
        "builtin_checks": builtin_checks,
        "custom_checks": custom_checks,
    }

    content = json_module.dumps(config, indent=2, ensure_ascii=False)
    filename = f"checks-{course.code}-{course.academic_year}.json"

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": content_disposition_attachment(filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


def _apply_builtin_items(cs: Any, items: list[Any], errors_list: list[str]) -> tuple[int, int]:
    """Built-in checks from an import: weight, on/off, name / description /
    category overrides (dropped when back to the default) and config keys.
    How many were applied and how many skipped."""
    applied = 0
    skipped = 0
    cfgs = dict(cs.check_configs or {})
    enabled = list(dict.fromkeys(cs.enabled_checks or []))

    for item in items:
        if not isinstance(item, dict):
            skipped += 1
            continue
        code = item.get("check_code", "")
        if code not in _R_CHECK_WEIGHT_FIELDS:
            skipped += 1
            continue

        weight_field = _R_CHECK_WEIGHT_FIELDS[code]

        # Weight
        try:
            w = float(item.get("weight", 0))
            if 0.0 <= w <= 1.0:
                setattr(cs, weight_field, round(w, 4))
        except (ValueError, TypeError):
            errors_list.append(f"{code}: invalid weight")

        # Active state
        is_active = item.get("is_active")
        if isinstance(is_active, bool):
            if is_active and code not in enabled:
                enabled.append(code)
            elif not is_active and code in enabled:
                enabled.remove(code)

        # Metadata overrides
        existing = dict(cfgs.get(code, {}))
        default_name = CHECK_DEFS_MAP.get(code, "")
        default_desc = _R_CHECK_DESCRIPTIONS.get(code, "")
        default_cat = _R_CHECK_CATEGORIES.get(code, "custom")

        name_val = str(item.get("name", "")).strip()[:200]
        if name_val and name_val != default_name:
            existing["_name"] = name_val
        else:
            existing.pop("_name", None)

        desc_val = str(item.get("description", "")).strip()[:500]
        if desc_val != default_desc:
            existing["_description"] = desc_val
        else:
            existing.pop("_description", None)

        cat_val = str(item.get("category", "")).strip()
        if cat_val in _VALID_CATEGORIES and cat_val != default_cat:
            existing["_category"] = cat_val
        else:
            existing.pop("_category", None)

        # Config params
        item_cfg = item.get("check_config")
        if isinstance(item_cfg, dict):
            valid_keys = {p["key"] for p in _R_CHECK_CONFIGURABLE.get(code, [])}
            for k in list(existing):
                if not k.startswith("_") and k in valid_keys:
                    del existing[k]
            for k, v in item_cfg.items():
                if k in valid_keys:
                    existing[k] = v

        if existing:
            cfgs[code] = existing
        else:
            cfgs.pop(code, None)
        applied += 1

    cs.enabled_checks = enabled
    cs.check_configs = cfgs
    return applied, skipped


async def _apply_custom_items(
    db: DbSession, course_id: uuid.UUID, items: list[Any], errors_list: list[str]
) -> tuple[int, int]:
    """Custom checks from an import: an existing code is updated, anything
    else becomes the next free C-code. How many were applied and skipped."""
    applied = 0
    skipped = 0
    from app.models.custom_check import CustomCheck

    # Get existing custom checks for this course
    stmt = select(CustomCheck).where(CustomCheck.course_id == course_id)
    result = await db.execute(stmt)
    existing_customs = {cc.check_code: cc for cc in result.scalars().all()}

    # Determine next available check code
    max_code = 0
    for cc_code in existing_customs:
        if cc_code.startswith("C"):
            with suppress(ValueError):
                max_code = max(max_code, int(cc_code[1:]))

    valid_rule_types = {"count", "field_check", "ratio", "word_count", "avg_word_count"}
    valid_entities = {
        "issue",
        "merge_request",
        "pipeline",
        "review",
        "note",
        "response",
    }

    _seen_codes: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            skipped += 1
            continue
        cc_code = item.get("check_code", "")
        name = str(item.get("name", "")).strip()[:200]
        if not name:
            skipped += 1
            continue

        # Detect duplicate check_codes within the same import batch
        _dedup_key = cc_code or name
        if _dedup_key in _seen_codes:
            errors_list.append(f"Duplicate check '{_dedup_key}' in import - skipped")
            skipped += 1
            continue
        _seen_codes.add(_dedup_key)

        try:
            w = float(item.get("weight", DEFAULT_CUSTOM_CHECK_WEIGHT))
            w = max(0.0, min(1.0, w))
        except (ValueError, TypeError):
            w = DEFAULT_CUSTOM_CHECK_WEIGHT

        cat = item.get("category", "custom")
        raw_active = item.get("is_active")

        # Validate evaluation_rule structure
        eval_rule = item.get("evaluation_rule")
        if not isinstance(eval_rule, dict):
            eval_rule = {}
        if eval_rule:
            rule_type = eval_rule.get("type", "count")
            if rule_type not in valid_rule_types:
                errors_list.append(f"{name}: unknown rule type '{rule_type}'")
                eval_rule = {}
            entity = eval_rule.get("entity")
            if entity and entity not in valid_entities:
                errors_list.append(f"{name}: unknown entity '{entity}'")
                eval_rule = {}

        if cc_code in existing_customs:
            # Update existing
            cc = existing_customs[cc_code]
            cc.name = name
            cc.description = str(item.get("description", "")).strip()[:500]
            cc.category = cat if cat in _VALID_CATEGORIES else "custom"
            cc.evaluation_rule = eval_rule
            cc.weight = round(w, 4)
            cc.is_active = raw_active if isinstance(raw_active, bool) else True
        else:
            # Create new
            max_code += 1
            new_code = f"C{max_code:02d}"
            cc = CustomCheck(
                course_id=course_id,
                check_code=new_code,
                name=name,
                description=str(item.get("description", "")).strip()[:500],
                category=cat if cat in _VALID_CATEGORIES else "custom",
                evaluation_rule=eval_rule,
                weight=round(w, 4),
                is_active=raw_active if isinstance(raw_active, bool) else True,
                sort_order=max_code,
                created_by="import",
            )
            db.add(cc)
        applied += 1
    return applied, skipped


@router.post("/courses/{course_id}/checks/import")
async def import_checks_config(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Import check configurations from a JSON file.

    Accepts the same format as the export endpoint.
    Updates built-in check weights, enabled state, and config.
    Creates or updates custom checks.
    """
    _loaded = await _load_course_settings(course_id, _auth, db)
    if isinstance(_loaded, JSONResponse):
        return _loaded
    course, cs = _loaded
    if (_blk := _archived_block(course)) is not None:
        return _blk

    # -- Size guard --
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_CONFIG_IMPORT_BYTES:
        return JSONResponse({"error": "Request body too large (max 2 MB)"}, status_code=413)

    try:
        raw = await request.body()
        if len(raw) > _MAX_CONFIG_IMPORT_BYTES:
            return JSONResponse({"error": "Request body too large (max 2 MB)"}, status_code=413)
        body = json.loads(raw)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=422)
    except Exception:
        logger.warning("config_import_body_read_error", exc_info=True)
        return JSONResponse({"error": "Invalid request"}, status_code=422)

    if not isinstance(body, dict):
        return JSONResponse({"error": "Expected a JSON object"}, status_code=422)

    # Auto-tag $schema if absent (manual configs may omit it)
    if not body.get("$schema"):
        body["$schema"] = "gitpulse/check-config/v1"

    applied = 0
    skipped = 0
    errors_list: list[str] = []

    builtin_items = body.get("builtin_checks", [])
    if not isinstance(builtin_items, list):
        return JSONResponse({"error": "builtin_checks must be a list"}, status_code=422)
    if len(builtin_items) > _MAX_IMPORT_ITEMS:
        err = f"Too many builtin_checks (max {_MAX_IMPORT_ITEMS})"
        return JSONResponse({"error": err}, status_code=422)
    done, passed = _apply_builtin_items(cs, builtin_items, errors_list)
    applied += done
    skipped += passed

    custom_items = body.get("custom_checks", [])
    if not isinstance(custom_items, list):
        return JSONResponse({"error": "custom_checks must be a list"}, status_code=422)
    if len(custom_items) > _MAX_IMPORT_ITEMS:
        err = f"Too many custom_checks (max {_MAX_IMPORT_ITEMS})"
        return JSONResponse({"error": err}, status_code=422)
    if custom_items:
        done, passed = await _apply_custom_items(db, course_id, custom_items, errors_list)
        applied += done
        skipped += passed

    warning = await check_weight_warning(db, cs, course_id)
    if warning:
        errors_list.append(warning)

    await db.flush()
    logger.info(
        "checks_config_imported",
        course_id=str(course_id),
        applied=applied,
        skipped=skipped,
        errors=len(errors_list),
    )

    # Write audit log entry for activity feed
    try:
        from app.services.audit import write_audit

        await write_audit(
            db,
            action="course.update",
            actor=_auth.get("user", "system"),
            entity_type="course",
            entity_id=course_id,
            detail={
                "summary": (
                    f"Check config imported for {course.code}"
                    f" ({applied} applied, {skipped} skipped)"
                ),
            },
        )
    except Exception:
        logger.debug("audit_log write failed during checks_config_import")

    return JSONResponse(
        {
            "ok": True,
            "applied": applied,
            "skipped": skipped,
            "errors": errors_list,
        }
    )


@router.put("/courses/{course_id}/checks/{check_code}")
async def update_check(
    course_id: uuid.UUID,
    check_code: str,
    data: CheckUpdate,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    course = await _load_course(course_id, _auth, db)
    if isinstance(course, JSONResponse):
        return course
    if (blocked := _archived_block(course)) is not None:
        return blocked
    return JSONResponse(
        await save_check(db, course, check_code, data, actor=str(_auth.get("user_id", "")))
    )


# -- Custom Checks CRUD --


@router.get("/courses/{course_id}/custom-checks")
async def list_custom_checks(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Return all custom checks for a course as JSON."""
    _loaded = await _load_course(course_id, _auth, db, require_settings=False)
    if isinstance(_loaded, JSONResponse):
        return _loaded

    from app.models.custom_check import CustomCheck

    stmt = (
        select(CustomCheck)
        .where(CustomCheck.course_id == course_id)
        .order_by(CustomCheck.sort_order, CustomCheck.check_code)
    )
    result = await db.execute(stmt)
    checks = result.scalars().all()
    return JSONResponse(
        [
            {
                "id": str(c.id),
                "check_code": c.check_code,
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "evaluation_rule": c.evaluation_rule,
                "weight": c.weight,
                "is_active": c.is_active,
                "sort_order": c.sort_order,
                "created_by": c.created_by,
            }
            for c in checks
        ]
    )


@router.post("/courses/{course_id}/custom-checks")
async def create_custom_check(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Create a new custom check for a course."""

    from app.models.custom_check import CustomCheck
    from app.schemas.custom_check import CustomCheckCreate

    _loaded = await _load_course(course_id, _auth, db, require_settings=False)
    if isinstance(_loaded, JSONResponse):
        return _loaded
    course = _loaded
    if (_blk := _archived_block(course)) is not None:
        return _blk

    raw = await request.json()
    try:
        payload = CustomCheckCreate.model_validate(raw)
    except ValidationError as exc:
        return JSONResponse({"error": exc.errors()[0]["msg"]}, status_code=422)

    # Auto-assign next check code if not provided
    check_code = payload.check_code.strip()
    if not check_code:
        existing_stmt = (
            select(CustomCheck.check_code)
            .where(CustomCheck.course_id == course_id)
            .order_by(CustomCheck.check_code.desc())
        )
        existing_result = await db.execute(existing_stmt)
        existing_codes = list(existing_result.scalars().all())
        max_num = 0
        for code in existing_codes:
            if code.startswith("C") and code[1:].isdigit():
                max_num = max(max_num, int(code[1:]))
        check_code = f"C{max_num + 1:02d}"

    # Auto-assign next sort_order if not explicitly set
    sort_order = payload.sort_order
    if sort_order == 0:
        max_sort_stmt = select(sa_func.coalesce(sa_func.max(CustomCheck.sort_order), 0)).where(
            CustomCheck.course_id == course_id
        )
        max_sort_result = await db.execute(max_sort_stmt)
        sort_order = (max_sort_result.scalar() or 0) + 1

    cc = CustomCheck(
        course_id=course_id,
        check_code=check_code,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        evaluation_rule=payload.evaluation_rule,
        weight=payload.weight,
        is_active=payload.is_active,
        sort_order=sort_order,
        created_by=payload.created_by,
    )
    db.add(cc)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            {"error": f"Check code '{check_code}' already exists in this course"},
            status_code=409,
        )

    logger.info("custom_check_created", course_id=str(course_id), check_code=check_code)

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="custom_check_created",
        actor=str(_auth.get("user_id", "")),
        entity_type="custom_check",
        entity_id=cc.id,
        detail={"course_id": str(course_id), "check_code": check_code, "name": cc.name},
    )

    return JSONResponse(
        {"id": str(cc.id), "check_code": cc.check_code, "name": cc.name},
        status_code=201,
    )


@router.put("/courses/{course_id}/custom-checks/{check_id}")
async def update_custom_check(
    course_id: uuid.UUID,
    check_id: uuid.UUID,
    data: CheckUpdate,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    from app.models.custom_check import CustomCheck

    course = await _load_course(course_id, _auth, db, require_settings=False, mask_denial=True)
    if isinstance(course, JSONResponse):
        return course
    if (blocked := _archived_block(course)) is not None:
        return blocked
    check = await db.get(CustomCheck, check_id)
    if check is None or check.course_id != course_id:
        return JSONResponse({"error": "Check not found"}, status_code=404)
    return JSONResponse(
        await save_check(db, course, check.check_code, data, actor=str(_auth.get("user_id", "")))
    )


@router.delete("/courses/{course_id}/custom-checks/{check_id}")
async def delete_custom_check(
    course_id: uuid.UUID,
    check_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Delete a custom check."""
    from app.models.custom_check import CustomCheck

    _loaded = await _load_course(course_id, _auth, db, require_settings=False, mask_denial=True)
    if isinstance(_loaded, JSONResponse):
        return _loaded
    course = _loaded
    if (_blk := _archived_block(course)) is not None:
        return _blk

    cc = await db.get(CustomCheck, check_id)
    if not cc or cc.course_id != course_id:
        return JSONResponse({"error": "Check not found"}, status_code=404)

    await db.delete(cc)
    await db.flush()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="custom_check_deleted",
        actor=str(_auth.get("user_id", "")),
        entity_type="custom_check",
        entity_id=check_id,
        detail={"course_id": str(course_id), "check_code": cc.check_code, "name": cc.name},
    )

    logger.info("custom_check_deleted", check_id=str(check_id))
    return JSONResponse({"ok": True})


@router.post("/courses/{course_id}/custom-checks/generate")
async def generate_custom_checks_llm(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Use LLM to generate custom check definitions based on course description.

    Request body::

        {
            "prompt": "Generate checks for DevOps best practices",
            "count": 5
        }

    Returns a list of suggested check definitions (not auto-saved).
    """
    _loaded = await _load_course(course_id, _auth, db, require_settings=False)
    if isinstance(_loaded, JSONResponse):
        return _loaded
    course = _loaded
    # Generating checks starts a paid LLM call against a read-only course.
    if (_blk := _archived_block(course)) is not None:
        return _blk

    body = await request.json()
    user_prompt = str(body.get("prompt", ""))[:2000]
    try:
        count = max(1, min(int(body.get("count", 5)), 20))
    except (ValueError, TypeError):
        return JSONResponse({"error": "count must be an integer"}, status_code=422)

    # Load existing custom checks to avoid duplicates
    from app.models.custom_check import CustomCheck

    existing_stmt = select(CustomCheck).where(CustomCheck.course_id == course_id)
    existing_result = await db.execute(existing_stmt)
    existing_checks = list(existing_result.scalars().all())
    existing_codes = {cc.check_code for cc in existing_checks}
    existing_names = [cc.name for cc in existing_checks]

    # Find next code number
    max_num = 0
    for code in existing_codes:
        if code.startswith("C") and code[1:].isdigit():
            max_num = max(max_num, int(code[1:]))

    # Build LLM prompt
    from app.config import get_settings as _get_llm_settings

    settings = _get_llm_settings()
    if not settings.llm_analysis_enabled:
        return JSONResponse({"error": "LLM suggestions feature is disabled"}, status_code=503)

    course_desc = course.description or course.name
    system_prompt = (
        "You are an expert DevOps and software engineering educator. "
        "Generate compliance check definitions for a university course.\n\n"
        f"Course: {course.name}\nDescription: {course_desc}\n\n"
        "Each check must evaluate student GitLab activity. "
        "Return a JSON array of check objects.\n\n"
        "Available entity types: issue, merge_request, pipeline, review, note, response\n"
        "Available rule types:\n"
        '- count: {"type":"count","entity":"...","filter":{"field":"value"},'
        '"operator":">=","threshold":N,"partial_scoring":false}\n'
        '- field_check: {"type":"field_check","entity":"...","field":"..field_name..",'
        '"expected":true,"match_mode":"any"}\n'
        '- ratio: {"type":"ratio","entity":"...","numerator_filter":{},'
        '"denominator_filter":{},"operator":">=","threshold":0.8,"partial_scoring":true}\n'
        '- word_count: {"type":"word_count","entity":"note","min_avg_words":30}\n\n'
        "Available entity fields:\n"
        "- issue: state, assignee_id\n"
        "- merge_request: state, has_test_changes, has_issue_link, "
        "branch_naming_ok, template_compliant, source_branch\n"
        "- pipeline: status, has_test_job, ref\n"
        "- review: is_meaningful, word_count\n"
        "- note: word_count, is_resolvable, is_resolved, discussion_id, "
        "contains_commit_ref\n\n"
        "Each object in the array MUST have these fields:\n"
        '  "name": "Human-readable name",\n'
        '  "description": "What this check evaluates",\n'
        '  "category": "issue|mr|review|ci|commit|custom",\n'
        '  "evaluation_rule": {... rule object ...},\n'
        '  "weight": 0.05\n\n'
    )
    if existing_names:
        system_prompt += (
            "Already existing checks (avoid duplicates): " + ", ".join(existing_names) + "\n\n"
        )
    if user_prompt:
        system_prompt += f"Teacher's additional requirements: {user_prompt}\n\n"

    system_prompt += f"Generate exactly {count} new checks. Return ONLY a JSON array."

    # Call LLM
    try:
        from app.services.llm.service import LLMService

        llm_svc = LLMService(settings)
        if not settings.llm_api_key:
            return JSONResponse(
                {"error": "LLM API key is not configured. Set LLM_API_KEY in environment."},
                status_code=400,
            )
        llm_resp = await llm_svc._call_llm(system_prompt, "Generate custom checks")

        # Extract text from LLM response
        raw_response = ""
        if hasattr(llm_resp, "choices") and llm_resp.choices:
            raw_response = llm_resp.choices[0].message.content or ""
        elif hasattr(llm_resp, "text"):
            raw_response = llm_resp.text or ""

        if not raw_response:
            return JSONResponse({"error": "LLM returned empty response"}, status_code=500)

        # Parse JSON from response (strip markdown fences if present)
        text = raw_response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.removesuffix("```")
            text = text.strip()

        suggestions = json.loads(text)
        # json_object mode may wrap the array in an object - unwrap it
        if isinstance(suggestions, dict):
            for _k in ("suggestions", "checks", "items", "results", "data"):
                if isinstance(suggestions.get(_k), list):
                    suggestions = suggestions[_k]
                    break
            else:
                # Fall back to the first list-typed value
                for _v in suggestions.values():
                    if isinstance(_v, list):
                        suggestions = _v
                        break
        if not isinstance(suggestions, list):
            return JSONResponse({"error": "LLM response is not a JSON array"}, status_code=500)

        # Validate, de-duplicate, and assign check codes
        valid_categories = {"issue", "mr", "review", "ci", "commit", "custom"}
        existing_names_lower = {n.lower() for n in existing_names}
        cleaned: list[dict[str, Any]] = []
        code_num = max_num
        for s in suggestions:
            # Skip malformed suggestions
            if not isinstance(s, dict) or not s.get("name"):
                continue
            # Skip duplicates against existing checks
            if s["name"].lower() in existing_names_lower:
                continue
            # Apply defaults for optional fields
            s.setdefault("description", "")
            try:
                s["weight"] = max(
                    0.0, min(float(s.get("weight", DEFAULT_CUSTOM_CHECK_WEIGHT)), 1.0)
                )
            except (ValueError, TypeError):
                s["weight"] = DEFAULT_CUSTOM_CHECK_WEIGHT
            if s.get("category") not in valid_categories:
                s["category"] = "custom"
            rule = s.get("evaluation_rule", {})
            valid_rule_types = {"count", "field_check", "ratio", "word_count", "avg_word_count"}
            if not isinstance(rule, dict) or (
                rule.get("type") and rule["type"] not in valid_rule_types
            ):
                s["evaluation_rule"] = {}
            else:
                s["evaluation_rule"] = rule
            code_num += 1
            s["check_code"] = f"C{code_num:02d}"
            s["created_by"] = "llm"
            existing_names_lower.add(s["name"].lower())
            cleaned.append(s)

        return JSONResponse({"suggestions": cleaned})

    except json.JSONDecodeError:
        return JSONResponse(
            {"error": "Could not parse LLM response as JSON. Try again or adjust the prompt."},
            status_code=500,
        )
    except Exception as exc:
        logger.exception("LLM check generation failed")
        err_msg = str(exc) or "Unknown error"
        return JSONResponse(
            {"error": f"LLM generation failed: {err_msg}"},
            status_code=500,
        )


@router.get("/courses/{course_id}/checks/table")
async def checks_table(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
) -> Response:
    """Refresh the same rows rendered in the initial settings page."""
    course = await _load_course(course_id, _auth, db)
    if isinstance(course, JSONResponse):
        return course
    return _templates(request).TemplateResponse(
        request,
        "partials/course_settings/_checks_response.html",
        {
            "course": course,
            "checks_first_json": await build_checks_payload(course, db),
        },
    )

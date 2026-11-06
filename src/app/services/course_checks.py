"""Check edits shared by individual endpoints and atomic course saves."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import check_optimistic_lock, raise_not_found, raise_unprocessable
from app.compliance.check_registry import (
    CATEGORIES,
    CHECK_DEFS,
    CHECK_DEFS_MAP,
    CONFIGURABLE,
    DESCRIPTIONS,
    WEIGHT_FIELDS,
)
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.schemas.custom_check import CheckUpdate


async def prepare_check_updates(
    db: AsyncSession, course: Course, edits: dict[str, CheckUpdate]
) -> dict[str, CourseSettings | CustomCheck]:
    """Resolve and lock every target before any edit or audit can flush."""
    customs = (
        (
            await db.scalars(
                select(CustomCheck).where(
                    CustomCheck.course_id == course.id, CustomCheck.check_code.in_(edits)
                )
            )
        ).all()
        if edits
        else []
    )
    targets: dict[str, CourseSettings | CustomCheck] = {c.check_code: c for c in customs}
    for code, edit in edits.items():
        if code in WEIGHT_FIELDS and course.settings is not None:
            targets[code] = course.settings
        target = targets.get(code)
        if target is None:
            raise_not_found(f"Check {code} not found")
        check_optimistic_lock(target, edit.expected_updated_at, label=f"Check {code}")
        unsupported = edit.model_fields_set & (
            {"evaluation_rule", "sort_order"}
            if isinstance(target, CourseSettings)
            else {"check_config"}
        )
        if unsupported:
            raise_unprocessable(f"Unsupported fields for {code}: {', '.join(sorted(unsupported))}")
    return targets


def apply_check_update(
    target: CourseSettings | CustomCheck, code: str, edit: CheckUpdate
) -> dict[str, Any]:
    """Apply a validated edit without committing, flushing or publishing."""
    fields = edit.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
    if isinstance(target, CustomCheck):
        for key, value in fields.items():
            setattr(target, key, value)
        return fields

    if "weight" in fields:
        setattr(target, WEIGHT_FIELDS[code], round(fields["weight"], 4))
    if "is_active" in fields:
        enabled = list(dict.fromkeys(target.enabled_checks or []))
        if fields["is_active"] and code not in enabled:
            enabled.append(code)
        elif not fields["is_active"] and code in enabled:
            enabled.remove(code)
        target.enabled_checks = enabled

    configs = dict(target.check_configs or {})
    config = dict(configs.get(code, {}))
    for field, default in (
        ("name", CHECK_DEFS_MAP.get(code, "")),
        ("description", DESCRIPTIONS.get(code, "")),
        ("category", CATEGORIES.get(code, "custom")),
    ):
        if field not in fields:
            continue
        value = fields[field].strip()
        if value != default and (value or field == "description"):
            config["_" + field] = value
        else:
            config.pop("_" + field, None)
    if "check_config" in fields:
        keys = {p["key"] for p in CONFIGURABLE.get(code, [])}
        config = {k: v for k, v in config.items() if k not in keys}
        config.update({k: v for k, v in fields["check_config"].items() if k in keys})
    if config:
        configs[code] = config
    else:
        configs.pop(code, None)
    target.check_configs = configs
    return fields


async def audit_check_update(
    db: AsyncSession,
    target: CourseSettings | CustomCheck,
    code: str,
    fields: dict[str, Any],
    actor: str,
) -> None:
    from app.services.audit import write_audit

    custom = isinstance(target, CustomCheck)
    await write_audit(
        db,
        action="custom_check_updated" if custom else "check_updated",
        actor=actor,
        entity_type="custom_check" if custom else "check",
        entity_id=target.id if custom else target.course_id,
        detail={"course_id": str(target.course_id), "check_code": code, "fields": list(fields)},
    )


async def save_check(
    db: AsyncSession, course: Course, code: str, edit: CheckUpdate, *, actor: str
) -> dict[str, Any]:
    """The single-check entry point uses the same mutation and refresh lifecycle."""
    from app.services.course_settings import after_settings_update, lock_configuration

    await lock_configuration(db, course)
    target = (await prepare_check_updates(db, course, {code: edit}))[code]
    if course.settings is not None:
        course.settings.updated_at = datetime.now(UTC)
    fields = apply_check_update(target, code, edit)
    await audit_check_update(db, target, code, fields, actor)
    await db.flush()
    result = {
        "ok": True,
        "updated_at": target.updated_at.isoformat() if target.updated_at else None,
    }
    if isinstance(target, CustomCheck):
        result["id"] = str(target.id)
    if course.settings is not None:
        await after_settings_update(db, course.id, course.settings)
    return result


async def build_checks_payload(course: Course, db: AsyncSession) -> dict[str, Any]:
    """The check catalog and course overrides for HTML and JSON projections."""
    cs = course.settings
    if cs is None:
        # Callers reach this through _load_course_settings, which already
        # refuses a course without settings; the Settings page can call it
        # directly, so answer with an empty view rather than raising.
        return {
            "checks": [],
            "total_weight": 0.0,
            "weight_valid": False,
            "presets": [],
            "pattern_presets": [],
        }
    enabled = set(cs.enabled_checks or [])
    check_cfgs: dict[str, dict[str, Any]] = cs.check_configs or {}

    checks: list[dict[str, Any]] = []
    settings_updated_at = cs.updated_at.isoformat() if cs.updated_at else None

    # Built-in R01-R13
    for _, code, label in CHECK_DEFS:
        weight_field = WEIGHT_FIELDS.get(code, "")
        weight = getattr(cs, weight_field, 0.0) if weight_field else 0.0
        cfg = check_cfgs.get(code, {})
        checks.append(
            {
                "id": None,
                "check_code": code,
                "name": cfg.get("_name", label),
                "description": cfg.get("_description", DESCRIPTIONS.get(code, "")),
                "category": cfg.get("_category", CATEGORIES.get(code, "custom")),
                "weight": round(weight, 4),
                "is_active": code in enabled,
                "is_builtin": True,
                "check_config": {k: v for k, v in cfg.items() if not k.startswith("_")},
                "configurable_params": CONFIGURABLE.get(code, []),
                "evaluation_rule": None,
                "sort_order": int(code[1:]),
                "created_by": "system",
                "updated_at": settings_updated_at,
            }
        )

    # Custom checks
    from app.models.custom_check import CustomCheck

    stmt = (
        select(CustomCheck)
        .where(CustomCheck.course_id == course.id)
        .order_by(CustomCheck.sort_order, CustomCheck.check_code)
    )
    result = await db.execute(stmt)
    customs = result.scalars().all()
    for cc in customs:
        checks.append(
            {
                "id": str(cc.id),
                "check_code": cc.check_code,
                "name": cc.name,
                "description": cc.description,
                "category": cc.category,
                "weight": round(cc.weight, 4),
                "is_active": cc.is_active,
                "is_builtin": False,
                "check_config": {},
                "configurable_params": [],
                "evaluation_rule": cc.evaluation_rule,
                "sort_order": 100 + cc.sort_order,
                "created_by": cc.created_by,
                "updated_at": cc.updated_at.isoformat() if cc.updated_at else None,
            }
        )

    # Match the shared table's initial Code ascending order before JavaScript runs.
    checks.sort(key=lambda check: check["check_code"])
    total_weight = round(sum(c["weight"] for c in checks if c["is_active"]), 4)
    # Scores divide by the active total, so any positive total is valid; only
    # active checks that weigh nothing leave no score to compute.
    weight_valid = total_weight > 0

    # Server-driven weight presets (dynamic over the live built-in check set,
    # incl. R13 and any future R-code) - the client applies these, it no
    # longer hard-codes weight distributions.
    from app.compliance.presets import build_pattern_presets, build_weight_presets

    return {
        "checks": checks,
        "total_weight": total_weight,
        "weight_valid": weight_valid,
        "presets": build_weight_presets(checks),
        # Convention presets carry the strict-mode toggles alongside the
        # patterns, so applying one cannot leave a regex that scores nothing.
        "pattern_presets": build_pattern_presets(),
    }

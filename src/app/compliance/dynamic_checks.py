"""Dynamic check evaluator - runs teacher-defined custom checks at runtime.

This module interprets the ``evaluation_rule`` JSONB stored in
:class:`~app.models.custom_check.CustomCheck` and produces
:class:`~app.compliance.types.CheckResult` instances identical to the
built-in R01-R13 checks.

Supported rule types
--------------------
- **count** - count entities matching filter, compare to threshold
- **field_check** - verify boolean/truthy field on entities (any/all mode)
- **ratio** - ratio of filtered entities to total
- **word_count** - average word count on notes/reviews

Entity types
------------
``issue``, ``merge_request``, ``pipeline``, ``review``, ``note``, ``response``

All entity data comes from :class:`~app.compliance.types.StudentContext` which
is already populated by the main compliance engine.
"""

import logging
from collections.abc import Callable
from typing import Any

from app.compliance.types import CheckResult, StudentContext

logger = logging.getLogger(__name__)


def evaluate_custom_check(
    ctx: StudentContext,
    check_code: str,
    name: str,
    rule: dict[str, Any],
    weight: float,
) -> CheckResult:
    """Evaluate a single custom check rule against student data.

    Parameters
    ----------
    ctx : StudentContext
        Pre-built student context with issues, MRs, notes, pipelines, etc.
    check_code : str
        Check identifier, e.g. ``"C01"``.
    name : str
        Human-readable check name.
    rule : dict
        The ``evaluation_rule`` JSONB from CustomCheck.
    weight : float
        Scoring weight for this check.

    Returns
    -------
    CheckResult
        Evaluation result with pass/fail, detail, and score.
    """
    rule_type = rule.get("type", "count")

    try:
        if rule_type == "count":
            return _eval_count(ctx, check_code, name, rule, weight)
        if rule_type == "field_check":
            return _eval_field_check(ctx, check_code, name, rule, weight)
        if rule_type == "ratio":
            return _eval_ratio(ctx, check_code, name, rule, weight)
        if rule_type in ("word_count", "avg_word_count"):
            return _eval_word_count(ctx, check_code, name, rule, weight)
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail=f"Unknown rule type: {rule_type}",
            weight=weight,
            score=0.0,
        )
    except Exception:
        logger.exception("Error evaluating custom check %s", check_code)
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail="Evaluation error - check rule configuration",
            weight=weight,
            score=0.0,
        )


# -- Entity resolution --


def _get_entities(ctx: StudentContext, entity_type: str) -> list[Any]:
    """Resolve entity type to the corresponding list from StudentContext."""
    mapping: dict[str, list[Any]] = {
        "issue": ctx.issues_assigned,
        "merge_request": ctx.mrs_authored,
        "pipeline": ctx.pipelines,
        "review": ctx.reviews_given,
        "note": ctx.notes_on_own_mr,
        "response": ctx.own_responses,
    }
    result = mapping.get(entity_type)
    if result is None:
        logger.warning("Unknown entity type '%s' in custom check rule", entity_type)
        return []
    return result


def _matches_filter(entity: Any, conditions: dict[str, Any]) -> bool:
    """Check whether an entity satisfies all filter conditions.

    Conditions map field names to expected values.
    Supports equality, ``in`` (if value is a list), and ``None`` checks.
    """
    for field, expected in conditions.items():
        actual = getattr(entity, field, None)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


# -- Rule evaluators --


def _eval_count(
    ctx: StudentContext,
    check_code: str,
    name: str,
    rule: dict[str, Any],
    weight: float,
) -> CheckResult:
    """Evaluate a count-based rule.

    Rule schema::

        {
            "type": "count",
            "entity": "merge_request",
            "filter": {"state": "merged"},
            "operator": ">=",
            "threshold": 2,
            "partial_scoring": false
        }
    """
    entity_type = rule.get("entity", "merge_request")
    entities = _get_entities(ctx, entity_type)
    conditions = rule.get("filter", {})
    threshold = int(rule.get("threshold", 1))
    operator = rule.get("operator", ">=")
    partial = bool(rule.get("partial_scoring", False))

    matching = [e for e in entities if _matches_filter(e, conditions)]
    count = len(matching)

    passed = _compare(count, operator, threshold)

    if partial and not passed and threshold > 0:
        score = weight * min(count / threshold, 1.0)
    else:
        score = weight if passed else 0.0

    entity_label = entity_type.replace("_", " ")
    filter_desc = ""
    if conditions:
        filter_desc = " (" + ", ".join(f"{k}={v}" for k, v in conditions.items()) + ")"

    return CheckResult(
        check_id=check_code,
        name=name,
        passed=passed,
        detail=f"{count}/{threshold} {entity_label}(s){filter_desc}",
        weight=weight,
        score=round(score, 4),
    )


def _eval_field_check(
    ctx: StudentContext,
    check_code: str,
    name: str,
    rule: dict[str, Any],
    weight: float,
) -> CheckResult:
    """Evaluate a field-check rule (any/all mode).

    Rule schema::

        {
            "type": "field_check",
            "entity": "merge_request",
            "field": "has_test_changes",
            "expected": true,
            "match_mode": "any"
        }
    """
    entity_type = rule.get("entity", "merge_request")
    entities = _get_entities(ctx, entity_type)
    field = rule.get("field", "")
    expected = rule.get("expected", True)
    match_mode = rule.get("match_mode", "any")

    if not field:
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail="Invalid rule: 'field' is required for field_check",
            weight=weight,
            score=0.0,
        )

    if not entities:
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail=f"No {entity_type.replace('_', ' ')}(s) to evaluate",
            weight=weight,
            score=0.0,
        )

    matching = [e for e in entities if getattr(e, field, None) == expected]
    count = len(matching)
    total = len(entities)
    partial = bool(rule.get("partial_scoring", False))

    if match_mode == "all":
        passed = count == total
        detail = f"{count}/{total} {entity_type.replace('_', ' ')}(s) have {field}={expected}"
    else:
        passed = count > 0
        detail = f"{count} of {total} {entity_type.replace('_', ' ')}(s) have {field}={expected}"

    score = weight * (count / total) if partial and total > 0 else weight if passed else 0.0

    return CheckResult(
        check_id=check_code,
        name=name,
        passed=passed,
        detail=detail,
        weight=weight,
        score=score,
    )


def _eval_ratio(
    ctx: StudentContext,
    check_code: str,
    name: str,
    rule: dict[str, Any],
    weight: float,
) -> CheckResult:
    """Evaluate a ratio rule.

    Rule schema::

        {
            "type": "ratio",
            "entity": "merge_request",
            "numerator_filter": {"has_issue_link": true},
            "denominator_filter": {},
            "operator": ">=",
            "threshold": 0.8,
            "partial_scoring": true
        }
    """
    entity_type = rule.get("entity", "merge_request")
    entities = _get_entities(ctx, entity_type)
    num_filter = rule.get("numerator_filter", {})
    den_filter = rule.get("denominator_filter", {})
    threshold = float(rule.get("threshold", 0.8))
    operator = rule.get("operator", ">=")
    partial = bool(rule.get("partial_scoring", False))

    denominator = [e for e in entities if _matches_filter(e, den_filter)]
    numerator = [e for e in denominator if _matches_filter(e, num_filter)]

    if not denominator:
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail=f"No {entity_type.replace('_', ' ')}(s) to evaluate",
            weight=weight,
            score=0.0,
        )

    ratio = len(numerator) / len(denominator)
    passed = _compare(ratio, operator, threshold)

    if partial and not passed:
        score = weight * min(ratio / max(threshold, 0.01), 1.0)
    else:
        score = weight if passed else 0.0

    return CheckResult(
        check_id=check_code,
        name=name,
        passed=passed,
        detail=f"{len(numerator)}/{len(denominator)} ({ratio:.0%}) vs {threshold:.0%}",
        weight=weight,
        score=round(score, 4),
    )


def _eval_word_count(
    ctx: StudentContext,
    check_code: str,
    name: str,
    rule: dict[str, Any],
    weight: float,
) -> CheckResult:
    """Evaluate average word count on notes/reviews.

    Rule schema::

        {
            "type": "word_count",
            "entity": "note",
            "min_avg_words": 30
        }
    """
    entity_type = rule.get("entity", "note")
    entities = _get_entities(ctx, entity_type)
    min_avg = int(rule.get("min_avg_words") or rule.get("threshold", 30))

    word_counts = [getattr(e, "word_count", 0) or 0 for e in entities]
    if not word_counts:
        return CheckResult(
            check_id=check_code,
            name=name,
            passed=False,
            detail="No notes/reviews to evaluate",
            weight=weight,
            score=0.0,
        )

    avg = sum(word_counts) / len(word_counts)
    operator = rule.get("operator", ">=")
    passed = _compare(avg, operator, min_avg)

    return CheckResult(
        check_id=check_code,
        name=name,
        passed=passed,
        detail=f"Avg word count {avg:.0f} (min: {min_avg})",
        weight=weight,
        score=weight if passed else 0.0,
    )


# -- Comparison helper --


def _compare(value: float, operator: str, threshold: float) -> bool:
    """Compare a value against a threshold using the given operator."""
    ops: dict[str, Callable[[Any, Any], bool]] = {
        ">=": lambda v, t: v >= t,
        "<=": lambda v, t: v <= t,
        ">": lambda v, t: v > t,
        "<": lambda v, t: v < t,
        "==": lambda v, t: v == t,
        "!=": lambda v, t: v != t,
    }
    fn = ops.get(operator, ops[">="])
    return bool(fn(value, threshold))

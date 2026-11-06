"""Dynamic compliance weight presets, computed server-side.

A preset is a named weight distribution a teacher can apply with one click
(Balanced / Code-Review Focus / CI Focus / Minimal). These used to be a
hard-coded object in the course-settings JavaScript that enumerated only
R01-R12 - so R09/R11/R13 were silently skipped (leaving stored weights that
summed above 1.0) and a newly-added built-in check never appeared.

The presets are now derived from the *live* built-in check set the API already
assembles (which comes from ``builtin_checks.json`` + the registry, so R13 and
any future R-code flow through automatically). Weights are normalised so the
active built-in checks sum to 1.0. The client just fetches and applies them -
no scoring logic lives on the client.
"""

from typing import Any

# Category emphasis multipliers. A category absent from a preset's map uses the
# implicit base multiplier 1.0, so "balanced" (empty map) weights every check
# equally. The registry assigns each built-in check a category:
# issue / mr / review / ci / commit.
_CATEGORY_EMPHASIS: dict[str, dict[str, float]] = {
    "balanced": {},
    "review_heavy": {"review": 3.0},
    "ci_heavy": {"ci": 4.0, "commit": 1.5},
}

# "Minimal" keeps only these essential codes active (those that exist in the
# course), equally weighted; every other built-in check is set to weight 0 and
# deactivated. Codes that are not present are simply ignored.
_MINIMAL_CORE_CODES: tuple[str, ...] = ("R01", "R03", "R04", "R06", "R07", "R10", "R12")

# Order matters only for a stable JSON payload / test assertions.
PRESET_NAMES: tuple[str, ...] = ("balanced", "review_heavy", "ci_heavy", "minimal")


def _normalise(raw: dict[str, float]) -> dict[str, float]:
    """Scale positive raw weights to sum to exactly 1.0 (4 dp), fixing drift.

    Rounding each share independently leaves a few units of error; the residue
    is folded into the largest-weight code so the total lands on 1.0 and the
    UI's ``abs(total - 1.0) < 0.02`` validator stays green.
    """
    total = sum(raw.values())
    if total <= 0:
        return dict.fromkeys(raw, 0.0)
    scaled = {code: round(w / total, 4) for code, w in raw.items()}
    drift = round(1.0 - sum(scaled.values()), 4)
    if drift and scaled:
        top = max(scaled, key=lambda c: raw[c])
        scaled[top] = round(scaled[top] + drift, 4)
    return scaled


def build_weight_presets(checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return ``{preset_name: {code: weight, ..., "_active": [codes]}}``.

    Only built-in checks participate (the client apply loop updates built-in
    checks); custom checks keep their own weights. Every built-in code appears
    in every preset map with an explicit weight so applying a preset is
    deterministic - inactive checks are set to 0.0 and left out of ``_active``.
    """
    builtins = [c for c in checks if c.get("is_builtin") and c.get("check_code")]
    codes = [str(c["check_code"]) for c in builtins]
    category_by_code = {str(c["check_code"]): str(c.get("category") or "custom") for c in builtins}
    presets: dict[str, dict[str, Any]] = {}

    for name, emphasis in _CATEGORY_EMPHASIS.items():
        raw = {code: emphasis.get(category_by_code[code], 1.0) for code in codes}
        weights = _normalise(raw)
        presets[name] = {**weights, "_active": list(codes)}

    core = [code for code in codes if code in _MINIMAL_CORE_CODES] or list(codes)
    minimal_raw = {code: (1.0 if code in core else 0.0) for code in codes}
    minimal_weights = _normalise(minimal_raw)
    presets["minimal"] = {**minimal_weights, "_active": core}

    return presets


# -- Convention pattern presets ------------------------------------------
# A pattern preset fills the R02/R03/R05 configuration in one click: the regex,
# globs and headings a course expects, PLUS the strict-mode toggles that decide
# whether any of it is scored. Those toggles matter: a branch regex on its own
# changes nothing until `require_branch_convention` is on, which is exactly the
# trap the old standalone "Patterns" card set for teachers.
#
# Values are the check_config overrides to write, keyed by check code, so the
# client applies them through the same endpoint it uses for a manual edit.
PATTERN_PRESET_LABELS: dict[str, str] = {
    "tuke_fei": "TUKE FEI",
    "strict": "Strict",
    "off": "No conventions",
}

_PATTERN_PRESETS: dict[str, dict[str, dict[str, Any]]] = {
    # Matches the branch names the TUKE FEI courses ask students to use, and
    # the test layouts their template repos ship with.
    "tuke_fei": {
        "R02": {
            "require_branch_convention": True,
            "branch_pattern": r"^(feature|fix|issue)[-/][a-z0-9._-]+$",
        },
        "R03": {
            "test_file_patterns": [
                "*test*.py",
                "*_test.go",
                "*Test.java",
                "*.test.js",
                "*.test.ts",
                "*.spec.js",
                "*.spec.ts",
                "tests/*",
            ],
        },
        "R05": {
            "require_template": True,
            "required_sections": ["## Popis", "## Testovanie"],
        },
    },
    # Every MR must trace back to an issue and carry a full What/Why/How body.
    "strict": {
        "R02": {"require_branch_convention": True, "branch_pattern": r"^issue-\d+"},
        "R03": {"test_file_patterns": ["*test*", "*spec*"]},
        "R05": {
            "require_template": True,
            "required_sections": ["## What", "## Why", "## How"],
        },
    },
    # Clears the patterns and turns strict mode off, so R02/R05 pass any MR and
    # R03 falls back to its built-in test detection.
    "off": {
        "R02": {"require_branch_convention": False, "branch_pattern": ""},
        "R03": {"test_file_patterns": []},
        "R05": {"require_template": False, "required_sections": []},
    },
}

PATTERN_PRESET_NAMES: tuple[str, ...] = ("tuke_fei", "strict", "off")


def build_pattern_presets() -> dict[str, dict[str, Any]]:
    """Return ``{preset_name: {"label": str, "configs": {code: {...}}}}``."""
    return {
        name: {
            "label": PATTERN_PRESET_LABELS[name],
            "configs": {code: dict(cfg) for code, cfg in _PATTERN_PRESETS[name].items()},
        }
        for name in PATTERN_PRESET_NAMES
    }

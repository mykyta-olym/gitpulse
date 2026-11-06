"""Resolution of R02/R03/R05 convention patterns after the move to check_configs."""

from __future__ import annotations

from app.compliance.patterns import resolve_patterns
from app.models.course_settings import CourseSettings


def _settings(**kwargs: object) -> CourseSettings:
    """A CourseSettings carrying only the fields resolve_patterns reads."""
    cs = CourseSettings()
    cs.check_configs = {}
    cs.branch_pattern = ""
    cs.test_file_patterns = []
    cs.mr_template_required_sections = []
    for key, value in kwargs.items():
        setattr(cs, key, value)
    return cs


def test_returns_empty_config_without_settings() -> None:
    resolved = resolve_patterns(None)

    assert resolved.branch_pattern == ""
    assert resolved.test_file_patterns == []
    assert resolved.required_sections == []


def test_reads_patterns_from_check_configs() -> None:
    resolved = resolve_patterns(
        _settings(
            check_configs={
                "R02": {"branch_pattern": "^feature-"},
                "R03": {"test_file_patterns": ["*_test.py"]},
                "R05": {"required_sections": ["## Why"]},
            }
        )
    )

    assert resolved.branch_pattern == "^feature-"
    assert resolved.test_file_patterns == ["*_test.py"]
    assert resolved.required_sections == ["## Why"]


def test_falls_back_to_legacy_columns_when_check_configs_empty() -> None:
    """A row that predates migration 011 must keep scoring the same way."""
    resolved = resolve_patterns(
        _settings(
            branch_pattern="^issue-",
            test_file_patterns=["*test*.py"],
            mr_template_required_sections=["## Description"],
        )
    )

    assert resolved.branch_pattern == "^issue-"
    assert resolved.test_file_patterns == ["*test*.py"]
    assert resolved.required_sections == ["## Description"]


def test_check_configs_wins_over_legacy_column() -> None:
    resolved = resolve_patterns(
        _settings(
            branch_pattern="^legacy-",
            check_configs={"R02": {"branch_pattern": "^new-"}},
        )
    )

    assert resolved.branch_pattern == "^new-"


def test_accepts_comma_separated_string_from_the_form() -> None:
    """The text input posts one string; the API stores a real list."""
    resolved = resolve_patterns(
        _settings(
            check_configs={
                "R03": {"test_file_patterns": "*_test.py, tests/*.py"},
                "R05": {"required_sections": "## What, ## Why"},
            }
        )
    )

    assert resolved.test_file_patterns == ["*_test.py", "tests/*.py"]
    assert resolved.required_sections == ["## What", "## Why"]


def test_blank_check_config_entries_fall_back_rather_than_disabling() -> None:
    """An empty override is "not configured", not "no conventions at all"."""
    resolved = resolve_patterns(
        _settings(
            branch_pattern="^issue-",
            test_file_patterns=["*test*.py"],
            check_configs={
                "R02": {"branch_pattern": "   "},
                "R03": {"test_file_patterns": []},
            },
        )
    )

    assert resolved.branch_pattern == "^issue-"
    assert resolved.test_file_patterns == ["*test*.py"]


def test_ignores_malformed_check_config_entries() -> None:
    resolved = resolve_patterns(
        _settings(
            branch_pattern="^issue-",
            check_configs={"R02": "not-a-dict", "R03": {"test_file_patterns": 42}},
        )
    )

    assert resolved.branch_pattern == "^issue-"
    assert resolved.test_file_patterns == []


def test_pattern_presets_always_ship_their_enforcement_flags() -> None:
    """A preset must never leave a pattern that nothing scores.

    R02 and R05 only read their pattern while the matching strict-mode flag is
    on, which is exactly the trap the old standalone "Patterns" card set.
    """
    from app.compliance.presets import build_pattern_presets

    presets = build_pattern_presets()
    assert set(presets) == {"tuke_fei", "strict", "off"}

    for name, preset in presets.items():
        configs = preset["configs"]
        assert preset["label"]
        assert set(configs) == {"R02", "R03", "R05"}
        # The flag travels with the pattern, in both directions.
        assert "require_branch_convention" in configs["R02"]
        assert "branch_pattern" in configs["R02"]
        assert "require_template" in configs["R05"]
        assert "required_sections" in configs["R05"]
        if name != "off":
            assert configs["R02"]["require_branch_convention"] is True
            assert configs["R05"]["require_template"] is True


def test_off_preset_clears_patterns_and_disables_enforcement() -> None:
    from app.compliance.presets import build_pattern_presets

    configs = build_pattern_presets()["off"]["configs"]

    assert configs["R02"] == {"require_branch_convention": False, "branch_pattern": ""}
    assert configs["R05"] == {"require_template": False, "required_sections": []}
    assert configs["R03"]["test_file_patterns"] == []


def test_preset_branch_patterns_are_valid_regexes() -> None:
    """They are compiled by validate_branch_name on every MR."""
    import re

    from app.compliance.presets import build_pattern_presets

    for preset in build_pattern_presets().values():
        re.compile(preset["configs"]["R02"]["branch_pattern"])


def _builtin(code: str, category: str, weight: float = 0.1) -> dict[str, object]:
    return {
        "check_code": code,
        "category": category,
        "weight": weight,
        "is_active": True,
        "is_builtin": True,
    }


_CHECKS = [
    _builtin("R01", "issue"),
    _builtin("R02", "mr"),
    _builtin("R03", "mr"),
    _builtin("R06", "review"),
    _builtin("R07", "review"),
    _builtin("R12", "ci"),
    {
        "check_code": "C01",
        "category": "custom",
        "weight": 0.5,
        "is_active": True,
        "is_builtin": False,
    },
]


def test_every_weight_preset_sums_to_one() -> None:
    """The UI shows this total and turns red when it drifts; a preset that does
    not normalise would ship a permanently invalid configuration."""
    from app.compliance.presets import build_weight_presets

    presets = build_weight_presets(_CHECKS)

    for name, preset in presets.items():
        weights = [v for k, v in preset.items() if not k.startswith("_")]
        assert abs(sum(weights) - 1.0) < 0.001, f"{name} sums to {sum(weights)}"


def test_presets_cover_only_builtin_checks() -> None:
    """Custom checks keep their own weights - the client apply loop skips them."""
    from app.compliance.presets import build_weight_presets

    for preset in build_weight_presets(_CHECKS).values():
        assert "C01" not in preset


def test_review_heavy_outweighs_balanced_on_review_checks() -> None:
    from app.compliance.presets import build_weight_presets

    presets = build_weight_presets(_CHECKS)

    assert presets["review_heavy"]["R06"] > presets["balanced"]["R06"]
    assert presets["ci_heavy"]["R12"] > presets["balanced"]["R12"]


def test_minimal_deactivates_the_non_core_checks() -> None:
    from app.compliance.presets import build_weight_presets

    minimal = build_weight_presets(_CHECKS)["minimal"]

    assert "R01" in minimal["_active"]
    assert "R02" not in minimal["_active"]
    assert minimal["R02"] == 0.0

"""Unit tests for dynamic server-side weight presets (build_weight_presets)."""

from app.compliance.presets import PRESET_NAMES, build_weight_presets

# A representative slice of the built-in registry (code + category + is_builtin)
# plus one custom check, matching the shape list_all_checks returns.
_CHECKS = [
    {"check_code": "R01", "category": "issue", "is_builtin": True},
    {"check_code": "R02", "category": "mr", "is_builtin": True},
    {"check_code": "R03", "category": "mr", "is_builtin": True},
    {"check_code": "R04", "category": "mr", "is_builtin": True},
    {"check_code": "R05", "category": "mr", "is_builtin": True},
    {"check_code": "R06", "category": "review", "is_builtin": True},
    {"check_code": "R07", "category": "review", "is_builtin": True},
    {"check_code": "R08", "category": "review", "is_builtin": True},
    {"check_code": "R09", "category": "review", "is_builtin": True},
    {"check_code": "R10", "category": "mr", "is_builtin": True},
    {"check_code": "R11", "category": "mr", "is_builtin": True},
    {"check_code": "R12", "category": "ci", "is_builtin": True},
    {"check_code": "R13", "category": "commit", "is_builtin": True},
    {"check_code": "C01", "category": "custom", "is_builtin": False},
]


def _weights(preset: dict) -> dict[str, float]:
    return {k: v for k, v in preset.items() if k != "_active"}


class TestBuildWeightPresets:
    def test_all_presets_present(self) -> None:
        presets = build_weight_presets(_CHECKS)
        assert set(presets) == set(PRESET_NAMES)

    def test_covers_r13_unlike_old_hardcoded(self) -> None:
        # The old client presets stopped at R12; the dynamic set must include R13.
        presets = build_weight_presets(_CHECKS)
        for name in PRESET_NAMES:
            assert "R13" in presets[name], f"{name} missing R13"

    def test_excludes_custom_checks(self) -> None:
        # Custom checks keep their own weights; presets only touch built-ins.
        presets = build_weight_presets(_CHECKS)
        for name in PRESET_NAMES:
            assert "C01" not in presets[name]

    def test_active_weights_sum_to_one(self) -> None:
        presets = build_weight_presets(_CHECKS)
        for name, preset in presets.items():
            active = set(preset["_active"])
            total = round(sum(w for c, w in _weights(preset).items() if c in active), 4)
            assert abs(total - 1.0) < 0.02, f"{name} sums to {total}"

    def test_balanced_is_equal_across_all_builtins(self) -> None:
        preset = build_weight_presets(_CHECKS)["balanced"]
        weights = list(_weights(preset).values())
        assert max(weights) - min(weights) < 0.001
        assert len(preset["_active"]) == 13

    def test_review_heavy_favours_review_category(self) -> None:
        preset = build_weight_presets(_CHECKS)["review_heavy"]
        w = _weights(preset)
        assert w["R06"] > w["R01"]  # review weighted above issue

    def test_ci_heavy_favours_ci(self) -> None:
        preset = build_weight_presets(_CHECKS)["ci_heavy"]
        w = _weights(preset)
        assert w["R12"] > w["R01"]  # ci weighted above issue

    def test_minimal_deactivates_non_core_with_zero_weight(self) -> None:
        preset = build_weight_presets(_CHECKS)["minimal"]
        w = _weights(preset)
        assert "R02" not in preset["_active"]
        assert w["R02"] == 0.0  # explicitly zeroed so apply loop deactivates it
        assert "R01" in preset["_active"]
        assert w["R01"] > 0.0

    def test_empty_input_yields_empty_maps(self) -> None:
        presets = build_weight_presets([])
        for name in PRESET_NAMES:
            assert presets[name]["_active"] == []

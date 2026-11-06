"""Unit tests for the compliance history and check registry pure helpers."""

from app.compliance.check_registry import _build_lookups
from app.services.compliance_history import _derive_category_scores


class TestDeriveCategoryScores:
    """Validate JSONB-based category score derivation."""

    def test_empty_input(self) -> None:
        assert _derive_category_scores(None) == {}
        assert _derive_category_scores({}) == {}

    def test_single_check(self) -> None:
        detail = {"R01": {"score": 0.5, "weight": 1.0}}
        result = _derive_category_scores(detail)
        assert result["issue"] == 0.5

    def test_ci_category(self) -> None:
        detail = {"R12": {"score": 1.0, "weight": 1.0}}
        result = _derive_category_scores(detail)
        assert result["ci"] == 1.0

    def test_missing_categories_are_none(self) -> None:
        detail = {"R01": {"score": 1.0, "weight": 1.0}}
        result = _derive_category_scores(detail)
        assert result["mr"] is None
        assert result["review"] is None
        assert result["ci"] is None

    def test_skips_non_dict_entries(self) -> None:
        detail = {"R01": "invalid", "R12": {"score": 1.0, "weight": 1.0}}
        result = _derive_category_scores(detail)
        assert result["ci"] == 1.0

    def test_skips_zero_weight(self) -> None:
        detail = {"R01": {"score": 1.0, "weight": 0}}
        result = _derive_category_scores(detail)
        assert result["issue"] is None

    def test_multiple_mr_checks(self) -> None:
        detail = {
            "R02": {"score": 0.5, "weight": 0.5},
            "R03": {"score": 0.5, "weight": 0.5},
        }
        result = _derive_category_scores(detail)
        assert result["mr"] == 1.0

    def test_review_category(self) -> None:
        detail = {
            "R06": {"score": 0.3, "weight": 0.5},
            "R07": {"score": 0.5, "weight": 0.5},
        }
        result = _derive_category_scores(detail)
        assert result["review"] == 0.8


class TestBuildLookups:
    """Validate check registry lookup structure builder."""

    def test_basic_entry(self) -> None:
        entries = [
            {
                "code": "R01",
                "db_field": "check_r01",
                "name": "Issue Ownership",
                "weight_field": "weight_r01",
                "category": "issue",
                "description": "Checks issue ownership",
            }
        ]
        defs, defs_map, weights, cats, descs, _configurable, builtins = _build_lookups(entries)
        assert defs == [("check_r01", "R01", "Issue Ownership")]
        assert defs_map == {"R01": "Issue Ownership"}
        assert weights == {"R01": "weight_r01"}
        assert cats == {"R01": "issue"}
        assert descs == {"R01": "Checks issue ownership"}
        assert "R01" in builtins

    def test_default_category(self) -> None:
        entries = [
            {"code": "C01", "db_field": "check_c01", "name": "Custom", "weight_field": "w_c01"}
        ]
        _, _, _, cats, _, _, _ = _build_lookups(entries)
        assert cats["C01"] == "custom"

    def test_params_stored(self) -> None:
        entries = [
            {
                "code": "R01",
                "db_field": "check_r01",
                "name": "Issue",
                "weight_field": "w_r01",
                "params": [{"key": "min_count", "type": "int", "default": "1"}],
            }
        ]
        _, _, _, _, _, configurable, _ = _build_lookups(entries)
        assert "R01" in configurable
        assert configurable["R01"][0]["key"] == "min_count"

    def test_empty_entries(self) -> None:
        defs, defs_map, _weights, _cats, _descs, _configurable, builtins = _build_lookups([])
        assert defs == []
        assert defs_map == {}
        assert builtins == set()

    def test_multiple_entries(self) -> None:
        entries = [
            {
                "code": "R01",
                "db_field": "check_r01",
                "name": "Issue",
                "weight_field": "w_r01",
                "category": "issue",
            },
            {
                "code": "R02",
                "db_field": "check_r02",
                "name": "MR Size",
                "weight_field": "w_r02",
                "category": "mr",
                "description": "MR check",
            },
            {
                "code": "R12",
                "db_field": "check_r12",
                "name": "CI",
                "weight_field": "w_r12",
                "category": "ci",
            },
        ]
        defs, _defs_map, _weights, cats, descs, _configurable, builtins = _build_lookups(entries)
        assert len(defs) == 3
        assert len(builtins) == 3
        assert cats["R02"] == "mr"
        assert descs["R02"] == "MR check"
        assert descs["R01"] == ""

import config
from evaluate import _binary_counts, _numeric_match


def test_binary_metrics_count_true_false_and_missed_items():
    counts = _binary_counts({"a", "b", "c"}, {"a", "b", "extra"})
    assert counts == {"tp": 2, "fp": 1, "fn": 1}


def test_nutrition_evaluation_requires_matching_unit_and_basis():
    expected = {"value": 100, "unit": "mg", "basis": "100g"}
    within_tolerance = {"value": 109, "unit": "mg", "basis": "100g"}
    outside_tolerance = {"value": 111, "unit": "mg", "basis": "100g"}
    wrong_basis = {"value": 100, "unit": "mg", "basis": "per_serving"}

    assert config.EVALUATION_NUTRIENT_REL_TOLERANCE == 0.10
    assert _numeric_match(expected, within_tolerance)
    assert not _numeric_match(expected, outside_tolerance)
    assert not _numeric_match(expected, wrong_basis)

from nutrition import parse_nutrition
from storage import load_knowledge
import pytest


def _limits():
    return load_knowledge()["nutrition_limits"]


def _by_name(items, name, *, estimated=None):
    return next(item for item in items if item["name"] == name and (estimated is None or item["estimated"] is estimated))


def test_parses_per_100g_values_mixed_units_and_preserves_source_spans():
    text = """Nutrition Information per 100 g
Energy 420 kcal
Total Fat 12.5 g
Saturated Fat 4 g
Trans Fat 0.1 g
Total sugars 8 g
Added sugars 6 g
Sodium 0.8 g
Protein 5 g
Dietary Fibre 3 g"""
    results = parse_nutrition(text, _limits())
    values = {item["name"]: item for item in results}
    assert values["energy"]["status"] == "Informational"
    assert values["total_fat"]["status"] == "Medium"
    assert values["saturated_fat"]["status"] == "Medium"
    assert values["trans_fat"]["status"] == "Low"
    assert values["sugar"]["status"] == "Medium"
    assert values["added_sugar"]["status"] == "not comparable"
    assert values["added_sugar"]["value"] == 6
    assert values["sodium"]["value"] == 800
    assert values["sodium"]["unit"] == "mg"
    assert values["sodium"]["status"] == "High"
    assert values["protein"]["status"] == "Informational"
    assert values["fibre"]["status"] == "Informational"
    for nutrient in ("energy", "protein", "fibre"):
        assert values[nutrient]["status"] == "Informational"
        assert "thresholds" not in values[nutrient]
    assert values["sugar"]["source_span"] == "Total sugars 8 g"
    assert values["sodium"]["threshold_source"]
    assert "Source:" not in values["sugar"]["reason"]


def test_per_serving_converts_only_with_clear_serving_size():
    results = parse_nutrition("Serving size 30 g\nPer serving\nSugar 6 g\nSodium 150 mg", _limits())
    sugar = _by_name(results, "sugar")
    sodium = _by_name(results, "sodium", estimated=False)
    assert sugar["value"] == 20
    assert sugar["basis"] == "100g"
    assert sugar["original_basis"] == "per_serving"
    assert "Converted from per_serving" in sugar["reason"]
    assert sodium["value"] == 500
    assert sodium["basis"] == "100g"


def test_per_serving_without_size_is_not_compared_to_per_100g():
    value = _by_name(parse_nutrition("Per serving\nSugar 6 g", _limits()), "sugar")
    assert value["basis"] == "per_serving"
    assert value["status"] == "not comparable"
    assert "uses 100g" in value["reason"]


def test_per_100ml_uses_a_separate_documented_liquid_rule():
    value = _by_name(parse_nutrition("Nutrition per 100 ml\nSugar 12 g", _limits()), "sugar")
    assert value["basis"] == "100ml"
    assert value["status"] == "High"
    assert value["thresholds"]["basis"] == "100ml"
    assert value["thresholds"]["high_above"] == 11.25


def test_salt_is_separate_and_sodium_estimate_is_explicit():
    results = parse_nutrition("Nutrition per 100 g\nSalt 1.0 g", _limits())
    salt = _by_name(results, "salt")
    sodium = _by_name(results, "sodium", estimated=True)
    assert salt["value"] == 1.0
    assert salt["status"] == "Medium"
    assert sodium["value"] == 400
    assert sodium["unit"] == "mg"
    assert sodium["status"] == "Medium"
    assert "estimate, not a measured sodium value" in sodium["reason"]
    assert sodium["source_span"] == "Salt 1.0 g"


def test_mixed_per_100g_and_per_serving_columns_keep_both_bases():
    text = "Nutrition per 100 g and per serving\nServing size 30 g\nSugar 20 g 6 g"
    results = [item for item in parse_nutrition(text, _limits()) if item["name"] == "sugar"]
    assert len(results) == 2
    assert [item["basis"] for item in results] == ["100g", "100g"]
    assert all(item["status"] == "Medium" for item in results)


def test_value_on_next_line_and_unit_before_value_are_associated():
    values = parse_nutrition("Per 100 g\nSaturated Fat\n8 g\nSodium (mg) 900", _limits())
    assert _by_name(values, "saturated_fat")["value"] == 8
    assert _by_name(values, "sodium")["value"] == 900
    assert all(item["status"] == "High" for item in values)


def test_potassium_and_cholesterol_do_not_supply_a_missing_sodium_value():
    values = parse_nutrition("Per 100 g\nSodium unreadable Potassium 170 mg\nSugar 12 g Cholesterol 5 mg", _limits())
    assert _by_name(values, "sodium")["value"] is None
    assert _by_name(values, "sodium")["verified"] is False
    assert _by_name(values, "sugar")["value"] == 12


@pytest.mark.parametrize("reading", ["Sugar <1 g", "Sugar -3 g", "Sugar 900 g", "Sugar 5 g 9 g", "Sugar ??"])
def test_uncertain_or_impossible_readings_are_not_verified(reading):
    values = parse_nutrition("Per 100 g\n" + reading, _limits())
    assert values
    assert all(item["verified"] is False and item["status"] == "not comparable" for item in values)


def test_low_confidence_numeric_ocr_is_unverified_even_when_mean_is_high():
    values = parse_nutrition("Per 100 g\nSugar 35 g", _limits(), ocr_context={
        "mean_confidence": 91,
        "lines": [{"text": "Sugar 35 g", "words": [{"text": "Sugar", "confidence": 96}, {"text": "35", "confidence": 12}]}],
    })
    assert _by_name(values, "sugar")["verified"] is False
    assert "OCR confidence" in _by_name(values, "sugar")["reason"]


def test_serving_size_parentheses_and_zero_size_are_handled_safely():
    values = parse_nutrition("Amount/serving\nServ. size 2 tbsp (37 g)\nSugar 15 g", _limits())
    assert _by_name(values, "sugar")["value"] == pytest.approx(15 * 100 / 37)
    assert _by_name(values, "sugar")["original_basis"] == "per_serving"
    assert _by_name(parse_nutrition("Per serving\nServing size 0 g\nSugar 5 g"), "sugar")["status"] == "not comparable"
    assert _by_name(parse_nutrition("Per 0 g\nSugar 5 g"), "sugar")["status"] == "not comparable"


def test_conflicting_values_and_unmapped_columns_are_not_guessed():
    values = parse_nutrition("Per 100 g\nSugar 5 g\nSugar 35 g", _limits())
    assert all(item["verified"] is False for item in values)
    values = parse_nutrition("Per 100 g and per serving\nSugar 5 g", _limits())
    assert _by_name(values, "sugar")["status"] == "not comparable"


def test_serving_heading_does_not_borrow_a_nutrient_quantity():
    value = _by_name(parse_nutrition("Per serving Sugar 30 g"), "sugar")
    assert value["basis"] == "per_serving"
    assert value["status"] == "not comparable"


def test_low_confidence_basis_cannot_verify_high_confidence_values():
    values = parse_nutrition("Per 100 g\nSugar 35 g", ocr_context={
        "mean_confidence": 95,
        "lines": [
            {"text": "Per 100 g", "words": [{"text": "100", "confidence": 20}]},
            {"text": "Sugar 35 g", "words": [{"text": "35", "confidence": 98}]},
        ],
    })
    assert values[0]["verified"] is False
    assert "comparison basis" in values[0]["reason"]


def test_explicit_row_bases_map_values_in_their_stated_order():
    values = parse_nutrition("Serving size 30 g\nSugar per serving 6 g per 100 g 20 g")
    assert [item["original_basis"] for item in values] == ["per_serving", "100g"]
    assert [item["value"] for item in values] == [20, 20]
    assert all(item["verified"] for item in values)


def test_one_local_basis_does_not_borrow_the_global_two_column_mapping():
    values = parse_nutrition("Per 100 g and per serving\nServing size 30 g\nSugar per 100 g 20 g 6 g")
    assert all(item["verified"] is False for item in values)


def test_incompatible_unit_preserves_the_declared_value_unit_and_basis():
    value = _by_name(parse_nutrition("Per 100 g\nSugar 20 kcal"), "sugar")
    assert (value["value"], value["unit"], value["basis"]) == (20, "kcal", "100g")
    assert value["original_basis"] == "100g"
    assert value["verified"] is False


def test_confidence_is_associated_with_each_nutrient_on_a_shared_line():
    values = parse_nutrition("Per 100 g\nTotalFat17g Saturated Fat5g", ocr_context={
        "mean_confidence": 90,
        "lines": [{"text": "TotalFat17g Saturated Fat5g", "words": [
            {"text": "TotalFat17g", "confidence": 3},
            {"text": "Saturated", "confidence": 90}, {"text": "Fat5g", "confidence": 88},
        ]}],
    })
    assert _by_name(values, "total_fat")["verified"] is False
    assert _by_name(values, "saturated_fat")["verified"] is True


def test_australian_nutrition_row_aliases_are_associated_with_values():
    values = parse_nutrition("Nutrition Information per 100 g\nFat, total 3.6 g\n- saturated 1.0 g\n- sugars 21.4 g")
    assert _by_name(values, "total_fat")["value"] == 3.6
    assert _by_name(values, "saturated_fat")["value"] == 1.0
    assert _by_name(values, "sugar")["value"] == 21.4
    assert all(item["verified"] for item in values)


def test_questionable_decimal_ocr_is_not_presented_as_verified():
    values = parse_nutrition("Serving size 25 g\nDietary fibre\n13g", ocr_context={
        "mean_confidence": 85,
        "lines": [{"text": "Dietary fibre", "words": [{"text": "fibre", "confidence": 94}], "confidence": 94},
                  {"text": "13g", "words": [{"text": "13g", "confidence": 50}], "confidence": 50}],
    })
    fibre = _by_name(values, "fibre")
    assert not fibre["verified"]
    assert fibre["status"] == "not comparable"
    assert "OCR confidence" in fibre["reason"]


def test_split_two_column_header_requires_both_values_and_prefers_printed_100g():
    text = ("Nutrition Information\nServing size: 25 g\nper %Daily intake per\n"
            "serving per serving 100g\nFat, total 0.8g 1% 3.0g\n"
            "- sugars 6.0g 7% 24.0g\nDietary fibre 13g\nSodium 87mg 4% 350mg")
    values = parse_nutrition(text)
    fat = _by_name(values, "total_fat")
    assert fat["original_basis"] == "100g" and fat["value"] == 3.0
    assert fat["status"] == "Low"
    assert _by_name(values, "fibre")["verified"] is False
    sodium = _by_name(values, "sodium")
    assert sodium["original_basis"] == "100g" and sodium["value"] == 350
    assert all(item["verified"] for item in values if item["name"] == "sugar")


def test_inconsistent_serving_and_100g_columns_remain_unverified():
    values = parse_nutrition("Nutrition per serving and per 100 g\nServing size 25 g\nSugar 6g 40g")
    assert all(not item["verified"] for item in values)


def test_uncertain_serving_size_cannot_support_a_normalized_score():
    text = "Nutrition Facts\nServing size 15 ml\nAmount per serving\nSaturated Fat 3.5g"
    context = {"mean_confidence": 90, "lines": [
        {"text": "Serving size 15 ml", "words": [{"text": "15", "confidence": 20}]},
        {"text": "Saturated Fat 3.5g", "words": [{"text": "3.5g", "confidence": 95}]},
    ]}
    value = _by_name(parse_nutrition(text, context_text=text, ocr_context=context), "saturated_fat")
    assert value["verified"] is False
    assert "serving size" in value["reason"]


def test_lone_right_column_value_needs_explicit_header_and_coordinates():
    text = "Nutrition Information\nServing size 45 g\nper serving per 100g\nSugars 21.4g"
    context = {"mean_confidence": 95, "lines": [
        {"text": "per serving per 100g", "words": [
            {"text": "serving", "confidence": 95, "box": [100, 0, 40, 10]},
            {"text": "100g", "confidence": 95, "box": [300, 0, 40, 10]}]},
        {"text": "Sugars 21.4g", "words": [
            {"text": "Sugars", "confidence": 95, "box": [0, 20, 50, 10]},
            {"text": "21.4g", "confidence": 95, "box": [300, 20, 40, 10]}]},
    ]}
    value = _by_name(parse_nutrition(text, ocr_context=context), "sugar")
    assert value["original_basis"] == "100g" and value["value"] == 21.4 and value["verified"]
    context["lines"][1]["words"][1]["box"][0] = 100
    assert not _by_name(parse_nutrition(text, ocr_context=context), "sugar")["verified"]


def test_unreadable_other_column_does_not_reduce_confidence_of_direct_value():
    text = "Nutrition Information\nServing size 45 g\nper serving per 100g\nSugars 9.69 11% 21.4g"
    context = {"mean_confidence": 95, "lines": [
        {"text": "per serving per 100g", "words": [
            {"text": "serving", "confidence": 95, "box": [100, 0, 40, 10]},
            {"text": "100g", "confidence": 95, "box": [300, 0, 40, 10]}]},
        {"text": "Sugars 9.69 11% 21.4g", "words": [
            {"text": "9.69", "confidence": 20, "box": [100, 20, 40, 10]},
            {"text": "11%", "confidence": 95, "box": [200, 20, 40, 10]},
            {"text": "21.4g", "confidence": 90, "box": [300, 20, 40, 10]}]},
    ]}
    sugar = _by_name(parse_nutrition(text, ocr_context=context), "sugar")
    assert sugar["verified"] and sugar["original_basis"] == "100g" and sugar["value"] == 21.4


def test_borderline_numeric_confidence_requires_matching_independent_evidence():
    text = "Nutrition per 100g\nSugar 12g"
    context = {"mean_confidence": 95, "lines": [{"text": "Sugar 12g", "words": [{"text": "12g", "confidence": 53}]}]}
    assert not _by_name(parse_nutrition(text, ocr_context=context), "sugar")["verified"]
    context["corroborated_readings"] = [["sugar", 12.0, "g", "100g", None, None]]
    assert _by_name(parse_nutrition(text, ocr_context=context), "sugar")["verified"]
    context["corroborated_readings"] = [["sugar", 1.2, "g", "100g", None, None]]
    assert not _by_name(parse_nutrition(text, ocr_context=context), "sugar")["verified"]

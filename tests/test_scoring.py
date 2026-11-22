
from scoring import calculate_health_score
from nutrition import parse_nutrition


def _complete_low_panel():
    return parse_nutrition("Per 100 g\nTotal Fat 1 g\nSaturated Fat 0.1 g\nTrans Fat 0 g\nSugar 1 g\nSodium 10 mg")


def test_hand_calculated_score_includes_every_reason():
    result = calculate_health_score(
        additives=[{"id": 1, "ins_code": "211", "name": "Sodium benzoate", "risk_level": "low", "reason": "Additive reason."}],
        ingredient_flags=[
            {"id": 1, "keyword": "partially hydrogenated oil", "flag_type": "harmful", "reason": "Flag reason."},
            {"id": 2, "keyword": "whole wheat flour", "flag_type": "beneficial", "reason": "Benefit reason."},
        ],
        nutrients=[
            {"name": "sugar", "value": 30, "unit": "g", "basis": "100g", "status": "High", "reason": "High sugar reason."},
            {"name": "sodium", "value": 500, "unit": "mg", "basis": "100g", "status": "Medium", "reason": "Medium sodium reason."},
            {"name": "energy", "status": "not comparable", "reason": "No basis."},
        ],
    )
    assert result["health_score"] == 67  # 100 - 3 - 10 - 15 - 7 + 2
    assert result["score_band"] == "Moderate"
    assert result["score_breakdown"][0]["reason"] == "The score starts at 100 points."
    assert sum(item["points"] for item in result["score_breakdown"]) == 67
    for reason in ("Additive reason.", "Flag reason.", "Benefit reason.", "High sugar reason.", "Medium sodium reason."):
        assert any(reason in item["reason"] for item in result["score_breakdown"])
    assert result["score_status"] == "provisional"


def test_deduction_caps_and_zero_clamp_are_applied():
    result = calculate_health_score(
        additives=[{"ins_code": str(index), "name": f"a{index}", "risk_level": "high"} for index in range(10)],
        ingredient_flags=[{"keyword": f"harmful {index}", "flag_type": "harmful"} for index in range(5)],
        nutrients=parse_nutrition("Per 100 g\nSugar 30 g"),
    )
    assert result["health_score"] == 0
    assert result["totals"]["additive_deduction"] == 60
    assert result["totals"]["harmful_flag_deduction"] == 30
    assert any(item.get("cap_note") for item in result["score_breakdown"])
    assert result["score_band"] == "Poor"


def test_beneficial_credit_is_capped_and_score_clamped():
    result = calculate_health_score(
        ingredient_flags=[{"keyword": f"beneficial {index}", "flag_type": "beneficial"} for index in range(8)],
        nutrients=_complete_low_panel(),
    )
    assert result["totals"]["beneficial_credit"] == 10
    assert result["health_score"] == 100
    assert result["score_band"] == "Good"
    assert result["score_breakdown"][-1]["category"] == "clamp"


def test_allergen_alerts_do_not_affect_score():
    baseline = calculate_health_score(nutrients=_complete_low_panel())
    # Alerts are deliberately not an input to the scoring function.
    with_alert = calculate_health_score(nutrients=_complete_low_panel())
    assert baseline["health_score"] == with_alert["health_score"] == 100


def test_duplicate_additives_and_flags_are_not_counted_twice():
    result = calculate_health_score(
        additives=[{"ins_code": "211", "name": "A", "risk_level": "low"}, {"ins_code": "211", "name": "A duplicate", "risk_level": "low"}],
        ingredient_flags=[{"keyword": "oats", "flag_type": "beneficial"}, {"keyword": "oats", "flag_type": "beneficial"}],
        nutrients=_complete_low_panel(),
    )
    assert result["health_score"] == 99


def test_energy_protein_and_fibre_never_reduce_score_even_with_legacy_statuses():
    result = calculate_health_score(nutrients=_complete_low_panel() + [
        {"name": "energy", "status": "High"},
        {"name": "protein", "status": "High"},
        {"name": "fibre", "status": "Medium"},
    ])
    assert result["health_score"] == 100
    assert result["totals"]["nutrient_deduction"] == 0
    assert not [item for item in result["score_breakdown"] if item["category"] == "nutrient"]


def test_empty_or_status_only_data_cannot_earn_a_score():
    for nutrients in ([], [{"name": "sugar", "status": "High"}], parse_nutrition("Per serving\nSugar 30 g")):
        result = calculate_health_score(nutrients=nutrients)
        assert result["health_score"] is None
        assert result["score_band"] is None
        assert result["score_status"] == "insufficient"
        assert result["score_breakdown"] == []


def test_partial_low_information_does_not_publish_a_perfect_score():
    result = calculate_health_score(nutrients=parse_nutrition("Per 100 g\nSugar 0 g"))
    assert result["health_score"] is None
    assert result["score_status"] == "insufficient"
    assert "sodium" in result["data_completeness"]["missing_nutrients"]


def test_score_rechecks_values_instead_of_trusting_status_strings():
    result = calculate_health_score(nutrients=[{"name": "sugar", "value": 35, "unit": "g", "basis": "100g", "status": "Low"}])
    assert result["health_score"] == 85
    assert sum(item["points"] for item in result["score_breakdown"]) == 85


def test_salt_and_sodium_are_not_deducted_twice():
    result = calculate_health_score(nutrients=parse_nutrition("Per 100 g\nSalt 2 g"))
    assert result["health_score"] == 85
    assert [item["item"] for item in result["score_breakdown"] if item["category"] == "nutrient"] == ["salt"]
    result = calculate_health_score(nutrients=parse_nutrition("Per 100 g\nSalt 2 g\nSodium 800 mg"))
    assert [item["item"] for item in result["score_breakdown"] if item["category"] == "nutrient"] == ["sodium"]


def test_explicit_zero_values_are_valid_when_the_full_panel_is_present():
    result = calculate_health_score(nutrients=parse_nutrition(
        "Per 100 g\nTotal Fat 0 g\nSaturated Fat 0 g\nTrans Fat 0 g\nSugar 0 g\nSodium 0 mg"
    ))
    assert result["score_status"] == "sufficient"
    assert result["health_score"] == 100
    assert result["data_completeness"]["verified_core_count"] == 5


def test_ingredient_only_score_has_explicit_scope_and_reconciled_existing_weights():
    result = calculate_health_score(additives=[{"ins_code": "211", "risk_level": "low"}],
                                    ingredient_flags=[{"keyword": "hydrogenated oil", "flag_type": "harmful"}])
    assert result["score_status"] == "ingredient-only"
    assert result["health_score"] == 87
    assert result["score_band"] == "Moderate"
    assert result["data_completeness"]["nutrition_status"] == "insufficient"
    assert result["data_completeness"]["verified_core_count"] == 0
    assert sum(row["points"] for row in result["score_breakdown"]) == 87
    assert not any(row["category"] == "nutrient" for row in result["score_breakdown"])
    assert any("Ingredient-only score" in message for message in result["data_completeness"]["messages"])


def test_caution_only_ingredient_score_is_labelled_and_cannot_earn_good_band():
    result = calculate_health_score(ingredient_flags=[{"keyword": "test caution", "flag_type": "caution"}])
    assert result["health_score"] == 100 and result["score_status"] == "ingredient-only"
    assert result["score_band"] == "Moderate"
    assert sum(row["points"] for row in result["score_breakdown"]) == 100


def test_low_coverage_caps_band_without_changing_numeric_score_or_ledger():
    result = calculate_health_score(nutrients=parse_nutrition("Per 100g\nSugar 35g"))
    assert result["health_score"] == 85 and result["score_band"] == "Moderate"
    assert result["score_status"] == "provisional"
    assert any("Based on 1 of 5 nutrients" in message for message in result["data_completeness"]["messages"])
    assert sum(row["points"] for row in result["score_breakdown"]) == 85
    result = calculate_health_score(nutrients=parse_nutrition("Per 100g\nSugar 35g\nSodium 10mg\nTotal Fat 1g"))
    assert result["score_band"] == "Good"  # Exactly 60%, so the requested cap does not apply.

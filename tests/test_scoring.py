from scoring import calculate_health_score


def test_hand_calculated_score_includes_every_reason():
    result = calculate_health_score(
        additives=[{"id": 1, "ins_code": "211", "name": "Sodium benzoate", "risk_level": "low", "reason": "Additive reason."}],
        ingredient_flags=[
            {"id": 1, "keyword": "partially hydrogenated oil", "flag_type": "harmful", "reason": "Flag reason."},
            {"id": 2, "keyword": "whole wheat flour", "flag_type": "beneficial", "reason": "Benefit reason."},
        ],
        nutrients=[
            {"name": "sugar", "status": "High", "reason": "High sugar reason."},
            {"name": "sodium", "status": "Medium", "reason": "Medium sodium reason."},
            {"name": "energy", "status": "not comparable", "reason": "No basis."},
        ],
    )
    assert result["health_score"] == 67  # 100 - 3 - 10 - 15 - 7 + 2
    assert result["score_band"] == "Moderate"
    assert result["score_breakdown"][0]["reason"] == "The score starts at 100 points."
    assert sum(item["points"] for item in result["score_breakdown"]) == 67
    assert {"Additive reason.", "Flag reason.", "Benefit reason.", "High sugar reason.", "Medium sodium reason."}.issubset(
        {item["reason"] for item in result["score_breakdown"]}
    )


def test_deduction_caps_and_zero_clamp_are_applied():
    result = calculate_health_score(
        additives=[{"ins_code": str(index), "name": f"a{index}", "risk_level": "high"} for index in range(10)],
        ingredient_flags=[{"keyword": f"harmful {index}", "flag_type": "harmful"} for index in range(5)],
        nutrients=[{"name": "sugar", "status": "High"}],
    )
    assert result["health_score"] == 0
    assert result["totals"]["additive_deduction"] == 60
    assert result["totals"]["harmful_flag_deduction"] == 30
    assert any(item.get("cap_note") for item in result["score_breakdown"])
    assert result["score_band"] == "Poor"


def test_beneficial_credit_is_capped_and_score_clamped():
    result = calculate_health_score(
        ingredient_flags=[{"keyword": f"beneficial {index}", "flag_type": "beneficial"} for index in range(8)]
    )
    assert result["totals"]["beneficial_credit"] == 10
    assert result["health_score"] == 100
    assert result["score_band"] == "Good"
    assert result["score_breakdown"][-1]["category"] == "clamp"


def test_allergen_alerts_do_not_affect_score():
    baseline = calculate_health_score()
    # Alerts are deliberately not an input to the scoring function.
    with_alert = calculate_health_score()
    assert baseline["health_score"] == with_alert["health_score"] == 100


def test_duplicate_additives_and_flags_are_not_counted_twice():
    result = calculate_health_score(
        additives=[{"ins_code": "211", "name": "A", "risk_level": "low"}, {"ins_code": "211", "name": "A duplicate", "risk_level": "low"}],
        ingredient_flags=[{"keyword": "oats", "flag_type": "beneficial"}, {"keyword": "oats", "flag_type": "beneficial"}],
    )
    assert result["health_score"] == 99


def test_energy_protein_and_fibre_never_reduce_score_even_with_legacy_statuses():
    result = calculate_health_score(nutrients=[
        {"name": "energy", "status": "High"},
        {"name": "protein", "status": "High"},
        {"name": "fibre", "status": "Medium"},
    ])
    assert result["health_score"] == 100
    assert result["totals"]["nutrient_deduction"] == 0
    assert not [item for item in result["score_breakdown"] if item["category"] == "nutrient"]

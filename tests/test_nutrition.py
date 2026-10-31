from nutrition import parse_nutrition
from storage import load_knowledge


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
    assert values["added_sugar"]["status"] == "Medium"
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


def test_per_100ml_is_not_compared_to_per_100g():
    value = _by_name(parse_nutrition("Nutrition per 100 ml\nSugar 12 g", _limits()), "sugar")
    assert value["basis"] == "100ml"
    assert value["status"] == "not comparable"


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

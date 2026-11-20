import pytest

from nutrition import parse_nutrition


def word(text, x, y, width=40, confidence=95):
    return {"text": text, "box": [x, y, width, 20], "confidence": confidence}


def context(reverse=False, confidence=95, unit=True):
    left, right = ("serving", "100g") if reverse else ("100g", "serving")
    values = ("6", "20") if reverse else ("20", "6")
    return {"mean_confidence": 95, "lines": [
        {"text": "Nutrition Facts", "words": [word("Nutrition", 0, 0, 80), word("Facts", 90, 0)]},
        {"text": "per " + left + " per " + right, "words": [word("per", 130, 40), word(left, 180, 40), word("per", 330, 40), word(right, 380, 40)]},
        # Tesseract split the label/values into different TSV line IDs.
        {"text": "Sugar", "words": [word("Sugar", 0, 80)]},
        {"text": values[0] + ("g" if unit else ""), "words": [word(values[0] + ("g" if unit else ""), 180, 80, confidence=confidence)]},
        {"text": values[1] + ("g" if unit else ""), "words": [word(values[1] + ("g" if unit else ""), 380, 80, confidence=confidence)]},
    ]}


@pytest.mark.parametrize("reverse", [False, True])
def test_coordinates_recover_rows_and_either_column_order(reverse):
    values = parse_nutrition("Nutrition Facts\nper 100g and per serving\nServing size 30g\nSugar unreadable",
                             context_text="Serving size 30g", ocr_context=context(reverse))
    recovered = [item for item in values if item.get("coordinate_association")]
    assert recovered and all(item["verified"] for item in recovered)
    assert all(item["value"] == 20 for item in recovered)
    assert {item["original_basis"] for item in recovered} == {"100g", "per_serving"}


def test_coordinates_never_invent_a_missing_unit_or_accept_low_confidence():
    for ctx in (context(unit=False), context(confidence=15)):
        values = parse_nutrition("Nutrition Facts\nSugar unreadable", ocr_context=ctx, context_text="Serving size 30g")
        assert not any(item["verified"] for item in values)


def test_coordinates_preserve_bounds_and_ignore_percentages():
    ctx = context()
    ctx["lines"][3]["text"] = "<20g"
    ctx["lines"][3]["words"][0]["text"] = "<20g"
    ctx["lines"][4]["text"] = "6%"
    ctx["lines"][4]["words"][0]["text"] = "6%"
    values = parse_nutrition("Nutrition Facts\nSugar unreadable", ocr_context=ctx, context_text="Serving size 30g")
    assert not any(item["verified"] for item in values)


def test_multiple_nutrition_panels_are_not_combined_by_coordinates():
    ctx = context()
    ctx["lines"].append({"text": "Nutrition Facts", "words": [word("Nutrition", 600, 0, 80)]})
    assert not any(item["verified"] for item in parse_nutrition("Sugar unreadable", ocr_context=ctx))


def test_explicit_row_units_and_fatty_acid_names_are_supported():
    values = parse_nutrition("Per 100g\nEnergy(kcal) 548.13\nSaturated Fats(g) 14.79\nTrans fatty acids(g) 0.00\nSodium(mg) 1412.65\nAdded Sugar(g) 1.73")
    by_name = {item["name"]: item for item in values}
    assert by_name["saturated_fat"]["value"] == 14.79
    assert by_name["sodium"]["value"] == 1412.65
    assert by_name["trans_fat"]["verified"]

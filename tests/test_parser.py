
from parser import normalize_text, parse_label_text, split_ingredient_tokens


def test_parser_preserves_raw_and_separates_label_sections():
    raw = (
        "Brand 0ne\n"
        "Ingredients: Wheat flour, sugar (cane, brown), E 211; soy lecithin\n"
        "Contains: Peanut and Milk\n"
        "Nutrition Information (per 100 g)\n"
        "Energy 425 kcal\nTotal Fat 15 g\nS0dium 520 mg\n"
        "Best before: 12/2026\nManufactured by Sample Foods"
    )
    parsed = parse_label_text(raw)
    assert parsed["raw_text"] == raw
    assert parsed["ingredient_tokens"] == ["Wheat flour", "sugar (cane, brown)", "E 211", "soy lecithin"]
    assert "Peanut and Milk" in parsed["contains_text"]
    assert "Energy 425 kcal" in parsed["nutrition_text"]
    assert "Best before" not in parsed["nutrition_text"]
    assert "sodium 520 mg" in parsed["normalized_text"]
    assert "brand one" in parsed["normalized_text"]
    assert "425" in parsed["nutrition_text"]


def test_split_preserves_nested_bracket_contents():
    assert split_ingredient_tokens("flour (wheat, rice), seasoning [salt; spice], oil") == [
        "flour (wheat, rice)", "seasoning [salt; spice]", "oil"
    ]


def test_same_line_headings_are_split_correctly():
    parsed = parse_label_text("Ingredients: flour, sugar Nutrition Information: Sugar 12 g")
    assert parsed["ingredient_tokens"] == ["flour", "sugar"]
    assert parsed["nutrition_text"] == "Sugar 12 g"


def test_ocr_number_corrections_do_not_change_nutrition_values():
    assert normalize_text("s0dium 12.50 mg; pr0tein 4.1 g") == "sodium 12.50 mg; protein 4.1 g"
    assert normalize_text("Saturated Fat5g Energy 425kcal") == "saturated fat5g energy 425kcal"


def test_sugar_only_panel_without_heading_keeps_its_basis_and_value():
    raw = "Per 100 g\nTotal Sugars 35 g"
    assert parse_label_text(raw)["nutrition_text"] == raw


def test_nutrition_heading_with_ocr_space_is_supported():
    assert "Sugar 35 g" in parse_label_text("Nutr ition Facts per 100 g\nSugar 35 g")["nutrition_text"]


def test_ocr_panel_body_before_heading_is_preserved_with_explicit_marker():
    text = "Amount Per Serving\nTotal Fat 6g\nSaturated Fat 3.5g\nNutrition Facts\nServing size 15 ml\nIngredients: cream"
    result = parse_label_text(text)
    assert "Total Fat 6g" in result["nutrition_text"]
    assert "Serving size 15 ml" in result["nutrition_text"]
    assert "cream" not in result["nutrition_text"]


def test_unmarked_preamble_is_not_added_to_nutrition_panel():
    result = parse_label_text("Ingredients sugar 10g\nNutrition Facts per 100g\nSodium 100 mg")
    assert "sugar" not in result["nutrition_text"]


def test_parenthesized_contains_does_not_truncate_ingredient_paragraph():
    raw = "Ingredients: sorbitol, gum base (contains soybean lecithin),\nthickeners (414, 1401), humectant (422).\nContains: Soy"
    parsed = parse_label_text(raw)
    assert "soybean lecithin" in parsed["ingredient_text"]
    assert "humectant (422)" in parsed["ingredient_text"]
    assert parsed["contains_text"] == "Soy"
    damaged = parse_label_text("Ingredients: gum base (soy lecithin\nContains: Soy")
    assert damaged["contains_text"] == "Soy"

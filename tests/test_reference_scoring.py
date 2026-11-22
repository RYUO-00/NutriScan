"""Real label syntax regression; values are the user-supplied reference transcript."""
import pytest
from io import BytesIO

import app as app_module
import config
from scoring import calculate_health_score

from nutrition import parse_nutrition
from parser import parse_label_text


NUTELLA_REFERENCE = """Nutrition Facts
about 10 servings per container
Serv. size
2 tbsp (37g)
Amount/serving
Calories 200
Total Fat 11g 14%
Saturated Fat 4g 20%
Trans Fat 0g
Sodium 15mg 1%
Potassium 170mg 4%
Total Sugars 21g
Includes 19g Added Sugars 38%
Protein 2g
Ingredients: sugar, palm oil, hazelnuts, skim milk
Contains: tree nuts, milk
"""


def test_container_is_not_an_allergen_heading():
    parsed = parse_label_text(NUTELLA_REFERENCE)
    assert "Saturated Fat 4g" in parsed["nutrition_text"]
    assert "tree nuts, milk" in parsed["contains_text"]
    assert "Calories" not in parsed["contains_text"]


def test_nutella_reference_extracts_every_declared_value_and_serving_basis():
    parsed = parse_label_text(NUTELLA_REFERENCE)
    values = {item["name"]: item for item in parse_nutrition(parsed["nutrition_text"], context_text=parsed["raw_text"])}
    expected = {"energy": (200, "kcal"), "total_fat": (11, "g"), "saturated_fat": (4, "g"),
                "trans_fat": (0, "g"), "sodium": (15, "mg"), "potassium": (170, "mg"),
                "sugar": (21, "g"), "added_sugar": (19, "g"), "protein": (2, "g")}
    assert set(values) == set(expected)
    for key, (amount, unit) in expected.items():
        item = values[key]
        assert item["original_value"] == amount
        assert item["original_unit"] == unit
        assert item["original_basis"] == "per_serving"
        assert item["serving_size"]["amount"] == 37
        assert item["value"] == pytest.approx(amount * 100 / 37, abs=0.001)
    assert values["saturated_fat"]["value"] == pytest.approx(10.811, abs=0.001)
    assert values["potassium"]["status"] == "Informational"


HEALTHY = "Per 100 g\nTotal Fat 1 g\nSaturated Fat 0.2 g\nTrans Fat 0 g\nSodium 10 mg\nTotal Sugars 2 g"
# Manufacturer reference, checked 20 Nov 2026; 150 g plain nonfat yogurt variant:
# https://usa.fage/products/yogurt/fage-total-0
HEALTHY_MANUFACTURER_LABEL = "Nutrition Facts\nServing size 1 container (150g)\nAmount/Serving\nCalories 80\nTotal Fat 0g\nSaturated Fat 0g\nTrans Fat 0g\nSodium 55mg\nTotal Sugars 5g\nIncludes 0g Added Sugars\nProtein 16g\nPotassium 230mg"


@pytest.mark.parametrize("text,expected,status", [
    pytest.param(NUTELLA_REFERENCE, 55, "sufficient", id="nutella-reference"),
    pytest.param(HEALTHY_MANUFACTURER_LABEL, 100, "sufficient", id="healthy-profile"),
    pytest.param(HEALTHY.replace("Total Sugars 2 g", "Total Sugars 35 g"), 85, "sufficient", id="high-sugar"),
    pytest.param(HEALTHY.replace("Sodium 10 mg", "Sodium 900 mg"), 85, "sufficient", id="high-sodium"),
    pytest.param("Nutrition Facts\nTotal Fat ??\nSugar ??\nSodium unreadable", None, "insufficient", id="unreadable"),
    pytest.param(HEALTHY.replace("Trans Fat 0 g\n", "").replace("Total Sugars 2 g", "Total Sugars 35 g"), 85, "provisional", id="missing-nutrient"),
    pytest.param(HEALTHY.replace("Total Sugars 2 g", "Total Sugars 35 g\nTotal Sugars 35 g"), 85, "sufficient", id="duplicate-reading"),
    pytest.param(NUTELLA_REFERENCE.split("Ingredients:")[0], 55, "sufficient", id="no-ingredients"),
])
def test_reference_profiles_score_deterministically_through_saved_reports(tmp_path, monkeypatch, text, expected, status):
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(config, "PROCESSED_DIR", tmp_path / "uploads" / "processed")
    monkeypatch.setattr(config, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.setattr(app_module, "recognize_text", lambda *_args: {
        "text": text, "mean_confidence": 95, "retried": False, "attempt_count": 1,
        "psm": 6, "used_original": False, "attempts": [],
    })
    client = app_module.create_app({"TESTING": True}).test_client()
    response = client.post("/scan", data={"image": (BytesIO((config.SAMPLE_LABEL_DIR / "clear_flat.png").read_bytes()), "reference.png", "image/png")}, content_type="multipart/form-data", headers={"Accept": "application/json"})
    assert response.status_code == 200
    result = response.get_json()
    assert (result["health_score"], result["score_status"]) == (expected, status)
    parsed = parse_label_text(text)
    nutrients = parse_nutrition(parsed["nutrition_text"], context_text=text)
    first = calculate_health_score(nutrients=nutrients)
    assert first == calculate_health_score(nutrients=nutrients)
    assert first["health_score"] == expected
    if expected is not None:
        assert sum(item["points"] for item in result["score_breakdown"]) == expected
        summary = app_module._score_summary(result)
        assert summary["starting_score"] - summary["deductions"] + summary["credits"] + summary["adjustment"] == expected
    assert client.get(f"/api/history/{result['scan_id']}").get_json() == result
    html = client.get(f"/history?scan_id={result['scan_id']}").get_data(as_text=True)
    assert "Data coverage:" in html and "Confidence:" in html
    assert f"Data status: {status.title()}" in html
    if expected is not None:
        assert f'class="score-value">{expected}</span>' in html
        assert f"matching the displayed Health Score of {expected}" in html
    else:
        assert "Insufficient data" in html
    if text == NUTELLA_REFERENCE:
        assert result["serving_size"]["amount"] == 37
        assert result["data_completeness"]["coverage_percent"] == 100
        assert [(item["item"], item["points"]) for item in result["score_breakdown"] if item["category"] == "nutrient"] == [("total_fat", -15), ("saturated_fat", -15), ("sugar", -15), ("added_sugar", 0)]


def test_one_missing_reading_does_not_invalidate_four_reliable_low_readings():
    result = calculate_health_score(nutrients=parse_nutrition(HEALTHY.replace("Trans Fat 0 g\n", "")))
    assert result["health_score"] == 100
    assert result["score_status"] == "provisional"
    assert result["data_completeness"]["coverage_percent"] == 80


def test_panel_retry_evidence_remains_visible_after_reopening(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(config, "PROCESSED_DIR", tmp_path / "uploads" / "processed")
    monkeypatch.setattr(config, "HISTORY_PATH", tmp_path / "history.json")
    panel = "Nutrition per 100g\nSugar 35g"
    monkeypatch.setattr(app_module, "recognize_text", lambda *_args: {
        "text": "Ingredients: wheat\nContains: peanut", "mean_confidence": 90,
        "retried": True, "attempt_count": 2, "psm": 11, "used_original": True, "attempts": [],
        "nutrition_ocr": {"text": panel, "mean_confidence": 95, "lines": []},
    })
    client = app_module.create_app({"TESTING": True}).test_client()
    response = client.post("/scan", data={"image": (BytesIO((config.SAMPLE_LABEL_DIR / "clear_flat.png").read_bytes()), "label.png", "image/png")},
                           content_type="multipart/form-data", headers={"Accept": "application/json"})
    result = response.get_json()
    assert result["health_score"] is not None
    html = client.get(f"/history?scan_id={result['scan_id']}").get_data(as_text=True)
    assert "Nutrition panel retry" in html and "Sugar 35g" in html
    assert "A separate closer view of the original" in html


def test_fda_added_sugar_boundary_and_sugar_group_are_not_counted_twice():
    values = parse_nutrition("Serving size 37 g\nPer serving\nAdded Sugars 10 g\nTotal Sugars 10 g")
    assert next(item for item in values if item["name"] == "added_sugar")["status"] == "High"
    result = calculate_health_score(nutrients=values)
    assert result["health_score"] == 85
    assert result["totals"]["nutrient_deduction"] == 15


def test_per_100ml_and_per_serving_liquid_inputs_score_equally():
    direct = parse_nutrition("Per 100 ml\nSugar 12 g\nSaturated Fat 3 g\nSodium 400 mg")
    serving = parse_nutrition("Serving size 250 ml\nPer serving\nSugar 30 g\nSaturated Fat 7.5 g\nSodium 1000 mg")
    assert calculate_health_score(nutrients=direct)["health_score"] == calculate_health_score(nutrients=serving)["health_score"] == 55


def test_unknown_fat_qualifier_does_not_conflict_with_a_clear_total_fat_reading():
    values = parse_nutrition("Per 100 g\nTotal Fat 11 g\nJans Fat 0 g\nSaturated Fat 4 g")
    total = [item for item in values if item["name"] == "total_fat"]
    assert len(total) == 1 and total[0]["value"] == 11 and total[0]["verified"]


def test_serving_metadata_survives_interleaved_columns_and_preceding_headings():
    text = "about 10 servings _ Jans Fat0g\nServ. size Cholesterol <5mg\n___\n2 tbsp (37g) Sodium 15mg\nNutrition Facts\nTotal Fat 11g\nSaturated Fat 4g"
    parsed = parse_label_text(text)
    values = parse_nutrition(parsed["nutrition_text"], context_text=text)
    assert all(item["serving_size"]["amount"] == 37 for item in values)
    assert values[0]["original_basis"] == "per_serving"
    damaged = text.replace("2 tbsp (37g)", "=e (37g):")
    assert parse_nutrition(parse_label_text(damaged)["nutrition_text"], context_text=damaged)[0]["serving_size"]["amount"] == 37
    assert next(item for item in parse_nutrition("Per serving\nIncludes19g Added Sugars 38%") if item["name"] == "added_sugar")["value"] == 19


def test_conflicting_duplicate_only_excludes_the_affected_field():
    values = parse_nutrition(HEALTHY + "\nSodium 900 mg")
    result = calculate_health_score(nutrients=values)
    assert result["score_status"] == "provisional"
    assert result["data_completeness"]["coverage_percent"] == 80
    assert "sodium" in result["data_completeness"]["unverified_nutrients"]


def test_one_unreadable_field_keeps_the_remaining_validated_deductions():
    values = parse_nutrition(HEALTHY.replace("Trans Fat 0 g", "Trans Fat unreadable").replace("Total Sugars 2 g", "Total Sugars 35 g"))
    result = calculate_health_score(nutrients=values)
    assert result["health_score"] == 85 and result["score_status"] == "provisional"
    assert result["data_completeness"]["coverage_percent"] == 80
    assert "trans_fat" in result["data_completeness"]["unverified_nutrients"]


def test_reference_score_uses_configured_weights(monkeypatch):
    monkeypatch.setattr(config, "HIGH_NUTRIENT_DEDUCTION", 9)
    values = parse_nutrition(parse_label_text(NUTELLA_REFERENCE)["nutrition_text"], context_text=NUTELLA_REFERENCE)
    result = calculate_health_score(nutrients=values)
    assert result["health_score"] == config.STARTING_SCORE - 3 * config.HIGH_NUTRIENT_DEDUCTION
    assert sum(item["points"] for item in result["score_breakdown"]) == 73


def test_readable_nutella_reference_image_uses_real_ocr():
    import shutil
    from pathlib import Path
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from ocr import recognize_text
    from preprocess import preprocess_image

    if not (Path(config.TESSERACT_CMD).is_file() or shutil.which("tesseract")):
        pytest.skip("Tesseract is installed separately.")
    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    if not font_path.is_file():
        pytest.skip("The test font is unavailable.")
    image = Image.new("RGB", (1500, 1450), "white")
    ImageDraw.Draw(image).multiline_text((40, 30), NUTELLA_REFERENCE, font=ImageFont.truetype(str(font_path), 40), fill="black", spacing=18)
    prepared = preprocess_image(np.asarray(image)[:, :, ::-1])
    ocr_result = recognize_text(prepared["processed"], prepared["original_gray"])
    nutrient_ocr = ocr_result.get("nutrition_ocr") or ocr_result
    parsed = parse_label_text(nutrient_ocr["text"])
    values = parse_nutrition(parsed["nutrition_text"], ocr_context=nutrient_ocr, context_text=nutrient_ocr["text"])
    assert next(item for item in values if item["name"] == "saturated_fat")["value"] == pytest.approx(4 * 100 / 37)
    score = calculate_health_score(nutrients=values)
    assert score["health_score"] == 55
    assert score["score_status"] == "sufficient"

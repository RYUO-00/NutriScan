
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

import config
import ocr
from preprocess import preprocess_image
from ocr import OCRNoTextError, recognize_text


def _data(words, confidence=80):
    return {
        "text": words,
        "conf": [str(confidence)] * len(words),
        "block_num": [1] * len(words),
        "par_num": [1] * len(words),
        "line_num": list(range(1, len(words) + 1)),
    }


def test_weak_output_retries_with_original_and_keeps_best(monkeypatch):
    calls = []
    outputs = [
        {"text": "short", "mean_confidence": 80.0, "word_confidences": [80.0]},
        {"text": "Ingredients:\nsugar,\nflour,", "mean_confidence": 81.0, "word_confidences": [81.0]},
    ]
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")

    def fake_decode(image, psm):
        calls.append((image, psm))
        return outputs[len(calls) - 1]

    monkeypatch.setattr(ocr, "_decode", fake_decode)
    processed = np.zeros((10, 10), dtype=np.uint8)
    original = np.ones((10, 10), dtype=np.uint8)
    result = recognize_text(processed, original)
    assert result["retried"] is True
    assert result["used_original"] is True
    assert result["text"] == "Ingredients:\nsugar,\nflour,"
    assert calls[0][0] is original
    assert calls[0][1] == config.OCR_PSM
    assert calls[1][1] == config.OCR_RETRY_PSM
    assert calls[1][0].shape == (30, 30)
    assert np.all(calls[1][0] == 1)


def test_empty_output_after_retry_has_friendly_error(monkeypatch):
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", lambda *_args: {"text": "", "mean_confidence": None, "word_confidences": []})
    with pytest.raises(OCRNoTextError, match="No readable label text"):
        recognize_text(np.zeros((5, 5), dtype=np.uint8))


def test_small_unusable_panel_gets_a_bounded_layout_retry(monkeypatch):
    calls = []
    texts = iter(["Nutrition Facts\nTotal Fat 11g", "Sodium 15mg", "Serv. size 2 tbsp (37g)\nPer serving\nTotal Fat 11g\nSaturated Fat 4g"])
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    def decode(image, psm):
        calls.append((image.shape, psm))
        return {"text": next(texts), "mean_confidence": 95, "word_confidences": [95]}
    monkeypatch.setattr(ocr, "_decode", decode)
    result = recognize_text(np.zeros((50, 80), dtype=np.uint8), np.zeros((50, 80), dtype=np.uint8))
    assert result["attempt_count"] == 3 and result["upscaled"]
    assert calls[-1] == ((150, 240), config.OCR_LAYOUT_PSM)
    assert "37g" in result["text"]


def test_retry_prefers_shorter_usable_text_over_long_low_confidence_noise(monkeypatch):
    outputs = iter([
        {"text": "unreadable garbled text " * 30, "mean_confidence": 29, "word_confidences": [29]},
        {"text": "Per 100 g\nSugar 35 g", "mean_confidence": 90, "word_confidences": [90]},
    ])
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", lambda *_args: next(outputs))
    result = recognize_text(np.zeros((10, 10), dtype=np.uint8), np.ones((10, 10), dtype=np.uint8))
    assert result["used_original"] is True
    assert result["text"] == "Per 100 g\nSugar 35 g"
    assert result["mean_confidence"] == 90


def test_unverified_numeric_reading_triggers_retry_despite_high_mean(monkeypatch):
    outputs = iter([
        {"text": "Nutrition Information Per 100 g\nSugar 35 g", "mean_confidence": 95, "word_confidences": [95],
         "lines": [{"text": "Sugar 35 g", "words": [{"text": "35", "confidence": 10}]}]},
        {"text": "Per 100 g\nSugar 35 g", "mean_confidence": 90, "word_confidences": [90]},
    ])
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", lambda *_args: next(outputs))
    result = recognize_text(np.zeros((10, 10), dtype=np.uint8), np.ones((10, 10), dtype=np.uint8))
    assert result["retried"] is True and result["used_original"] is True
    assert result["text"] == "Per 100 g\nSugar 35 g"


def test_panel_crop_requires_a_detected_nutrition_heading():
    image = np.zeros((600, 800), dtype=np.uint8)
    image[50:550, 50:350] = 255
    assert ocr._nutrition_panel_crop(image, []) is None
    attempts = [{"used_original": True, "lines": [{"words": [
        {"text": "Nutrition", "box": [80, 100, 70, 20], "confidence": 95}
    ]}]}]
    crop = ocr._nutrition_panel_crop(image, attempts)
    assert crop is not None and crop.shape == (500, 300)
    attempts[0]["lines"][0]["words"][0]["box"] = [700, 100, 70, 20]
    assert ocr._nutrition_panel_crop(image, attempts) is None


def test_independent_ocr_attempts_must_agree_on_reading_and_basis():
    attempts = [{"text": "Per 100g\nSugar 12g"}, {"text": "Per 100g\nSugar 12g"},
                {"text": "Per 100g\nSugar 1.2g"}]
    ocr._mark_corroborated(attempts)
    assert ["sugar", 12.0, "g", "100g", None, None] in attempts[0]["corroborated_readings"]
    assert ["sugar", 1.2, "g", "100g", None, None] not in attempts[0]["corroborated_readings"]


def test_local_tesseract_english_data_is_available():
    command = config.TESSERACT_CMD
    available = Path(command).is_file() or shutil.which(command) or shutil.which("tesseract")
    if not available:
        pytest.skip("Tesseract is installed separately from Python packages.")
    resolved = ocr._configure_tesseract()
    import pytesseract

    assert "5." in str(pytesseract.get_tesseract_version())
    assert "eng" in pytesseract.get_languages(config="")


def test_clear_sample_label_recognizes_ingredient_and_nutrition_text():
    command = config.TESSERACT_CMD
    if not (Path(command).is_file() or shutil.which(command) or shutil.which("tesseract")):
        pytest.skip("Tesseract is installed separately from Python packages.")
    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    if not font_path.is_file():
        pytest.skip("No test font is available on this machine.")
    image = Image.new("RGB", (1500, 520), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_path), 44)
    draw.text((45, 35), "Ingredients:", fill="black", font=font)
    draw.text((45, 105), "Wheat flour, rice flour, sugar, E 211, salt", fill="black", font=font)
    draw.text((45, 225), "Nutrition Information (per 100 g)", fill="black", font=font)
    draw.text((45, 295), "Energy 425 kcal   Total Fat 15 g   Sugar 12 g", fill="black", font=font)
    result = recognize_text(preprocess_image(np.asarray(image)[:, :, ::-1])["processed"])
    assert "Ingredients" in result["text"]
    assert "Wheat" in result["text"]
    assert result["mean_confidence"] is not None


def test_bundled_sample_ocr_keeps_reconciled_scoring():
    if not (Path(config.TESSERACT_CMD).is_file() or shutil.which(config.TESSERACT_CMD) or shutil.which("tesseract")):
        pytest.skip("Tesseract is installed separately from Python packages.")
    from app import _analyze_label
    from storage import load_knowledge

    prepared = preprocess_image(config.BASE_DIR / "static" / "images" / "sample_label.png")
    result = recognize_text(prepared["processed"], prepared["original_gray"])
    analysis = _analyze_label(result["text"], [], load_knowledge(), result)
    assert analysis["health_score"] == 68
    assert analysis["score_status"] == "sufficient"
    assert sum(row["points"] for row in analysis["score_breakdown"]) == 68


@pytest.mark.parametrize("first_text", ["Per 100g\nSugar 12g", ""])
def test_grayscale_rescue_runs_for_partial_or_empty_ocr_and_preserves_ledger(monkeypatch, first_text):
    from app import _analyze_label
    from storage import load_knowledge

    complete = ("Nutrition Facts\nServing size 37g\nPer serving\n"
                "Total Fat 11g\nSaturated Fat 4g\nTrans Fat 0g\n"
                "Sodium 15mg\nTotal Sugars 21g")
    calls = []
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_nutrition_panel_crop", lambda *_: None)
    def decode(image, psm):
        calls.append((image.shape, psm))
        # Realistic full-page dimensions; only bordered rescue reads the table.
        text = complete if image.shape == (3040, 2440) and psm == 4 else first_text
        return {"text": text, "mean_confidence": 95, "word_confidences": [95]}
    monkeypatch.setattr(ocr, "_decode", decode)
    result = recognize_text(np.zeros((1000, 800), dtype=np.uint8), np.zeros((1000, 800), dtype=np.uint8))
    analysis = _analyze_label(result["text"], [], load_knowledge(), result)
    assert result["psm"] == 4 and result["upscaled"]
    assert result["attempt_count"] <= 6
    assert analysis["score_status"] == "sufficient"
    assert analysis["health_score"] < 100
    assert sum(row["points"] for row in analysis["score_breakdown"]) == analysis["health_score"]
    assert any(item["variant"] == "word_height_grayscale" for item in result["attempts"])


def test_optional_rescue_timeout_retains_valid_partial_reading(monkeypatch):
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_nutrition_panel_crop", lambda *_: None)
    def decode(image, psm):
        if image.shape != (1000, 800):
            raise RuntimeError("Tesseract process timeout")
        return {"text": "Per 100g\nSugar 35g", "mean_confidence": 95, "word_confidences": [95]}
    monkeypatch.setattr(ocr, "_decode", decode)
    result = recognize_text(np.zeros((1000, 800), dtype=np.uint8), np.zeros((1000, 800), dtype=np.uint8))
    assert result["text"] == "Per 100g\nSugar 35g"


def test_serving_corroboration_requires_two_legible_matching_attempts():
    def attempt(size, confidence):
        return {"text": f"Serving size {size}g\nPer serving\nSugar 12g", "mean_confidence": 95,
                "lines": [{"text": f"Serving size {size}g", "words": [{"text": f"{size}g", "confidence": confidence}]}]}
    attempts = [attempt(28, 51), attempt(28, 52), attempt(37, 95)]
    ocr._mark_corroborated(attempts)
    assert attempts[0]["corroborated_serving_sizes"] == [[28.0, "g"]]
    attempts = [attempt(28, 20), attempt(28, 52)]
    ocr._mark_corroborated(attempts)
    assert attempts[0]["corroborated_serving_sizes"] == []


def test_sparse_retry_timeout_does_not_discard_original_text(monkeypatch):
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    def decode(image, psm):
        if psm == config.OCR_RETRY_PSM:
            raise RuntimeError("Tesseract process timeout")
        return {"text": "Per 100g\nSugar 35g", "mean_confidence": 40, "word_confidences": [40]}
    monkeypatch.setattr(ocr, "_decode", decode)
    result = recognize_text(np.zeros((10, 10), dtype=np.uint8), np.zeros((10, 10), dtype=np.uint8))
    assert result["text"] == "Per 100g\nSugar 35g"


def test_panel_without_separate_background_requires_heading_basis_and_several_rows():
    image = np.full((800, 1000), 200, dtype=np.uint8)
    rows = [{"text": "Nutrition Information", "words": [{"text": "Nutrition", "box": [200, 100, 90, 20]}]}]
    for index, name in enumerate(("Total Fat", "Saturated Fat", "Sugar")):
        rows.append({"text": name + " 12g", "words": [
            {"text": name, "box": [200, 160 + 40 * index, 110, 20]},
            {"text": "12g", "box": [450, 160 + 40 * index, 40, 20]}]})
    attempt = {"used_original": True, "text": "Nutrition Information per 100g", "lines": rows}
    crop = ocr._nutrition_panel_crop(image, [attempt])
    assert crop is not None and crop.size < image.size
    attempt["text"] = "Nutrition Information"
    assert ocr._nutrition_panel_crop(image, [attempt]) is None
    attempt["text"] = "Nutrition Information per 100g"
    attempt["lines"] = rows[:2]
    assert ocr._nutrition_panel_crop(image, [attempt]) is None


def test_preparation_warning_survives_retry_which_drops_column_heading():
    from nutrition import comparable_nutrients, parse_nutrition
    attempts = [
        {"text": "Nutrition per 100g\n30g serving with\n200 ml COW'S MILK\nTotal Fat 93g"},
        {"text": "Nutrition per 100g\nTotal Fat 93g"},
    ]
    ocr._mark_corroborated(attempts)
    assert attempts[1]["prepared_columns"] is True
    values = parse_nutrition(attempts[1]["text"], ocr_context=attempts[1])
    assert not comparable_nutrients(values)
    assert "prepared-food column" in values[0]["reason"]


def test_retry_scales_native_grayscale_from_observed_median_word_height(monkeypatch):
    calls = []
    complete = "Per 100g\nTotal Fat 1g\nSaturated Fat 0.1g\nTrans Fat 0g\nSugar 1g\nSodium 10mg"
    def decode(image, psm):
        calls.append((image.copy(), psm))
        text = "Nutrition per 100g\nSugar unreadable" if len(calls) == 1 else complete
        return {"text": text, "mean_confidence": 95, "word_confidences": [95],
                "lines": [{"text": text, "words": [
                    {"text": "Nutrition", "confidence": 95, "box": [0, 0, 70, 10]},
                    {"text": "Sugar", "confidence": 95, "box": [0, 20, 30, 10]},
                    {"text": "Brand", "confidence": 95, "box": [0, 40, 100, 90]}]}]}
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", decode)
    monkeypatch.setattr(ocr, "_nutrition_panel_crop", lambda *_: None)
    result = recognize_text(np.zeros((80, 100), dtype=np.uint8), np.full((800, 1000), 200, dtype=np.uint8))
    assert calls[0][0].shape == (800, 1000) and np.all(calls[0][0] == 200)
    assert result["first_median_word_height"] == 10
    assert result["retry_scale"] == 3
    assert calls[1][0].shape == (2400, 3000)
    assert result["text"] == complete


def test_word_height_scaling_respects_resolution_cap_and_handles_empty_tsv():
    image = np.zeros((1000, 4000), dtype=np.uint8)
    first = {"lines": [{"words": [{"text": "Sugar", "confidence": 95, "box": [0, 0, 30, 5]}]}]}
    scaled, height, scale = ocr._scaled_for_words(image, first)
    assert height == 5
    assert max(scaled.shape) + 2 * config.OCR_RESCUE_BORDER <= config.OCR_MAX_LONG_SIDE
    scaled, height, scale = ocr._scaled_for_words(image, {})
    assert height is None and np.isfinite(scale)


def test_illumination_flattening_reduces_background_gradient_and_preserves_ink():
    image = np.tile(np.linspace(100, 240, 400, dtype=np.uint8), (160, 1))
    image[70:85, 150:220] = 0
    flattened = ocr._flatten_illumination(image)
    assert flattened.dtype == np.uint8 and flattened.shape == image.shape
    assert flattened[10].std() < image[10].std() * 0.3
    assert flattened[75, 180] == 0
    assert not ocr._flatten_illumination(np.zeros((20, 20), dtype=np.uint8)).any()


def test_panel_detection_maps_scaled_retry_boxes_back_to_native_pixels():
    image = np.zeros((600, 800), dtype=np.uint8)
    image[50:550, 50:350] = 255
    attempt = {"used_original": True, "rescaled": True, "upscaled": True,
               "coordinate_scale": 2, "coordinate_border": 20,
               "text": "Nutrition", "lines": [{"words": [
                   {"text": "Nutrition", "box": [180, 220, 140, 40], "confidence": 95}]}]}
    crop = ocr._nutrition_panel_crop(image, [attempt])
    assert crop is not None and crop.shape == (500, 300)


def test_small_observed_words_can_reach_target_height_beyond_legacy_three_times_scale():
    image = np.zeros((200, 400), dtype=np.uint8)
    first = {"lines": [{"words": [{"text": "Sugar", "confidence": 95, "box": [0, 0, 20, 5]}]}]}
    scaled, height, scale = ocr._scaled_for_words(image, first)
    assert height * scale == config.OCR_TARGET_WORD_HEIGHT
    assert scale == 6 and max(scaled.shape) <= config.OCR_MAX_LONG_SIDE

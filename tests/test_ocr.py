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


@pytest.mark.parametrize("primary", ["gray", "legacy_adaptive"])
def test_weak_output_retries_with_original_and_keeps_best(monkeypatch, primary):
    monkeypatch.setattr(config, "OCR_PRIMARY_VARIANT", primary)
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
    assert calls == [(original if primary == "gray" else processed, config.OCR_PSM), (original, config.OCR_RETRY_PSM)]


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

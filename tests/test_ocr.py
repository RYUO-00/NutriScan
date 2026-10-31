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
    assert calls == [(processed, config.OCR_PSM), (original, config.OCR_RETRY_PSM)]


def test_empty_output_after_retry_has_friendly_error(monkeypatch):
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", lambda *_args: {"text": "", "mean_confidence": None, "word_confidences": []})
    with pytest.raises(OCRNoTextError, match="No readable label text"):
        recognize_text(np.zeros((5, 5), dtype=np.uint8))


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

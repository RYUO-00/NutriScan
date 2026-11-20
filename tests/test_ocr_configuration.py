import json
from pathlib import Path
import shlex
import sys

import numpy as np
import pytest
from pytesseract import TesseractError

import config
import ocr
from scripts.benchmark_ocr import text_errors, measure_fields


def data():
    return {"text": ["Sugar", "21g"], "conf": [90, 92], "page_num": [1, 1], "block_num": [2, 2],
            "par_num": [1, 1], "line_num": [3, 3], "left": [0, 100], "top": [10, 10],
            "width": [40, 30], "height": [20, 20]}


def test_optional_missing_model_falls_back_without_changing_system_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OCR_MODELS_DIR", tmp_path)
    monkeypatch.setattr(config, "OCR_TESSDATA_DIR", "")
    assert ocr._model_settings("tessdata_best") == ("installed", None, "optional model unavailable")
    with pytest.raises(ocr.OCRSetupError, match="unavailable"):
        ocr._decode(np.zeros((20, 20), dtype=np.uint8), 6, model="tessdata_best", allow_model_fallback=False)


def test_lstm_model_and_vocabulary_options_preserve_coordinates(tmp_path, monkeypatch):
    model_dir = tmp_path / "best"
    model_dir.mkdir()
    (model_dir / "eng.traineddata").write_bytes(b"test pack")
    calls = []
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", lambda *_args, **kwargs: calls.append(kwargs) or data())
    result = ocr._decode(np.zeros((20, 20), dtype=np.uint8), 11, tessdata_dir=model_dir, vocabulary=True)
    command = calls[0]["config"]
    assert "--oem 1 --psm 11" in command and "--tessdata-dir" in command
    assert "--user-words" in command and "--user-patterns" in command
    assert "whitelist" not in command
    assert result["model"] == "custom" and result["invocations"] == 1
    word = result["lines"][0]["words"][1]
    assert word["box"] == [100, 10, 30, 20]
    assert (word["page"], word["block"], word["line"]) == (1, 2, 3)


def test_broken_optional_pack_retries_installed_pack(tmp_path, monkeypatch):
    (tmp_path / "eng.traineddata").write_bytes(b"invalid")
    calls = []
    def decode(*_args, **kwargs):
        calls.append(kwargs)
        if "--tessdata-dir" in kwargs["config"]:
            raise TesseractError(1, "invalid model")
        return data()
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", decode)
    result = ocr._decode(np.zeros((20, 20), dtype=np.uint8), 6, tessdata_dir=tmp_path)
    assert len(calls) == 2 and result["model"] == "installed" and result["model_fallback"]
    again = ocr._decode(np.zeros((20, 20), dtype=np.uint8), 6, tessdata_dir=tmp_path)
    assert len(calls) == 3 and again["model"] == "installed"


def test_timeout_is_a_friendly_ocr_failure(monkeypatch):
    def timeout(*_args, **_kwargs):
        raise RuntimeError("Tesseract process timeout")
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", timeout)
    with pytest.raises(ocr.OCRNoTextError, match="too long"):
        ocr._decode(np.zeros((20, 20), dtype=np.uint8), 6, model="installed", tessdata_dir="")


def test_ocr_data_paths_with_spaces_are_not_passed_as_literal_quotes(tmp_path):
    path = tmp_path / "food words.txt"
    path.write_text("lecithin", encoding="utf-8")
    try:
        quoted = ocr._quoted_path(path)
    except ocr.OCRSetupError:
        if sys.platform == "win32":
            pytest.skip("This Windows volume does not provide short paths; a clear error is required.")
        raise
    tokens = shlex.split(quoted, posix=sys.platform != "win32")
    assert len(tokens) == 1 and Path(tokens[0]).samefile(path)


def test_food_vocabulary_is_curated_normalized_and_unique():
    words = config.OCR_WORDS_PATH.read_text(encoding="utf-8").splitlines()
    assert len(words) == len(set(words)) and len(words) < 100
    assert all(word.isalpha() and word == word.casefold() for word in words)
    assert {"lecithin", "maltodextrin", "sorbitol"}.issubset(words)


def test_benchmark_distinguishes_ocr_text_and_verified_field_errors():
    assert text_errors("Sugar 21 g", "Sugar 2l g")["char_errors"] == 1
    truth = {"nutrients": {"sugar": {"value": 21, "unit": "g", "basis": "100g"}}}
    reading = {"name": "sugar", "value": 21, "unit": "g", "basis": "100g", "verified": True}
    result = measure_fields(truth, {"nutrients": [{**reading, "verified": False}]}, [reading])
    assert result["parsed_correct"] == 1 and result["verified_correct"] == 0
    result = measure_fields(truth, {"nutrients": [{**reading, "basis": "per_serving"}]}, [])
    assert result["verified_correct"] == 0 and result["verified_wrong"] == 1


def test_model_manifest_has_pinned_checksums():
    manifest = json.loads((config.BASE_DIR / "data/ocr/models.json").read_text(encoding="utf-8"))
    assert set(manifest) == {"tessdata_best", "tessdata_fast", "tessdata"}
    assert all(len(row["commit"]) == 40 and len(row["sha256"]) == 64 for row in manifest.values())


def test_optional_model_download_rejects_a_bad_checksum(tmp_path, monkeypatch):
    from scripts import install_ocr_models
    from io import BytesIO
    monkeypatch.setattr(install_ocr_models.urllib.request, "urlopen", lambda *_args, **_kwargs: BytesIO(b"bad pack"))
    with pytest.raises(ValueError, match="checksum"):
        install_ocr_models.install("tessdata_best", tmp_path)
    assert not list(tmp_path.rglob("*.traineddata"))


def test_full_page_ingredient_result_does_not_force_nutrition_retries(monkeypatch):
    calls = []
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_decode", lambda *_args: calls.append(1) or {
        "text": "Ingredients: sorbitol, maltitol, soybean lecithin\nContains: Soy",
        "mean_confidence": 95, "word_confidences": [95], "seconds": 0.1})
    result = ocr.recognize_text(np.zeros((150, 300), dtype=np.uint8), np.zeros((150, 300), dtype=np.uint8))
    assert len(calls) == result["attempt_count"] == 1


def test_panel_attempts_are_bounded_and_included_in_diagnostics(monkeypatch):
    monkeypatch.setattr(ocr, "_configure_tesseract", lambda: "tesseract")
    monkeypatch.setattr(ocr, "deskew_for_ocr", lambda image: (image, 0))
    monkeypatch.setattr(ocr, "_nutrition_panel_crop", lambda *_args: np.zeros((150, 200), dtype=np.uint8))
    def decode(_image, _psm):
        return {"text": "Nutrition Facts\nPer 100g\nSugar 35g", "mean_confidence": 95,
                "word_confidences": [95], "seconds": 0.1, "model": "installed", "oem": 1}
    monkeypatch.setattr(ocr, "_decode", decode)
    result = ocr.recognize_text(np.zeros((150, 300), dtype=np.uint8), np.zeros((150, 300), dtype=np.uint8))
    assert result["panel_attempt_count"] == 2
    assert result["attempt_count"] == len(result["attempts"]) <= config.OCR_MAX_WHOLE_ATTEMPTS + config.OCR_MAX_PANEL_ATTEMPTS
    assert sum(item["scope"] == "nutrition" for item in result["attempts"]) == 2
    assert result["seconds"] == pytest.approx(result["attempt_count"] * 0.1)


@pytest.mark.parametrize("model", ["installed", "tessdata_best", "tessdata_fast"])
def test_available_models_read_a_known_nutrient_with_lstm(model):
    from PIL import Image, ImageDraw
    from scripts.make_sample_labels import _font
    from nutrition import parse_nutrition
    if ocr._model_settings(model)[2]:
        pytest.skip("Optional trained-data model has not been installed.")
    try:
        ocr._configure_tesseract()
    except ocr.OCRSetupError:
        pytest.skip("Tesseract is installed separately from Python packages.")
    image = Image.new("RGB", (700, 170), "white")
    draw = ImageDraw.Draw(image)
    draw.text((15, 10), "Per 100 g", font=_font(40), fill="black")
    draw.text((15, 80), "Sugar 21 g", font=_font(40), fill="black")
    result = ocr._decode(np.asarray(image), 6, model=model, oem=1, allow_model_fallback=False)
    nutrients = parse_nutrition(result["text"])
    assert any(item["name"] == "sugar" and item["value"] == 21 and item["basis"] == "100g" for item in nutrients)
    assert result["oem"] == 1

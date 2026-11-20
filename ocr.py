"""Tesseract wrapper with confidence capture and bounded layout retries."""

import shutil
import shlex
import sys
import statistics
import math
import time
from pathlib import Path

import pytesseract
import cv2
from pytesseract import Output
from pytesseract.pytesseract import TesseractError, TesseractNotFoundError

import config
from nutrition import comparable_nutrients, parse_nutrition, _label_matches
from parser import parse_label_text
from preprocess import ocr_variant, deskew_for_ocr


class OCRSetupError(RuntimeError):
    """Tesseract is missing or not configured."""


class OCRNoTextError(RuntimeError):
    """Tesseract could not read enough text to create a useful result."""


_FAILED_MODEL_FILES = set()


def _model_signature(directory):
    return tuple((str(path.resolve()), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in (directory / (language + ".traineddata") for language in config.TESSERACT_LANG.split("+")))


def _configure_tesseract():
    configured = str(config.TESSERACT_CMD)
    if Path(configured).is_file():
        pytesseract.pytesseract.tesseract_cmd = configured
        return configured
    on_path = shutil.which(configured) or shutil.which("tesseract")
    if on_path:
        pytesseract.pytesseract.tesseract_cmd = on_path
        return on_path
    raise OCRSetupError(
        "NutriScan could not find Tesseract OCR. Install Tesseract 5 with English language data and set TESSERACT_CMD in config.py."
    )


def _quoted_path(path):
    value = str(Path(path).resolve())
    if any(char in value for char in ('"', '\n', '\r', '\x00')):
        raise OCRSetupError("An OCR configuration path contains unsupported characters.")
    if sys.platform == "win32":
        # pytesseract 0.3.13 uses shlex(posix=False) on Windows, retaining quote
        # characters in argv. Use an existing Windows short path when needed.
        if any(char.isspace() for char in value):
            import ctypes
            buffer = ctypes.create_unicode_buffer(32768)
            if not ctypes.windll.kernel32.GetShortPathNameW(value, buffer, len(buffer)):
                raise OCRSetupError("Use an OCR data folder without spaces on this Windows installation.")
            value = buffer.value
            if any(char.isspace() for char in value):
                raise OCRSetupError("Use an OCR data folder without spaces on this Windows installation.")
        return value
    return shlex.quote(value)


def _model_settings(model=None, tessdata_dir=None):
    requested = config.OCR_MODEL if model is None else model
    directory = tessdata_dir if tessdata_dir is not None else config.OCR_TESSDATA_DIR
    if not directory and requested != "installed":
        if requested not in {"tessdata_best", "tessdata_fast", "tessdata"}:
            raise OCRSetupError("Unknown OCR model. Use installed, tessdata_best, tessdata_fast, or tessdata.")
        directory = config.OCR_MODELS_DIR / requested
    if directory:
        directory = Path(directory)
        if not directory.is_absolute():
            directory = config.BASE_DIR / directory
        if all((directory / (language + ".traineddata")).is_file() for language in config.TESSERACT_LANG.split("+")):
            if _model_signature(directory) in _FAILED_MODEL_FILES:
                return "installed", None, "optional model could not be loaded"
            return requested if requested != "installed" else "custom", directory, None
        return "installed", None, "optional model unavailable"
    return "installed", None, None


def _decode(image, psm, *, model=None, tessdata_dir=None, oem=None, vocabulary=None,
            whitelist=None, allow_model_fallback=True):
    selected_model, directory, fallback = _model_settings(model, tessdata_dir)
    if fallback and not allow_model_fallback:
        raise OCRSetupError("The requested benchmark model is unavailable.")
    engine = config.TESSERACT_OEM if oem is None else oem
    use_words = config.OCR_USE_VOCABULARY if vocabulary is None else vocabulary
    options = f"--oem {engine} --psm {int(psm)}"
    if use_words:
        if config.OCR_WORDS_PATH.is_file():
            options += " --user-words " + _quoted_path(config.OCR_WORDS_PATH)
        if config.OCR_PATTERNS_PATH.is_file():
            options += " --user-patterns " + _quoted_path(config.OCR_PATTERNS_PATH)
    if whitelist is not None:
        if not whitelist or any(char.isspace() or char in "\"'" for char in whitelist):
            raise OCRSetupError("Invalid OCR character restriction.")
        options += " -c tessedit_char_whitelist=" + whitelist
    started = time.perf_counter()
    invocations = 1
    def run(data_directory):
        command = options + (" --tessdata-dir " + _quoted_path(data_directory) if data_directory else "")
        try:
            return pytesseract.image_to_data(image, lang=config.TESSERACT_LANG, config=command,
                                            output_type=Output.DICT, timeout=config.OCR_TIMEOUT_SECONDS)
        except RuntimeError as exc:
            if "timeout" not in str(exc).casefold():
                raise
            raise OCRNoTextError("Text recognition took too long. Try a closer photo with less background.") from exc
    try:
        data = run(directory)
    except TesseractError:
        if directory is None or not allow_model_fallback:
            raise
        data = run(None)
        invocations += 1
        _FAILED_MODEL_FILES.add(_model_signature(directory))
        selected_model, fallback = "installed", "optional model could not be loaded"
    result = _data_result(data)
    result.update(model=selected_model, model_fallback=fallback, oem=engine,
                  seconds=time.perf_counter() - started, invocations=invocations, vocabulary=bool(use_words))
    return result


def _data_result(data):
    """Adapt Tesseract TSV without dropping page/line or word geometry."""
    rows = []
    confidence = []
    lines = []
    last_line = None
    for i, text in enumerate(data.get("text", [])):
        word = str(text).strip()
        if not word:
            continue
        line_key = tuple(data.get(key, [0] * len(data.get("text", [])))[i] for key in ("page_num", "block_num", "par_num", "line_num"))
        if last_line is not None and line_key != last_line:
            rows.append("\n")
        elif rows and rows[-1] != "\n":
            rows.append(" ")
        rows.append(word)
        if line_key != last_line:
            lines.append({"text": "", "words": []})
        last_line = line_key
        score = None
        try:
            score = float(data.get("conf", [])[i])
            if score >= 0:
                confidence.append(score)
            else:
                score = None
        except (IndexError, TypeError, ValueError):
            score = None
        lines[-1]["text"] = (lines[-1]["text"] + " " + word).strip()
        token = {"text": word, "confidence": score}
        token.update(zip(("page", "block", "paragraph", "line"), line_key))
        token["word_id"] = data.get("word_num", [0] * len(data.get("text", [])))[i]
        try:
            token["box"] = [int(data[key][i]) for key in ("left", "top", "width", "height")]
        except (KeyError, IndexError, TypeError, ValueError):
            pass
        lines[-1]["words"].append(token)
    for line in lines:
        scores = [word["confidence"] for word in line["words"] if word["confidence"] is not None]
        line["confidence"] = round(sum(scores) / len(scores), 2) if scores else None
    text = "".join(rows).strip()
    return {
        "text": text,
        "mean_confidence": round(sum(confidence) / len(confidence), 2) if confidence else None,
        "word_confidences": confidence,
        "lines": lines,
    }


def _nutrition_panel_crop(image, attempts):
    """Find a bounded light panel containing an OCR nutrition heading.

    This optional retry never replaces the whole-page OCR used for allergens.
    If no credible panel or heading is found, do not guess where to crop.
    """
    if image is None or len(image.shape) != 2 or min(image.shape) < 100:
        return None
    anchors, nutrient_anchors = [], []
    for attempt in attempts:
        if not attempt.get("used_original") or attempt.get("upscaled") or attempt.get("variant", "").startswith("deskew"):
            continue
        for line in attempt.get("lines", []):
            labels = _label_matches(line.get("text", ""))
            if labels:
                first_box = next((word["box"] for word in line.get("words", []) if word.get("box")), None)
                if first_box:
                    nutrient_anchors.extend((first_box[0], first_box[1], label[3]) for label in labels)
            for word in line.get("words", []):
                box = word.get("box")
                if box and word.get("text", "").casefold().strip(":") in {"nutrition", "nutritional"}:
                    anchors.append((box[0] + box[2] // 2, box[1] + box[3] // 2))
    if not anchors and len({key for _, _, key in nutrient_anchors}) < 3:
        return None
    _, mask = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY)
    kernel = max(3, int(min(image.shape) / 50) | 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (kernel, kernel)))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = image.shape
    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h / (width * height)
        if not (0.05 <= area <= 0.75 and w >= 100 and h >= 100 and w < width * 0.9):
            continue
        supported = {key for ax, ay, key in nutrient_anchors if x <= ax < x + w and y <= ay < y + h}
        if any(x <= ax < x + w and y <= ay < y + h for ax, ay in anchors) or len(supported) >= 3:
            candidates.append((w * h, x, y, w, h))
    if not candidates:
        return None
    _, x, y, w, h = min(candidates)
    return image[y:y + h, x:x + w]


def _mark_corroborated(attempts):
    """Record exact readings independently present in at least two attempts."""
    counts = {}
    for attempt in attempts:
        parsed = parse_label_text(attempt["text"])
        readings = parse_nutrition(parsed["nutrition_text"], context_text=attempt["text"])
        found = set()
        for item in readings:
            if not item.get("verified") or item.get("estimated") or item.get("original_value") is None:
                continue
            serving = item.get("serving_size") or {}
            found.add((item["name"], item["original_value"], item["original_unit"], item["original_basis"], serving.get("amount"), serving.get("unit")))
        for signature in found:
            counts[signature] = counts.get(signature, 0) + 1
    agreement = [list(signature) for signature, count in counts.items() if count >= 2]
    for attempt in attempts:
        attempt["corroborated_readings"] = agreement
        attempt.pop("_assessment", None)


def _assess(item):
    if "_assessment" in item:
        return item["_assessment"]
    import re
    parsed = parse_label_text(item["text"])
    readings = parse_nutrition(parsed["nutrition_text"], ocr_context=item, context_text=item["text"])
    comparable = comparable_nutrients(readings)
    core_count = sum(key in comparable or any(alias in comparable for alias in config.SCORE_NUTRIENT_ALTERNATIVES.get(key, ()))
                     for key in config.SCORE_CORE_NUTRIENTS)
    verified = sum(row.get("verified", False) for row in readings)
    sections = sum(bool(parsed[key]) for key in ("ingredient_text", "contains_text"))
    vocabulary = set(config.OCR_WORDS_PATH.read_text(encoding="utf-8").splitlines()) if config.OCR_WORDS_PATH.is_file() else set()
    words = re.findall(r"[a-z]+", item["text"].casefold())
    meaningful = len(set(words) & vocabulary)
    suspicious = len(re.findall(r"\b\d*[oils]\d+(?:mg|g|kcal)\b", item["text"], re.IGNORECASE))
    has_panel = bool(re.search(r"\bnutri\s*tion(?:al)?\b|\bper\s*100\s*(?:g|ml)\b", item["text"], re.IGNORECASE))
    result = {"key": (core_count, len(comparable), verified, sections, meaningful, -suspicious,
                       item.get("mean_confidence") or 0, len(words)),
              "core_count": core_count, "has_panel": has_panel, "readings": readings,
              "meaningful_words": meaningful, "sections": sections, "suspicious_tokens": suspicious}
    item["_assessment"] = result
    return result


def recognize_text(processed_image, original_gray=None):
    """Recognize the page and only retry when its structure is incomplete."""
    _configure_tesseract()
    attempts, panel_attempts = [], []
    def run(image, psm, variant, *, original=False, upscaled=False, scope="whole", optional=False):
        started = time.perf_counter()
        try:
            item = _decode(image, psm)
        except (TesseractError, TesseractNotFoundError, FileNotFoundError, OCRNoTextError) as exc:
            if not optional:
                raise
            item = {"text": "", "mean_confidence": None, "word_confidences": [], "lines": [],
                    "seconds": time.perf_counter() - started, "error": type(exc).__name__, "invocations": 1}
        item.update(psm=psm, variant=variant, scope=scope, used_original=original, upscaled=upscaled)
        (attempts if scope == "whole" else panel_attempts).append(item)
        return item
    def quality(item):
        return _assess(item)["key"]
    try:
        primary_gray = original_gray is not None and config.OCR_PRIMARY_VARIANT == "gray"
        first = run(original_gray if primary_gray else processed_image, config.OCR_PSM,
                    "gray" if primary_gray else "legacy_adaptive", original=primary_gray)
        first_length = len("".join(first["text"].split()))
        confidence_is_weak = first["mean_confidence"] is not None and first["mean_confidence"] < config.OCR_MIN_CONFIDENCE
        assessment = _assess(first)
        no_usable_panel = assessment["has_panel"] and assessment["core_count"] == 0
        unverified_readings = assessment["has_panel"] and any(row.get("verified") is False for row in assessment["readings"])
        if first_length < config.OCR_WEAK_CHARACTERS or confidence_is_weak or no_usable_panel or unverified_readings:
            retry_image = original_gray if original_gray is not None else processed_image
            run(retry_image, config.OCR_RETRY_PSM, "gray", original=original_gray is not None, optional=True)
        _mark_corroborated(attempts)
        best = max(attempts, key=quality)
        if (original_gray is not None and (_assess(best)["core_count"] < config.SCORE_MIN_CORE_FIELDS
                or (_assess(best)["has_panel"] and any(not row.get("verified") for row in _assess(best)["readings"])))):
            deskewed, angle = deskew_for_ocr(original_gray)
            if angle and min(original_gray.shape) >= 100:
                # A rotated word's axis-aligned box includes its horizontal
                # extent. Remove that tilt contribution before judging type size.
                slope = abs(math.tan(math.radians(angle)))
                heights = [max(1, word["box"][3] - slope * word["box"][2]) for attempt in attempts if attempt.get("used_original") and not attempt.get("upscaled")
                           for line in attempt.get("lines", []) for word in line.get("words", [])
                           if word.get("box") and (word.get("confidence") or 0) >= config.OCR_MIN_CONFIDENCE]
                enlarge = len(heights) >= 8 and statistics.median(heights) < config.OCR_SMALL_TEXT_HEIGHT and max(deskewed.shape) < config.OCR_UPSCALE_LONG_SIDE
                if enlarge:
                    scale = min(config.OCR_UPSCALE_MAX_SCALE, config.OCR_UPSCALE_LONG_SIDE / max(deskewed.shape))
                    deskewed = cv2.resize(deskewed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                item = run(deskewed, config.OCR_PSM, "deskew_upscaled_gray" if enlarge else "deskew_gray",
                           original=True, upscaled=enlarge, optional=True)
                item["deskew_degrees"] = angle
            elif (max(original_gray.shape[:2]) < config.OCR_UPSCALE_LONG_SIDE and quality(best)[0] == 0
                  and (any(row.get("value") is not None for item in attempts for row in _assess(item)["readings"])
                       or (min(original_gray.shape[:2]) >= 100 and (confidence_is_weak or no_usable_panel)))):
                scale = min(config.OCR_UPSCALE_MAX_SCALE, config.OCR_UPSCALE_LONG_SIDE / max(original_gray.shape[:2]))
                enlarged = cv2.resize(original_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                run(enlarged, config.OCR_LAYOUT_PSM, "upscaled_gray", original=True, upscaled=True, optional=True)
            _mark_corroborated(attempts)
            best = max(attempts, key=quality)
            if (_assess(best)["has_panel"] and quality(best)[0] < len(config.SCORE_CORE_NUTRIENTS)
                    and any(not row.get("verified") for row in _assess(best)["readings"])
                    and len(attempts) < config.OCR_MAX_WHOLE_ATTEMPTS and min(original_gray.shape[:2]) >= 100):
                run(ocr_variant(original_gray, "contrast"), config.OCR_PSM, "contrast", original=True, optional=True)
                _mark_corroborated(attempts)
                best = max(attempts, key=quality)
    except (TesseractNotFoundError, FileNotFoundError) as exc:
        raise OCRSetupError(
            "NutriScan could not start Tesseract OCR. Check the executable path in config.py."
        ) from exc
    except TesseractError as exc:
        raise OCRSetupError("Tesseract could not process this image. Try a PNG or JPG with a closer, flatter label.") from exc

    if not best["text"].strip():
        raise OCRNoTextError("No readable label text was found. Try a closer, flatter photo with less glare and clearer lighting.")
    nutrition_ocr = None
    crop = _nutrition_panel_crop(original_gray, attempts)
    if crop is not None and quality(best)[0] < len(config.SCORE_CORE_NUTRIENTS):
        scale = min(config.OCR_UPSCALE_MAX_SCALE, config.OCR_PANEL_UPSCALE_LONG_SIDE / max(crop.shape))
        enlarged = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        _, thresholded = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        run(enlarged, config.OCR_PSM, "panel_gray", original=True, upscaled=scale > 1, scope="nutrition", optional=True)
        if config.OCR_MAX_PANEL_ATTEMPTS > 1:
            run(thresholded, config.OCR_PSM, "panel_otsu", original=True, upscaled=scale > 1, scope="nutrition", optional=True)
        _mark_corroborated(panel_attempts)
        if panel_attempts:
            panel = max(panel_attempts, key=quality)
            if quality(panel)[:3] > quality(best)[:3]:
                nutrition_ocr = {"text": panel["text"], "mean_confidence": panel["mean_confidence"], "lines": panel.get("lines", []),
                                 "corroborated_readings": panel.get("corroborated_readings", [])}
    all_attempts = attempts + panel_attempts
    return {
        "text": best["text"],
        "mean_confidence": best["mean_confidence"],
        "word_confidences": best["word_confidences"],
        "lines": best.get("lines", []),
        "retried": len(all_attempts) > 1,
        "attempt_count": sum(item.get("invocations", 1) for item in all_attempts),
        "whole_attempt_count": len(attempts), "panel_attempt_count": len(panel_attempts),
        "psm": best["psm"],
        "used_original": best["used_original"],
        "upscaled": best.get("upscaled", False),
        "model": best.get("model", "installed"), "oem": best.get("oem", config.TESSERACT_OEM),
        "model_fallback": best.get("model_fallback"), "variant": best["variant"],
        "seconds": sum(item.get("seconds", 0) for item in all_attempts),
        "nutrition_ocr": nutrition_ocr,
        "corroborated_readings": best.get("corroborated_readings", []),
        "attempts": [
            {"psm": item["psm"], "characters": len("".join(item["text"].split())), "mean_confidence": item["mean_confidence"],
             "scope": item["scope"], "variant": item["variant"], "model": item.get("model", "installed"),
             "oem": item.get("oem", config.TESSERACT_OEM), "seconds": round(item.get("seconds", 0), 4),
             "invocations": item.get("invocations", 1), "core_fields": _assess(item)["core_count"], "error": item.get("error"),
             "deskew_degrees": item.get("deskew_degrees")}
            for item in all_attempts
        ],
    }

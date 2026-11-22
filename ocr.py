"""Tesseract wrapper with confidence capture and bounded layout retries."""

import shutil
import shlex
import sys
import time
from preprocess import deskew_for_ocr, ocr_variant
from statistics import median
import re
from pathlib import Path

import pytesseract
import cv2
from pytesseract import Output
from pytesseract.pytesseract import TesseractError, TesseractNotFoundError

import config
from nutrition import _has_prepared_columns, _label_matches, _ocr_uncertainty, comparable_nutrients, parse_nutrition
from parser import parse_label_text


class OCRSetupError(RuntimeError):
    """Tesseract is missing or not configured."""


class OCRNoTextError(RuntimeError):
    """Tesseract could not read enough text to create a useful result."""


_FAILED_MODEL_FILES = set()

def _model_signature(directory):
    return tuple((str(path.resolve()), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in (directory / (language + ".traineddata") for language in config.TESSERACT_LANG.split("+")))


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


def _scaled_for_words(image, first):
    """Target the observed text size; never derive scale from score or product."""
    heights = [word["box"][3] for line in first.get("lines", [])
               for word in line.get("words", [])
               if word.get("box") and word["box"][3] > 0
               and re.search(r"[a-z0-9]", word.get("text", ""), re.IGNORECASE)
               and (word.get("confidence") or 0) >= config.OCR_MIN_CONFIDENCE]
    word_height = float(median(heights)) if heights else None
    desired = (config.OCR_TARGET_WORD_HEIGHT / word_height if word_height
               else min(config.OCR_UPSCALE_MAX_SCALE, config.OCR_RESCUE_LONG_SIDE / max(image.shape[:2])))
    scale = min(desired,
                (config.OCR_MAX_LONG_SIDE - 2 * config.OCR_RESCUE_BORDER) / max(image.shape[:2]))
    scaled = image if scale == 1 else cv2.resize(
        image, None, fx=scale, fy=scale,
        interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA,
    )
    return scaled, word_height, scale


def _flatten_illumination(gray):
    """Divide out slow background brightness variation, preserving dark ink."""
    background = cv2.GaussianBlur(gray, (0, 0), config.OCR_ILLUMINATION_SIGMA)
    return cv2.divide(gray, cv2.max(background, 1), scale=255)


def _nutrition_panel_crop(image, attempts):
    """Find a bounded light panel containing an OCR nutrition heading.

    This optional retry never replaces the whole-page OCR used for allergens.
    If no credible panel or heading is found, do not guess where to crop.
    """
    if image is None or len(image.shape) != 2 or min(image.shape) < 100:
        return None
    # Retry TSV coordinates are in the rescaled image. Map geometry back to
    # native grayscale before panel detection; do not discard useful headings.
    native_attempts = []
    for attempt in attempts:
        if not attempt.get("used_original") or attempt.get("deskew_degrees"):
            continue
        if (attempt.get("upscaled") or attempt.get("rescaled")) and "coordinate_scale" not in attempt:
            continue
        scale = attempt.get("coordinate_scale", 1)
        border = attempt.get("coordinate_border", 0)
        rows = []
        for row in attempt.get("lines", []):
            words = []
            for word in row.get("words", []):
                mapped = dict(word)
                if word.get("box"):
                    x, y, w, h = word["box"]
                    mapped["box"] = [round((x - border) / scale), round((y - border) / scale),
                                     round(w / scale), round(h / scale)]
                words.append(mapped)
            rows.append({**row, "words": words})
        native_attempts.append({**attempt, "lines": rows, "upscaled": False, "rescaled": False})
    attempts = native_attempts
    anchors = []
    for attempt in attempts:
        if not attempt.get("used_original") or attempt.get("upscaled") or attempt.get("rescaled"):
            continue
        for line in attempt.get("lines", []):
            for word in line.get("words", []):
                box = word.get("box")
                if box and word.get("text", "").casefold().strip(":") in {"nutrition", "nutritional"}:
                    anchors.append((box[0] + box[2] // 2, box[1] + box[3] // 2))
    if not anchors:
        return None
    detect_scale = min(1.0, config.PREPROCESS_LONG_SIDE / max(image.shape))
    detection = image if detect_scale == 1 else cv2.resize(
        image, None, fx=detect_scale, fy=detect_scale, interpolation=cv2.INTER_AREA)
    _, mask = cv2.threshold(detection, 180, 255, cv2.THRESH_BINARY)
    kernel = max(3, int(min(detection.shape) / 50) | 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (kernel, kernel)))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = image.shape
    candidates = []
    for contour in contours:
        x, y, w, h = (round(value / detect_scale) for value in cv2.boundingRect(contour))
        area = w * h / (width * height)
        if not (0.05 <= area <= 0.75 and w >= 100 and h >= 100 and w < width * 0.9):
            continue
        if any(x <= ax < x + w and y <= ay < y + h for ax, ay in anchors):
            candidates.append((w * h, x, y, w, h))
    if not candidates:
        # Some panels share the packaging background and have no separate light
        # rectangle. Bound a retry using OCR heading + nutrient row coordinates.
        # At least three named rows and an explicit basis/serving declaration
        # are required; never search arbitrary image regions for plausible data.
        for attempt in attempts:
            if not attempt.get("used_original") or attempt.get("upscaled") or attempt.get("rescaled"):
                continue
            if not any(token in attempt.get("text", "").casefold() for token in ("serving", "per 100", "per100")):
                continue
            nutrient_rows = [row for row in attempt.get("lines", []) if _label_matches(row.get("text", ""))]
            if len(nutrient_rows) < 3:
                continue
            boxes = [word["box"] for row in nutrient_rows for word in row.get("words", []) if word.get("box")]
            if not boxes:
                continue
            x0 = max(0, min(box[0] for box in boxes) - config.OCR_RESCUE_BORDER)
            x1 = min(width, max(box[0] + box[2] for box in boxes) + config.OCR_RESCUE_BORDER)
            y0 = max(0, min(ay for _ax, ay in anchors) - config.OCR_RESCUE_BORDER * 2)
            y1 = min(height, max(box[1] + box[3] for box in boxes) + config.OCR_RESCUE_BORDER)
            if (x1 - x0 >= 100 and y1 - y0 >= 100
                    and (x1 - x0) * (y1 - y0) < width * height * 0.75
                    and any(x0 <= ax < x1 and y0 <= ay < y1 for ax, ay in anchors)):
                return image[y0:y1, x0:x1]
        return None
    _, x, y, w, h = min(candidates)
    return image[y:y + h, x:x + w]


def _mark_corroborated(attempts):
    """Record exact readings independently present in at least two attempts."""
    counts = {}
    prepared_columns = any(item.get("prepared_columns") or
                           _has_prepared_columns(parse_label_text(item["text"])["nutrition_text"])
                           for item in attempts)
    for item in attempts:
        item["prepared_columns"] = prepared_columns
    serving_counts = {}
    for attempt in attempts:
        parsed = parse_label_text(attempt["text"])
        readings = parse_nutrition(parsed["nutrition_text"], context_text=attempt["text"])
        sizes = {(item["serving_size"]["amount"], item["serving_size"]["unit"]): item["serving_size"]
                 for item in readings if item.get("serving_size")}
        for signature, size in sizes.items():
            if not _ocr_uncertainty(size["source_span"], attempt, number=f"{size['amount']:g}",
                                    minimum=config.OCR_MIN_CONFIDENCE):
                serving_counts[signature] = serving_counts.get(signature, 0) + 1
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
        attempt.pop("_assessment", None)
        attempt["corroborated_readings"] = agreement
        attempt["corroborated_serving_sizes"] = [list(size) for size, count in serving_counts.items() if count >= 2]


def recognize_text(processed_image, original_gray=None):
    """Recognize the page, with bounded optional nutrition-panel retries."""
    _configure_tesseract()
    attempts, panel_attempts = [], []
    def decode(image, psm, *, scope="whole"):
        started = time.perf_counter()
        item = _decode(image, psm)
        item.setdefault("seconds", time.perf_counter() - started)
        item.setdefault("invocations", 1)
        item["scope"] = scope
        item.setdefault("psm", psm)
        if scope == "nutrition":
            panel_attempts.append(item)
        return item
    source = original_gray if original_gray is not None else processed_image
    if max(source.shape[:2]) > config.OCR_MAX_LONG_SIDE:
        cap_scale = config.OCR_MAX_LONG_SIDE / max(source.shape[:2])
        source = cv2.resize(source, None, fx=cap_scale, fy=cap_scale, interpolation=cv2.INTER_AREA)
    if original_gray is not None:
        original_gray = source
    def quality(item):
        parsed = parse_label_text(item["text"])
        readings = parse_nutrition(parsed["nutrition_text"], ocr_context=item, context_text=item["text"])
        confidence = item["mean_confidence"]
        usable = comparable_nutrients(readings)
        core = set(usable).intersection(config.SCORE_CORE_NUTRIENTS)
        if "salt" in usable:
            core.add("sodium")
        return (len(core), len(usable), confidence is not None and confidence >= config.OCR_MIN_CONFIDENCE,
                confidence or 0, len("".join(item["text"].split())))
    try:
        first = decode(source, config.OCR_PSM)
        first.update(psm=config.OCR_PSM, used_original=original_gray is not None,
                     variant="grayscale_native" if original_gray is not None else "processed_compatibility")
        attempts.append(first)
        retry_image, median_height, retry_scale = _scaled_for_words(source, first)
        first_length = len("".join(first["text"].split()))
        confidence_is_weak = first["mean_confidence"] is not None and first["mean_confidence"] < config.OCR_MIN_CONFIDENCE
        parsed = parse_label_text(first["text"])
        readings = parse_nutrition(parsed["nutrition_text"], ocr_context=first, context_text=first["text"])
        no_usable_panel = _assess(first)["has_panel"] and not comparable_nutrients(readings)
        unverified_readings = _assess(first)["has_panel"] and any(item.get("verified") is False and item["name"] not in config.INFORMATIONAL_NUTRIENTS for item in readings)
        if first_length < config.OCR_WEAK_CHARACTERS or confidence_is_weak or no_usable_panel or unverified_readings:
            try:
                retry = decode(retry_image, config.OCR_RETRY_PSM)
            except (TesseractError, RuntimeError, OCRNoTextError):
                retry = None
            if retry is not None:
                retry["psm"] = config.OCR_RETRY_PSM
                retry.update(used_original=original_gray is not None, upscaled=retry_scale > 1,
                             rescaled=retry_scale != 1, coordinate_scale=retry_scale, variant="word_height_sparse")
                attempts.append(retry)
        # A small multi-column panel can stay unreadable with both block and
        # sparse layouts. One bounded automatic-layout attempt uses actual pixels.
        has_numeric_reading = any(reading.get("value") is not None for item in attempts
                                  for reading in parse_nutrition(parse_label_text(item["text"])["nutrition_text"], context_text=item["text"]))
        if (original_gray is not None and max(original_gray.shape[:2]) < config.OCR_UPSCALE_LONG_SIDE
                and (max(quality(item)[0] for item in attempts) == 0
                     or (min(original_gray.shape[:2]) >= 100 and max(quality(item)[0] for item in attempts) < config.SCORE_MIN_CORE_FIELDS))
                and (has_numeric_reading or (min(original_gray.shape[:2]) >= 100 and (confidence_is_weak or no_usable_panel)))):
            enlarged, angle = deskew_for_ocr(retry_image)
            try:
                layout = decode(enlarged, config.OCR_PSM if angle else config.OCR_LAYOUT_PSM)
            except (TesseractError, RuntimeError, OCRNoTextError):
                layout = None
            if layout is not None:
                layout.update(psm=config.OCR_PSM if angle else config.OCR_LAYOUT_PSM, used_original=True, upscaled=retry_scale > 1,
                              rescaled=retry_scale != 1, coordinate_scale=retry_scale, variant="deskew_gray" if angle else "word_height_layout", deskew_degrees=angle)
                attempts.append(layout)
    except (TesseractNotFoundError, FileNotFoundError) as exc:
        raise OCRSetupError(
            "NutriScan could not start Tesseract OCR. Check the executable path in config.py."
        ) from exc
    except (TesseractError, RuntimeError, OCRNoTextError) as exc:
        raise OCRSetupError("Tesseract could not process this image. Try a PNG or JPG with a closer, flatter label.") from exc

    _mark_corroborated(attempts)
    best = max(attempts, key=quality)
    nutrition_ocr = None
    crop = _nutrition_panel_crop(original_gray, attempts)
    if crop is not None and quality(best)[0] < len(config.SCORE_CORE_NUTRIENTS):
        enlarged, _panel_height, scale = _scaled_for_words(crop, first)
        _, thresholded = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        panel_variants = [(enlarged, config.OCR_PSM, "panel_gray"),
                          (thresholded, config.OCR_PSM, "panel_otsu")]
        if config.OCR_MAX_PANEL_ATTEMPTS > 2:
            panel_variants.extend([(enlarged, config.OCR_RESCUE_PSMS[-1], "panel_column"),
                                   (_flatten_illumination(enlarged), config.OCR_RESCUE_PSMS[-1], "panel_flattened")])
        for panel_image, panel_psm, panel_variant in panel_variants[:config.OCR_MAX_PANEL_ATTEMPTS]:
            try:
                item = decode(panel_image, panel_psm, scope="nutrition")
            except (TesseractError, TesseractNotFoundError, FileNotFoundError, RuntimeError, OCRNoTextError):
                continue  # Keep earlier readable panel evidence.
            item.update(variant=panel_variant, used_original=True, upscaled=scale > 1,
                        prepared_columns=any(attempt.get("prepared_columns") for attempt in attempts))
        _mark_corroborated(panel_attempts)
        if panel_attempts:
            panel = max(panel_attempts, key=quality)
            if quality(panel)[0] > quality(best)[0]:
                nutrition_ocr = {"text": panel["text"], "mean_confidence": panel["mean_confidence"], "lines": panel.get("lines", []),
                                 "corroborated_readings": panel.get("corroborated_readings", []),
                                 "corroborated_serving_sizes": panel.get("corroborated_serving_sizes", []),
                                 "prepared_columns": panel.get("prepared_columns", False)}
    # Thresholding can erase small decimals and make a printed g look like 9.
    # A partial panel must not suppress a retry simply because one field scored.
    # Retry the complete grayscale page with a border in two bounded layouts;
    # select a coherent attempt instead of combining unrelated table columns.
    current = nutrition_ocr or best
    ingredient_page = bool(parse_label_text(best["text"])["ingredient_text"]) and not _assess(best)["has_panel"]
    if (not ingredient_page and original_gray is not None and min(original_gray.shape[:2]) >= 100
            and quality(current)[0] < len(config.SCORE_CORE_NUTRIENTS)):
        scale = retry_scale
        enlarged = retry_image
        border = config.OCR_RESCUE_BORDER
        enlarged = cv2.copyMakeBorder(enlarged, border, border, border, border,
                                      cv2.BORDER_CONSTANT, value=255)
        flattened = _flatten_illumination(retry_image)
        flattened = cv2.copyMakeBorder(flattened, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
        variants = [(enlarged, psm, "word_height_grayscale") for psm in config.OCR_RESCUE_PSMS]
        variants.append((flattened, config.OCR_PSM, "illumination_flattened"))
        for variant_image, psm, variant in variants:
            try:
                rescue = decode(variant_image, psm)
            except (TesseractError, TesseractNotFoundError, FileNotFoundError, RuntimeError, OCRNoTextError):
                continue  # An optional timeout must not discard readable OCR.
            rescue.update(psm=psm, used_original=True, upscaled=scale > 1,
                          rescaled=scale != 1, coordinate_scale=scale, coordinate_border=border, variant=variant)
            attempts.append(rescue)
        _mark_corroborated(attempts)
        if nutrition_ocr and any(item.get("prepared_columns") for item in attempts):
            nutrition_ocr["prepared_columns"] = True
        best = max(attempts, key=quality)
        if nutrition_ocr and quality(best) >= quality(nutrition_ocr):
            nutrition_ocr = None
    if not best["text"].strip():
        raise OCRNoTextError("No readable label text was found. Try a closer, flatter photo with less glare and clearer lighting.")
    all_attempts = attempts + panel_attempts
    return {
        "model": best.get("model", "installed"), "oem": best.get("oem", config.TESSERACT_OEM),
        "model_fallback": best.get("model_fallback"), "variant": best.get("variant"),
        "seconds": sum(item.get("seconds", 0) for item in all_attempts),
        "whole_attempt_count": len(attempts), "panel_attempt_count": len(panel_attempts),
        "text": best["text"],
        "mean_confidence": best["mean_confidence"],
        "word_confidences": best["word_confidences"],
        "lines": best.get("lines", []),
        "first_median_word_height": median_height,
        "retry_scale": retry_scale,
        "ocr_width": int(source.shape[1]), "ocr_height": int(source.shape[0]),
        "retried": len(all_attempts) > 1,
        "attempt_count": sum(item.get("invocations", 1) for item in all_attempts),
        "psm": best["psm"],
        "used_original": best["used_original"],
        "upscaled": best.get("upscaled", False),
        "nutrition_ocr": nutrition_ocr,
        "corroborated_readings": best.get("corroborated_readings", []),
        "corroborated_serving_sizes": best.get("corroborated_serving_sizes", []),
        "prepared_columns": best.get("prepared_columns", False),
        "attempts": [
            {"psm": item["psm"], "scope": item.get("scope", "whole"), "variant": item.get("variant", "standard"), "characters": len("".join(item["text"].split())), "mean_confidence": item["mean_confidence"]}
            for item in all_attempts
        ],
    }

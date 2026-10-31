"""Tesseract wrapper with confidence capture and one weak-output retry."""

import shutil
from pathlib import Path

import pytesseract
from pytesseract import Output
from pytesseract.pytesseract import TesseractError, TesseractNotFoundError

import config


class OCRSetupError(RuntimeError):
    """Tesseract is missing or not configured."""


class OCRNoTextError(RuntimeError):
    """Tesseract could not read enough text to create a useful result."""


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


def _decode(image, psm):
    data = pytesseract.image_to_data(
        image,
        lang=config.TESSERACT_LANG,
        config=f"--oem 3 --psm {psm}",
        output_type=Output.DICT,
    )
    rows = []
    confidence = []
    last_line = None
    for i, text in enumerate(data.get("text", [])):
        word = str(text).strip()
        if not word:
            continue
        line_key = tuple(data.get(key, [0] * len(data.get("text", [])))[i] for key in ("block_num", "par_num", "line_num"))
        if last_line is not None and line_key != last_line:
            rows.append("\n")
        elif rows and rows[-1] != "\n":
            rows.append(" ")
        rows.append(word)
        last_line = line_key
        try:
            score = float(data.get("conf", [])[i])
            if score >= 0:
                confidence.append(score)
        except (IndexError, TypeError, ValueError):
            pass
    text = "".join(rows).strip()
    return {
        "text": text,
        "mean_confidence": round(sum(confidence) / len(confidence), 2) if confidence else None,
        "word_confidences": confidence,
    }


def recognize_text(processed_image, original_gray=None):
    """Recognize text; retry once on weak output and return diagnostics."""
    _configure_tesseract()
    attempts = []
    try:
        first = _decode(processed_image, config.OCR_PSM)
        first["psm"] = config.OCR_PSM
        first["used_original"] = False
        attempts.append(first)
        first_length = len("".join(first["text"].split()))
        confidence_is_weak = first["mean_confidence"] is not None and first["mean_confidence"] < config.OCR_MIN_CONFIDENCE
        if first_length < config.OCR_WEAK_CHARACTERS or confidence_is_weak:
            retry_image = original_gray if original_gray is not None else processed_image
            retry = _decode(retry_image, config.OCR_RETRY_PSM)
            retry["psm"] = config.OCR_RETRY_PSM
            retry["used_original"] = original_gray is not None
            attempts.append(retry)
    except (TesseractNotFoundError, FileNotFoundError) as exc:
        raise OCRSetupError(
            "NutriScan could not start Tesseract OCR. Check the executable path in config.py."
        ) from exc
    except TesseractError as exc:
        raise OCRSetupError("Tesseract could not process this image. Try a PNG or JPG with a closer, flatter label.") from exc

    best = max(
        attempts,
        key=lambda item: (len("".join(item["text"].split())), item["mean_confidence"] or 0),
    )
    if not best["text"].strip():
        raise OCRNoTextError("No readable label text was found. Try a closer, flatter photo with less glare and clearer lighting.")
    return {
        "text": best["text"],
        "mean_confidence": best["mean_confidence"],
        "word_confidences": best["word_confidences"],
        "retried": len(attempts) > 1,
        "attempt_count": len(attempts),
        "psm": best["psm"],
        "used_original": best["used_original"],
        "attempts": [
            {"psm": item["psm"], "characters": len("".join(item["text"].split())), "mean_confidence": item["mean_confidence"]}
            for item in attempts
        ],
    }

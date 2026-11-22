"""Controlled Tesseract comparisons; no uploads or history are written.

python scripts/benchmark_ocr.py --mode control --real-dir PATH
python scripts/benchmark_ocr.py --mode matrix --real-dir PATH --output results/ocr_matrix
python scripts/benchmark_ocr.py --mode pipeline --real-dir PATH --output results/ocr_pipeline
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time
import tempfile
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Manifest replay is a separate adapter; legacy model/matrix modes stay intact.
from scripts.benchmark_replay import comparison_rows
if __name__ == "__main__" and "--manifest" in sys.argv:
    from scripts.benchmark_replay import main as replay_main
    replay_main()
    raise SystemExit(0)

import config
import ocr
from app import _analyze_label
from matcher import normalize_term
from nutrition import parse_nutrition
from parser import parse_label_text
from preprocess import preprocess_image, ocr_variant, deskew_for_ocr
from scripts.make_sample_labels import TEXT
from scripts.make_sample_labels import _font
from storage import load_knowledge


def edit_distance(left, right):
    previous = list(range(len(right) + 1))
    for i, item in enumerate(left, 1):
        current = [i]
        for j, other in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (item != other)))
        previous = current
    return previous[-1]


def text_errors(reference, actual):
    # Case/whitespace normalization only; do not repair OCR spelling or digits.
    reference = " ".join(reference.casefold().split())
    actual = " ".join(actual.casefold().split())
    return {"char_errors": edit_distance(reference, actual), "char_count": len(reference),
            "word_errors": edit_distance(reference.split(), actual.split()), "word_count": len(reference.split())}


def _numeric_match(expected, actual):
    value = actual.get("value")
    return (isinstance(value, (float, int)) and math.isfinite(value)
            and actual.get("unit") == expected["unit"] and actual.get("basis") == expected["basis"]
            and math.isclose(value, expected["value"], rel_tol=0.01, abs_tol=0.05))


def measure_fields(truth, analysis, raw_readings):
    expected = truth.get("nutrients", {})
    readings = analysis.get("nutrients", [])
    def correct(items):
        return sum(any(item.get("name") == name and item.get("verified") and not item.get("estimated")
                       and _numeric_match(value, item) for item in items) for name, value in expected.items())
    actual_text = " " + normalize_term(analysis.get("ingredient_text", "")) + " "
    terms = truth.get("ingredient_terms", truth.get("ingredient_tokens", []))
    ingredient_hits = sum(" " + normalize_term(term) + " " in actual_text for term in terms)
    allergens = {item["allergen_group"] for item in analysis.get("allergen_alerts", [])}
    additives = {str(item["ins_code"]) for item in analysis.get("additives", [])}
    expected_allergens, expected_additives = set(truth.get("allergen_groups", [])), set(truth.get("additive_codes", []))
    serving = truth.get("serving_size")
    actual_serving = analysis.get("serving_size") or {}
    return {
        "nutrition_expected": len(expected), "parsed_correct": correct(raw_readings), "verified_correct": correct(readings),
        "verified_wrong": sum(item.get("verified") and not item.get("estimated") and item.get("name") in expected
                              and not _numeric_match(expected[item["name"]], item) for item in readings),
        "ingredient_expected": len(terms), "ingredient_correct": ingredient_hits,
        "allergen_expected": len(expected_allergens), "allergen_correct": len(allergens & expected_allergens),
        "allergen_false": len(allergens - expected_allergens) if truth.get("allergen_exhaustive", True) else None,
        "additive_expected": len(expected_additives), "additive_correct": len(additives & expected_additives),
        "additive_false": len(additives - expected_additives) if truth.get("additive_exhaustive", True) else None,
        "serving_expected": int(serving is not None),
        "serving_correct": int(serving is not None and actual_serving.get("unit") == serving["unit"]
                               and actual_serving.get("amount") == serving["amount"]),
    }


def without_confidence(context):
    return {"mean_confidence": 100, "lines": [
        {"text": line["text"], "confidence": 100, "words": [{**word, "confidence": 100} for word in line.get("words", [])]}
        for line in context.get("lines", [])]}


def dataset(real_dir=None):
    reference = "\n".join(row[0] for row in TEXT) + "\nSynthetic example for OCR testing · not a real product"
    samples = []
    for path in sorted(config.GROUND_TRUTH_DIR.glob("*.json")):
        truth = json.loads(path.read_text(encoding="utf-8"))
        truth.update(reference_text=reference, serving_size={"amount": 30, "unit": "g"})
        samples.append((config.SAMPLE_LABEL_DIR / truth["image"], truth, "synthetic"))
    if real_dir:
        manifest = json.loads((config.BASE_DIR / "tests/ocr_real_labels.json").read_text(encoding="utf-8"))
        for truth in manifest["labels"]:
            path = Path(real_dir) / truth["image"]
            if not path.is_file():
                raise FileNotFoundError(f"Missing real-label input: {truth['image']}")
            samples.append((path, truth, "real"))
    return samples


def variant(gray, prepared, name):
    if name == "legacy":
        return prepared["processed"]
    if name in {"deskew", "deskew_scaled"}:
        output = deskew_for_ocr(gray)[0]
        if name == "deskew_scaled":
            import cv2
            scale = min(config.OCR_UPSCALE_MAX_SCALE, config.OCR_UPSCALE_LONG_SIDE / max(output.shape))
            output = cv2.resize(output, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return output
    return ocr_variant(gray, name)


def write_results(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(result, handle, indent=2, ensure_ascii=True)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def numeric_probe(model):
    """Restrict characters only on an explicitly numeric synthetic line."""
    from PIL import Image, ImageDraw
    import numpy as np
    image = Image.new("RGB", (850, 95), "white")
    reference = "21.4 g 350 mg 0.1 g"
    ImageDraw.Draw(image).text((15, 15), reference, font=_font(42), fill="black")
    rows = []
    for restriction in (None, "0123456789.,gmkcalKJML<>"):
        started = time.perf_counter()
        result = ocr._decode(np.asarray(image), 7, model=model, oem=1, vocabulary=False,
                             whitelist=restriction, allow_model_fallback=False)
        rows.append({"model": model, "whitelist": restriction, "text": result["text"],
                     "seconds": time.perf_counter() - started, **text_errors(reference, result["text"])})
    return rows


@contextmanager
def settings(**values):
    previous = {key: getattr(config, key) for key in values}
    try:
        for key, value in values.items():
            setattr(config, key, value)
        yield
    finally:
        for key, value in previous.items():
            setattr(config, key, value)


def aggregate(rows):
    def ratio(numerator, denominator):
        n, d = sum(row.get(numerator, 0) for row in rows), sum(row.get(denominator, 0) for row in rows)
        return n / d if d else None
    return {
        "cer": ratio("char_errors", "char_count"), "wer": ratio("word_errors", "word_count"),
        "parsed_accuracy": ratio("parsed_correct", "nutrition_expected"),
        "verified_accuracy": ratio("verified_correct", "nutrition_expected"),
        "ingredient_recall": ratio("ingredient_correct", "ingredient_expected"),
        "allergen_recall": ratio("allergen_correct", "allergen_expected"),
        "additive_recall": ratio("additive_correct", "additive_expected"),
        "serving_accuracy": ratio("serving_correct", "serving_expected"),
        "verified_wrong": sum(row.get("verified_wrong", 0) for row in rows),
        "ocr_seconds": statistics.mean(row["ocr_seconds"] for row in rows),
        "full_seconds": statistics.mean(row["full_seconds"] for row in rows),
        "attempts": statistics.mean(row["attempt_count"] for row in rows),
        "failures": sum(row.get("error") is not None for row in rows),
    }


def report(result):
    def percent(value):
        return "not measured" if value is None else f"{value:.1%}"
    lines = ["# Tesseract OCR benchmark", "", result["method"], "",
             "CER/WER apply only to the five synthetic images with complete transcripts. Real-photo metrics use only manually checked visible fields. Parsed accuracy excludes OCR confidence admission; verified accuracy applies the full application pipeline. Both require correct nutrient, value, unit and basis (1% relative or 0.05 absolute tolerance). Missing/unverified readings are misses, never zero. Ingredient/additive/allergen metrics are recall, with false positives reported per image when references are exhaustive. The small development set is not a held-out or representative performance claim.", "",
             "| Profile | CER | WER | Parsed fields | Verified fields | Wrong verified | Ingredients | Allergens | Serving | OCR s | Full s | Attempts | Failures |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name in dict.fromkeys(row["profile"] for row in result["rows"]):
        a = aggregate([row for row in result["rows"] if row["profile"] == name])
        lines.append(f"| {name} | {percent(a['cer'])} | {percent(a['wer'])} | {percent(a['parsed_accuracy'])} | {percent(a['verified_accuracy'])} | {a['verified_wrong']} | {percent(a['ingredient_recall'])} | {percent(a['allergen_recall'])} | {percent(a['serving_accuracy'])} | {a['ocr_seconds']:.3f} | {a['full_seconds']:.3f} | {a['attempts']:.2f} | {a['failures']} |")
    lines += ["", "## Per-image evidence", "", "| Profile | Image | Parsed / verified fields | Wrong verified | OCR s | Score / status | Error |",
              "|---|---|---:|---:|---:|---|---|"]
    for row in result["rows"]:
        lines.append(f"| {row['profile']} | {row['image']} | {row['parsed_correct']} / {row['verified_correct']} of {row['nutrition_expected']} | {row['verified_wrong']} | {row['ocr_seconds']:.3f} | {row.get('health_score')} / {row.get('score_status')} | {row.get('error') or ''} |")
    lines += ["", "Each pytesseract call launches a Tesseract subprocess and includes model loading, OCR, TSV parsing and process overhead. Isolated model-loading time and Tesseract subprocess peak RAM are not measured. Optional Python peak memory excludes OpenCV native allocations and the OCR child process. Model identity/file size and input hashes are in the JSON sidecar. Single-pass tests are controlled recognition comparisons, not the bounded runtime retry policy. Pipeline times cover preprocessing and analysis but exclude upload/storage. Timings are descriptive local measurements and can vary with CPU load.", ""]
    if result.get("numeric_probe"):
        lines += ["## Numeric-only region probe", "", "| Model | Restriction | CER | WER | Seconds |", "|---|---|---:|---:|---:|"]
        for row in result["numeric_probe"]:
            lines.append(f"| {row['model']} | {'numeric/units' if row['whitelist'] else 'none'} | {row['char_errors']/row['char_count']:.1%} | {row['word_errors']/row['word_count']:.1%} | {row['seconds']:.3f} |")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["control", "matrix", "pipeline"], default="control")
    parser.add_argument("--models", nargs="+", default=["installed", "tessdata_best", "tessdata_fast"])
    parser.add_argument("--real-dir", type=Path)
    parser.add_argument("--output", type=Path, default=config.RESULTS_DIR / "ocr_models")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--python-memory", action="store_true")
    parser.add_argument("--variants", nargs="+", default=["gray", "contrast", "legacy", "otsu", "adaptive", "deskew", "deskew_scaled"])
    parser.add_argument("--psms", nargs="+", type=int, default=[6, 11, 3])
    parser.add_argument("--numeric-probe", action="store_true")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    ocr._configure_tesseract()
    source_hashes = {name: hashlib.sha256((config.BASE_DIR / name).read_bytes()).hexdigest()
                     for name in ("config.py", "ocr.py", "preprocess.py", "nutrition.py", "parser.py", "app.py",
                                  "matcher.py", "scoring.py", "scripts/benchmark_ocr.py", "scripts/make_sample_labels.py",
                                  "tests/ocr_real_labels.json")}
    models = {}
    for model in args.models:
        selected, directory, _ = ocr._model_settings(model)
        if directory:
            path = directory / "eng.traineddata"
        else:
            # --list-langs identifies the actual installed search directory.
            import subprocess
            listed = subprocess.check_output([ocr.pytesseract.pytesseract.tesseract_cmd, "--list-langs"], text=True)
            match = re.search(r'in "([^"]+)"', listed)
            path = Path(match.group(1)) / "eng.traineddata" if match else Path()
        models[model] = {"resolved": selected, "bytes": path.stat().st_size if path.is_file() else None,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None}
    samples, knowledge, rows = dataset(args.real_dir), load_knowledge(), []
    if args.mode == "matrix":
        profiles = [(f"installed/{v}/psm{p}", "installed", v, p, False) for v in args.variants for p in args.psms]
        profiles += [("installed/gray/psm6/vocabulary", "installed", "gray", 6, True)]
    else:
        profiles = [(model, model, "gray", 6, False) for model in args.models]
    for name, model, variant_name, psm, words in profiles:
        selected, _, fallback = ocr._model_settings(model)
        if fallback:
            raise ocr.OCRSetupError(f"Requested benchmark model is unavailable: {model}")
        for repeat in range(args.repeat):
            for image_path, truth, kind in samples:
                started = time.perf_counter()
                if args.python_memory:
                    tracemalloc.start()
                prepared = preprocess_image(image_path)
                context, analysis, raw_readings, error = {}, {}, [], None
                ocr_started = time.perf_counter()
                try:
                    with settings(OCR_MODEL=model, OCR_USE_VOCABULARY=words, OCR_TESSDATA_DIR="", TESSERACT_OEM=1):
                        if args.mode == "pipeline":
                            context = ocr.recognize_text(prepared["processed"], prepared["original_gray"])
                        else:
                            context = ocr._decode(variant(prepared["original_gray"], prepared, variant_name), psm,
                                                  model=model, oem=1, vocabulary=words, allow_model_fallback=False)
                    seconds = time.perf_counter() - ocr_started
                    analysis = _analyze_label(context["text"], [], knowledge, context)
                    nutrition_context = context.get("nutrition_ocr") or context
                    parsed = parse_label_text(nutrition_context["text"])
                    raw_readings = parse_nutrition(parsed["nutrition_text"], context_text=nutrition_context["text"],
                                                   ocr_context=without_confidence(nutrition_context))
                except (ValueError, RuntimeError, OSError) as exc:
                    seconds = time.perf_counter() - ocr_started
                    error = f"{type(exc).__name__}: {exc}"
                row = {"profile": name, "image": image_path.name, "kind": kind, "repeat": repeat,
                       "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
                       "ocr_seconds": seconds, "full_seconds": time.perf_counter() - started,
                       "attempt_count": context.get("attempt_count", 1), "error": error,
                       "health_score": analysis.get("health_score"), "score_status": analysis.get("score_status"),
                       "text": context.get("text", ""), "nutrients": analysis.get("nutrients", []),
                       **measure_fields(truth, analysis, raw_readings)}
                if truth.get("reference_text"):
                    row.update(text_errors(truth["reference_text"], context.get("text", "")))
                if args.python_memory:
                    row["python_peak_bytes"] = tracemalloc.get_traced_memory()[1]
                    tracemalloc.stop()
                rows.append(row)
                print(name, image_path.name, f"{row['verified_correct']}/{row['nutrition_expected']}", f"{seconds:.2f}s", flush=True)
                result = {"method": f"Mode {args.mode}; OEM 1, English; repetitions {args.repeat}. Control uses original grayscale, PSM 6, no vocabulary for all models.",
                          "tesseract": str(ocr.pytesseract.get_tesseract_version()), "models": models, "source_hashes": source_hashes, "rows": rows}
    if args.numeric_probe:
        result["numeric_probe"] = [row for model in args.models for row in numeric_probe(model)]
    write_results(args.output.with_suffix(".json"), result)
    args.output.with_suffix(".md").write_text(report(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

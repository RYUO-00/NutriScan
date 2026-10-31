"""Evaluate the bundled synthetic label set with preprocessing off and on."""

import csv
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from matcher import decode_additives, match_allergens, match_ingredient_tokens, normalize_term
from nutrition import parse_nutrition
from ocr import recognize_text
from parser import parse_label_text
from preprocess import preprocess_image
from storage import load_knowledge


CSV_FIELDS = [
    "preprocessing", "image", "ingredient_expected", "ingredient_matched", "ingredient_recall",
    "additive_tp", "additive_fp", "additive_fn", "additive_precision", "additive_recall",
    "nutrition_expected", "nutrition_correct", "nutrition_accuracy",
    "allergen_tp", "allergen_fp", "allergen_fn", "allergen_precision", "allergen_recall",
    "processing_seconds", "error",
]


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _binary_counts(expected, actual):
    expected = set(expected)
    actual = set(actual)
    return {
        "tp": len(expected & actual),
        "fp": len(actual - expected),
        "fn": len(expected - actual),
    }


def _numeric_match(expected, actual):
    if actual.get("unit") != expected.get("unit") or actual.get("basis") != expected.get("basis"):
        return False
    expected_value = float(expected["value"])
    actual_value = float(actual["value"])
    tolerance = max(
        config.EVALUATION_NUTRIENT_ABS_TOLERANCE,
        abs(expected_value) * config.EVALUATION_NUTRIENT_REL_TOLERANCE,
    )
    return abs(actual_value - expected_value) <= tolerance


def _score_sample(image_path, truth, enabled, knowledge):
    started = time.perf_counter()
    error = ""
    ingredient_expected = {normalize_term(token) for token in truth["ingredient_tokens"]}
    ingredient_actual = set()
    additive_expected = set(truth["additive_codes"])
    additive_actual = set()
    allergen_expected = set(truth["allergen_groups"])
    allergen_actual = set()
    nutrition_expected = truth["nutrients"]
    nutrition_actual = []

    try:
        prepared = preprocess_image(image_path, enabled=enabled)
        ocr = recognize_text(prepared["processed"], prepared["original_gray"])
        parsed = parse_label_text(ocr["text"])
        ingredient_actual = {normalize_term(token) for token in parsed["ingredient_tokens"]}
        named_additives, _flags, _unknown_tokens = match_ingredient_tokens(
            parsed["ingredient_tokens"], knowledge["additives"], knowledge["ingredient_flags"]
        )
        coded_additives, _unknown_codes = decode_additives(parsed["raw_text"], knowledge["additives"])
        additive_actual = {
            str(item["ins_code"]) for item in [*named_additives, *coded_additives]
        }
        allergens = match_allergens(
            parsed["ingredient_text"], parsed["contains_text"], knowledge["allergens"]
        )
        allergen_actual = {item["allergen_group"] for item in allergens}
        nutrition_actual = parse_nutrition(parsed["nutrition_text"], knowledge["nutrition_limits"])
    except Exception as exc:  # Continue through the full set and report each failure.
        error = f"{type(exc).__name__}: {exc}"

    ingredient_hits = len(ingredient_expected & ingredient_actual)
    additive_counts = _binary_counts(additive_expected, additive_actual)
    allergen_counts = _binary_counts(allergen_expected, allergen_actual)
    nutrition_hits = 0
    for key, expected in nutrition_expected.items():
        if any(item.get("name") == key and _numeric_match(expected, item) for item in nutrition_actual):
            nutrition_hits += 1

    row = {
        "preprocessing": "on" if enabled else "off",
        "image": image_path.name,
        "ingredient_expected": len(ingredient_expected),
        "ingredient_matched": ingredient_hits,
        "ingredient_recall": _ratio(ingredient_hits, len(ingredient_expected)),
        "additive_tp": additive_counts["tp"],
        "additive_fp": additive_counts["fp"],
        "additive_fn": additive_counts["fn"],
        "additive_precision": _ratio(additive_counts["tp"], additive_counts["tp"] + additive_counts["fp"]),
        "additive_recall": _ratio(additive_counts["tp"], additive_counts["tp"] + additive_counts["fn"]),
        "nutrition_expected": len(nutrition_expected),
        "nutrition_correct": nutrition_hits,
        "nutrition_accuracy": _ratio(nutrition_hits, len(nutrition_expected)),
        "allergen_tp": allergen_counts["tp"],
        "allergen_fp": allergen_counts["fp"],
        "allergen_fn": allergen_counts["fn"],
        "allergen_precision": _ratio(allergen_counts["tp"], allergen_counts["tp"] + allergen_counts["fp"]),
        "allergen_recall": _ratio(allergen_counts["tp"], allergen_counts["tp"] + allergen_counts["fn"]),
        "processing_seconds": round(time.perf_counter() - started, 3),
        "error": error,
    }
    return row


def _aggregate(rows):
    ingredient_expected = sum(row["ingredient_expected"] for row in rows)
    ingredient_matched = sum(row["ingredient_matched"] for row in rows)
    additive_tp = sum(row["additive_tp"] for row in rows)
    additive_fp = sum(row["additive_fp"] for row in rows)
    additive_fn = sum(row["additive_fn"] for row in rows)
    nutrition_expected = sum(row["nutrition_expected"] for row in rows)
    nutrition_correct = sum(row["nutrition_correct"] for row in rows)
    allergen_tp = sum(row["allergen_tp"] for row in rows)
    allergen_fp = sum(row["allergen_fp"] for row in rows)
    allergen_fn = sum(row["allergen_fn"] for row in rows)
    durations = [row["processing_seconds"] for row in rows]
    return {
        "ingredient_recall": _ratio(ingredient_matched, ingredient_expected),
        "ingredient_counts": f"{ingredient_matched}/{ingredient_expected}",
        "additive_precision": _ratio(additive_tp, additive_tp + additive_fp),
        "additive_recall": _ratio(additive_tp, additive_tp + additive_fn),
        "additive_counts": f"TP {additive_tp}, FP {additive_fp}, FN {additive_fn}",
        "nutrition_accuracy": _ratio(nutrition_correct, nutrition_expected),
        "nutrition_counts": f"{nutrition_correct}/{nutrition_expected}",
        "allergen_precision": _ratio(allergen_tp, allergen_tp + allergen_fp),
        "allergen_recall": _ratio(allergen_tp, allergen_tp + allergen_fn),
        "allergen_counts": f"TP {allergen_tp}, FP {allergen_fp}, FN {allergen_fn}",
        "average_seconds": statistics.mean(durations) if durations else 0.0,
        "median_seconds": statistics.median(durations) if durations else 0.0,
        "failures": sum(bool(row["error"]) for row in rows),
    }


def _markdown_report(rows, sample_count):
    sections = [
        "# NutriScan synthetic-label evaluation",
        "",
        f"Generated from {sample_count} bundled synthetic label categories, each run with preprocessing off and on. These fixtures are not real retail packaging and do not establish real-world OCR or food-safety performance.",
        "",
        "The same five ground-truth files are used for both modes. Ingredient recall uses normalized ingredient-token equality. Additive precision/recall count normalized INS identities reported from an explicit code or a known additive name; allergen precision/recall count detected groups. Nutrition accuracy requires the expected nutrient, unit, basis, and a value within the absolute/relative tolerance configured in `config.py`. Processing time covers preprocessing, OCR, parsing, and lookups; startup and disk persistence are excluded.",
        "",
        "## Aggregate results",
        "",
        "| Preprocessing | Ingredient recall | Additive precision | Additive recall | Nutrition accuracy | Allergen precision | Allergen recall | Mean / median seconds | Failed scans |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in ("off", "on"):
        mode_rows = [row for row in rows if row["preprocessing"] == mode]
        metrics = _aggregate(mode_rows)
        sections.append(
            f"| {mode.title()} | {metrics['ingredient_recall']:.1%} ({metrics['ingredient_counts']}) | "
            f"{metrics['additive_precision']:.1%} | {metrics['additive_recall']:.1%} ({metrics['additive_counts']}) | "
            f"{metrics['nutrition_accuracy']:.1%} ({metrics['nutrition_counts']}) | "
            f"{metrics['allergen_precision']:.1%} | {metrics['allergen_recall']:.1%} ({metrics['allergen_counts']}) | "
            f"{metrics['average_seconds']:.3f} / {metrics['median_seconds']:.3f} | {metrics['failures']}/{len(mode_rows)} |"
        )
    sections.extend([
        "",
        "## Per-image detail",
        "",
        "| Mode | Image | Ingredient recall | Additive P / R | Nutrition accuracy | Allergen P / R | Seconds | Error |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in rows:
        error = row["error"].replace("|", "\\|").replace("\n", " ") or "—"
        sections.append(
            f"| {row['preprocessing'].title()} | {row['image']} | {row['ingredient_recall']:.1%} "
            f"({row['ingredient_matched']}/{row['ingredient_expected']}) | "
            f"{row['additive_precision']:.1%} / {row['additive_recall']:.1%} | "
            f"{row['nutrition_accuracy']:.1%} ({row['nutrition_correct']}/{row['nutrition_expected']}) | "
            f"{row['allergen_precision']:.1%} / {row['allergen_recall']:.1%} | "
            f"{row['processing_seconds']:.3f} | {error} |"
        )
    sections.extend([
        "",
        "## Interpretation limits",
        "",
        "- Synthetic text is cleanly typeset and does not model package curvature, camera variation, multilingual labels, regulatory edge cases, or the variety of commercial packaging.",
        "- The fixture set is intentionally small. Results are descriptive regression checks, not a statistically representative benchmark.",
        "- Failed OCR or preprocessing runs remain in the denominator as misses and are listed in the table; no threshold was adjusted to improve these results.",
        "- The score, risk categories, allergen keyword expansion, and nutrition screening values remain project assumptions documented in `DATA_REVIEW.md`.",
        "",
    ])
    return "\n".join(sections)


def run_evaluation():
    truth_paths = sorted(config.GROUND_TRUTH_DIR.glob("*.json"))
    if not truth_paths:
        raise FileNotFoundError("No ground-truth fixtures found. Run scripts/make_sample_labels.py first.")
    knowledge = load_knowledge()
    rows = []
    for enabled in (False, True):
        for truth_path in truth_paths:
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
            image_path = config.SAMPLE_LABEL_DIR / truth["image"]
            if not image_path.is_file():
                raise FileNotFoundError(f"Synthetic image is missing: {image_path}")
            rows.append(_score_sample(image_path, truth, enabled, knowledge))

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = config.RESULTS_DIR / "evaluation.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report_path = config.RESULTS_DIR / "evaluation.md"
    report_path.write_text(_markdown_report(rows, len(truth_paths)), encoding="utf-8")
    return rows, report_path, csv_path


def main():
    try:
        rows, report_path, csv_path = run_evaluation()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1
    failures = sum(bool(row["error"]) for row in rows)
    print(f"Evaluation complete: {len(rows)} runs, {failures} failed scans.")
    print(f"Markdown: {report_path}")
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

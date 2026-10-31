"""Validate the local NutriScan knowledge base and assumption review queue."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config


EXPECTED_COUNTS = {
    "additives.json": 180,
    "allergens.json": 45,
    "ingredient_flags.json": 65,
    "nutrition_limits.json": 10,
}
REQUIRED = {
    "additives.json": {"id", "ins_code", "name", "synonyms", "category", "category_source", "category_review_reason", "risk_level", "reason", "source"},
    "allergens.json": {"id", "allergen_group", "keyword", "source"},
    "ingredient_flags.json": {"id", "keyword", "flag_type", "reason", "source"},
    "nutrition_limits.json": {"nutrient", "unit", "per_basis", "config_key", "source"},
}
RISK_LEVELS = {"low", "moderate", "high"}
FLAG_TYPES = {"harmful", "caution", "beneficial"}
INS_CODE = re.compile(r"^\d{3,4}[a-z]{0,5}$")


class DataValidationError(ValueError):
    pass


def read_records(filename):
    path = config.KNOWLEDGE_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
    except FileNotFoundError as exc:
        raise DataValidationError(f"Knowledge file is missing: {path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DataValidationError(f"Knowledge file is malformed: {path}: {exc}") from exc
    if not isinstance(records, list):
        raise DataValidationError(f"{path} must contain a top-level JSON array.")
    return records


def validate_data():
    loaded = {}
    errors = []
    for filename, expected in EXPECTED_COUNTS.items():
        try:
            rows = read_records(filename)
        except DataValidationError as exc:
            errors.append(str(exc))
            continue
        loaded[filename] = rows
        if len(rows) != expected:
            errors.append(f"{filename}: expected {expected} records, found {len(rows)}.")
        seen_ids = set()
        seen_codes = set()
        seen_terms = set()
        for index, record in enumerate(rows, 1):
            label = f"{filename} record {index}"
            if not isinstance(record, dict):
                errors.append(f"{label} must be an object.")
                continue
            missing = REQUIRED[filename] - record.keys()
            if missing:
                errors.append(f"{label} missing required fields: {', '.join(sorted(missing))}.")
                continue
            optional_nullable = {"category_review_reason"} if filename == "additives.json" else set()
            for field in REQUIRED[filename] - {"id", "synonyms"} - optional_nullable:
                if not isinstance(record[field], str) or not record[field].strip():
                    errors.append(f"{label} field {field!r} must be a non-empty string.")
            if filename != "nutrition_limits.json":
                record_id = record["id"]
                if isinstance(record_id, bool) or not isinstance(record_id, int):
                    errors.append(f"{label} id must be an integer.")
                elif record_id in seen_ids:
                    errors.append(f"{filename} has duplicate id {record_id}.")
                seen_ids.add(record_id)
            if filename == "additives.json":
                code = record["ins_code"]
                if not isinstance(code, str) or not INS_CODE.fullmatch(code):
                    errors.append(f"{label} has invalid normalized INS code {code!r}.")
                elif code in seen_codes:
                    errors.append(f"additives.json has duplicate code {code}.")
                seen_codes.add(code)
                if not isinstance(record["risk_level"], str) or record["risk_level"] not in RISK_LEVELS:
                    errors.append(f"{label} has invalid risk_level {record['risk_level']!r}.")
                if not isinstance(record["category_source"], str) or not record["category_source"].strip():
                    errors.append(f"{label} must cite a functional-class source.")
                review_reason = record["category_review_reason"]
                if review_reason is not None and (not isinstance(review_reason, str) or not review_reason.strip()):
                    errors.append(f"{label} has an invalid category review reason.")
                if review_reason is not None and record["category"] != "Class under review":
                    errors.append(f"{label} assigns an unverified functional class.")
                if review_reason is None and " or " in record["category"].casefold():
                    errors.append(f"{label} uses a broad multi-class category.")
                if not isinstance(record["synonyms"], list) or not all(isinstance(x, str) for x in record["synonyms"]):
                    errors.append(f"{label} synonyms must be an array of strings.")
            elif filename == "ingredient_flags.json":
                if not isinstance(record["flag_type"], str) or record["flag_type"] not in FLAG_TYPES:
                    errors.append(f"{label} has invalid flag_type {record['flag_type']!r}.")
            elif filename == "allergens.json":
                if isinstance(record["keyword"], str):
                    term = record["keyword"].casefold()
                    if term in seen_terms:
                        errors.append(f"allergens.json has duplicate keyword {record['keyword']!r}.")
                    seen_terms.add(term)
            elif filename == "nutrition_limits.json":
                if any(k in record for k in ("medium_above", "high_above", "threshold", "cutoff")):
                    errors.append(f"{label} duplicates numeric thresholds; keep those values in config.py only.")
                if not isinstance(record["config_key"], str) or record["config_key"] not in config.NUTRITION_THRESHOLDS:
                    errors.append(f"{label} references unknown config key {record['config_key']!r}.")
                if record["nutrient"] != record["config_key"]:
                    errors.append(f"{label} nutrient and config_key must agree.")
    if set(loaded) == set(EXPECTED_COUNTS):
        review_text = (config.BASE_DIR / "DATA_REVIEW.md").read_text(encoding="utf-8") if (config.BASE_DIR / "DATA_REVIEW.md").exists() else ""
        for filename, rows in loaded.items():
            for record in rows:
                if filename == "additives.json" and record.get("category_review_reason"):
                    marker = f"INS {record['ins_code']} {record['name']}: {record['category_review_reason']}"
                    if marker not in review_text:
                        errors.append(f"DATA_REVIEW.md is missing functional-class review for INS {record['ins_code']}.")
                source = record.get("source", "")
                if not isinstance(source, str) or "project assumption" not in source.lower():
                    continue
                display = record.get("name") or record.get("keyword") or record.get("nutrient")
                key = record.get("ins_code") or record.get("id")
                marker = f"{filename}` record {key} ({display})"
                if marker not in review_text:
                    errors.append(f"DATA_REVIEW.md is missing assumption item {marker}.")
    if errors:
        raise DataValidationError("\n".join(errors))
    return {filename: len(rows) for filename, rows in loaded.items()}


def main():
    try:
        counts = validate_data()
    except DataValidationError as exc:
        print(f"DATA VALIDATION FAILED\n{exc}", file=sys.stderr)
        return 1
    total = sum(counts.values())
    print("DATA VALIDATION PASSED")
    for filename, count in counts.items():
        print(f"{filename}: {count}")
    print(f"Total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

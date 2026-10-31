"""Nutrition extraction with explicit units, serving basis, and comparability."""

import re

import config


NUMBER_UNIT_RE = re.compile(r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>kcal|kj|mg|g)\b", re.IGNORECASE)
UNIT_RE = re.compile(r"\b(kcal|kj|mg|g)\b", re.IGNORECASE)
BASIS_RE = re.compile(r"\bper\s*(?:(100)\s*(g|grams?|ml|millilit(?:er|re)s?)|(serv(?:e|ing)|portion)|([0-9]+(?:[.,][0-9]+)?)\s*(g|grams?|ml|millilit(?:er|re)s?))\b", re.IGNORECASE)
SERVING_SIZE_RE = re.compile(
    r"\b(?:serving|serve|portion)\s*(?:size)?\s*[:=]?\s*(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>g|grams?|ml|millilit(?:er|re)s?)\b",
    re.IGNORECASE,
)

LABELS = (
    ("energy", re.compile(r"(?<![a-z])(?:energy|calories|calorific\s*value)(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("added_sugar", re.compile(r"(?<![a-z])added\s*sugars?(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("saturated_fat", re.compile(r"(?<![a-z])(?:saturat(?:ed|e)\s*fat|sat\.?\s*fat)(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("trans_fat", re.compile(r"(?<![a-z])trans\s*fat(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("total_fat", re.compile(r"(?<![a-z])total\s*fat(?=\s|[:=0-9]|$)|(?<![a-z])fat(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("sodium", re.compile(r"(?<![a-z])sodium(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("salt", re.compile(r"(?<![a-z])salt(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("sugar", re.compile(r"(?<![a-z])(?:total\s*sugars?|sugars?)(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("protein", re.compile(r"(?<![a-z])protein(?=\s|[:=0-9]|$)", re.IGNORECASE)),
    ("fibre", re.compile(r"(?<![a-z])(?:dietary\s*)?(?:fibre|fiber)(?=\s|[:=0-9]|$)", re.IGNORECASE)),
)


def _number(value):
    value = value.strip()
    if "," in value and "." not in value:
        left, right = value.split(",", 1)
        value = left + ("." + right if len(right) <= 2 else right)
    else:
        value = value.replace(",", "")
    return float(value)


def _unit(value):
    normalized = value.casefold()
    return {"grams": "g", "gram": "g", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml", "millilitres": "ml"}.get(normalized, normalized)


def _basis_occurrences(text):
    found = []
    for match in BASIS_RE.finditer(text or ""):
        if match.group(1):
            amount, unit, basis = 100.0, _unit(match.group(2)), None
        elif match.group(3):
            amount, unit, basis = None, None, "per_serving"
        else:
            amount, unit, basis = _number(match.group(4)), _unit(match.group(5)), None
        if basis:
            found.append((match.start(), match.end(), basis))
        elif unit == "g" and amount == 100:
            found.append((match.start(), match.end(), "100g"))
        elif unit == "ml" and amount == 100:
            found.append((match.start(), match.end(), "100ml"))
        else:
            found.append((match.start(), match.end(), f"per_{amount:g}{unit}"))
    return found


def _serving_size(text):
    match = SERVING_SIZE_RE.search(text or "")
    if not match:
        return None
    return {"amount": _number(match.group("amount")), "unit": _unit(match.group("unit")), "source_span": match.group(0)}


def _basis_for_line(line, global_basis, global_conflict):
    local = _basis_occurrences(line)
    if local:
        return local[0][2], None
    if global_conflict:
        return "ambiguous", "The panel contains more than one serving basis and this row does not identify which column the value belongs to."
    return global_basis or "unknown", None


def _convert_unit(value, source_unit, target_unit):
    if source_unit == target_unit:
        return value
    if source_unit == "g" and target_unit == "mg":
        return value * 1000
    if source_unit == "mg" and target_unit == "g":
        return value / 1000
    if source_unit == "kj" and target_unit == "kcal":
        return value / 4.184
    return None


def _threshold_status(key, value, basis, unit, metadata):
    if key in config.INFORMATIONAL_NUTRIENTS:
        if key == "energy":
            return "Informational", "Shown for context only because no verified energy screening threshold is available.", None
        return "Informational", "Shown for context only; this nutrient does not reduce the screening score.", None
    threshold = config.NUTRITION_THRESHOLDS.get(key)
    if threshold is None:
        return "not comparable", "No screening value is available for this nutrient.", None
    if unit != threshold["unit"]:
        return "not comparable", f"This value uses {unit}; the screening value is shown in {threshold['unit']}.", threshold
    if basis != threshold["basis"]:
        return "not comparable", f"The extracted basis is {basis}; this screening threshold uses {threshold['basis']}.", threshold
    if value > threshold["high_above"]:
        status = "High"
    elif value > threshold["medium_above"]:
        status = "Medium"
    else:
        status = "Low"
    return status, f"Compared with the screening values for {threshold['basis']}.", threshold


def _label_matches(line):
    candidates = []
    for priority, (key, pattern) in enumerate(LABELS):
        for match in pattern.finditer(line):
            candidates.append((match.start(), match.end(), priority, key))
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[2]))
    selected = []
    for candidate in candidates:
        start, end, _priority, _key = candidate
        if any(start < old_end and old_start < end for old_start, old_end, *_ in selected):
            continue
        selected.append(candidate)
    return sorted(selected)


def _values_in_span(span):
    complete = [(match.group("number"), _unit(match.group("unit"))) for match in NUMBER_UNIT_RE.finditer(span)]
    if complete:
        return complete
    # Labels sometimes print the unit before the number, e.g. "Energy (kcal) 425".
    number = re.search(r"\d+(?:[.,]\d+)?", span)
    unit = UNIT_RE.search(span)
    if number and unit:
        return [(number.group(0), _unit(unit.group(1)))]
    return []


def parse_nutrition(nutrition_text, nutrition_limit_records=None):
    """Extract supported values; retain source spans and never guess a basis."""
    text = nutrition_text or ""
    limit_records = nutrition_limit_records or []
    metadata_by_key = {item.get("config_key", item.get("nutrient")): item for item in limit_records}
    all_bases = _basis_occurrences(text)
    distinct_bases = list(dict.fromkeys(item[2] for item in all_bases))
    global_conflict = len(distinct_bases) > 1
    global_basis = distinct_bases[0] if len(distinct_bases) == 1 else None
    serving_size = _serving_size(text)
    extracted = []

    for line in text.splitlines():
        if not line.strip():
            continue
        labels = _label_matches(line)
        for label_index, (label_start, label_end, _priority, selected_key) in enumerate(labels):
            next_start = labels[label_index + 1][0] if label_index + 1 < len(labels) else len(line)
            suffix = line[label_end:next_start]
            value_matches = _values_in_span(suffix)
            if not value_matches:
                continue
            if global_conflict and len(value_matches) > 1:
                # Two-column tables most commonly print per-100-g first and per-serving second.
                line_bases = distinct_bases[:len(value_matches)]
            else:
                line_bases = []
            for index, (raw_number, raw_unit) in enumerate(value_matches):
                original_value = _number(raw_number)
                value = original_value
                expected = config.NUTRITION_THRESHOLDS.get(selected_key, {}).get("unit", raw_unit)
                if selected_key == "energy":
                    expected = "kcal"
                converted = _convert_unit(value, raw_unit, expected)
                original_basis = "unknown"
                if converted is None:
                    status = "not comparable"
                    reason = f"The unit {raw_unit} cannot be converted safely to {expected}."
                    basis = "unknown"
                    threshold = None
                else:
                    value = converted
                    if line_bases:
                        basis, basis_error = line_bases[min(index, len(line_bases) - 1)], None
                    else:
                        basis, basis_error = _basis_for_line(line, global_basis, global_conflict)
                    original_basis = basis
                    converted_from = None
                    if basis.startswith("per_") and basis not in {"per_serving", "per_100g", "per_100ml"}:
                        match = re.fullmatch(r"per_([0-9.]+)(g|ml)", basis)
                        if match:
                            denominator, base_unit = float(match.group(1)), match.group(2)
                            basis = "100g" if base_unit == "g" else "100ml"
                            value = value * 100 / denominator
                            converted_from = original_basis
                    elif basis == "per_serving" and serving_size and serving_size["unit"] in {"g", "ml"}:
                        basis = "100g" if serving_size["unit"] == "g" else "100ml"
                        value = value * 100 / serving_size["amount"]
                        converted_from = "per_serving"
                    if basis_error:
                        status, reason, threshold = "not comparable", basis_error, None
                    else:
                        status, reason, threshold = _threshold_status(
                            selected_key, value, basis, expected, metadata_by_key.get(selected_key, {})
                        )
                        if status == "not comparable" and basis == "unknown":
                            reason = "The panel does not state whether this value is per 100 g, per 100 ml, or per serving."
                        elif converted_from and status != "not comparable":
                            reason += f" Converted from {converted_from} using the stated serving size."
                item = {
                    "name": selected_key,
                    "value": round(value, 3),
                    "unit": expected,
                    "basis": basis,
                    "original_value": original_value,
                    "original_unit": raw_unit,
                    "original_basis": original_basis,
                    "source_span": line.strip(),
                    "status": status,
                    "reason": reason,
                    "estimated": False,
                    "threshold_source": metadata_by_key.get(selected_key, {}).get("source"),
                }
                if threshold:
                    item["thresholds"] = {
                        "medium_above": threshold["medium_above"],
                        "high_above": threshold["high_above"],
                        "basis": threshold["basis"],
                        "unit": threshold["unit"],
                    }
                if value_matches and len(value_matches) > 1:
                    item["column_index"] = index
                extracted.append(item)

    present_keys = {item["name"] for item in extracted}
    salt = next((item for item in extracted if item["name"] == "salt"), None)
    if salt and "sodium" not in present_keys:
        estimated_value = salt["value"] * 0.4
        estimated_basis = salt["basis"]
        status, reason, threshold = _threshold_status(
            "sodium", estimated_value * 1000, estimated_basis, "mg", metadata_by_key.get("sodium", {})
        )
        reason = "Estimated sodium is about 40% of the declared salt amount; it is an estimate, not a measured sodium value. " + reason
        estimate = {
            "name": "sodium",
            "value": round(estimated_value * 1000, 3),
            "unit": "mg",
            "basis": estimated_basis,
            "original_value": salt["original_value"],
            "original_unit": salt["original_unit"],
            "original_basis": salt["original_basis"],
            "source_span": salt["source_span"],
            "status": status,
            "reason": reason,
            "estimated": True,
            "threshold_source": metadata_by_key.get("sodium", {}).get("source"),
        }
        if threshold:
            estimate["thresholds"] = {
                "medium_above": threshold["medium_above"],
                "high_above": threshold["high_above"],
                "basis": threshold["basis"],
                "unit": threshold["unit"],
            }
        extracted.append(estimate)
    return extracted

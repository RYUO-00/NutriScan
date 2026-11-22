"""Nutrition extraction with explicit units, serving basis, and comparability."""

import math
import re

import config
from parser import normalize_text


NUMBER_UNIT_RE = re.compile(r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>kcal|kj|mg|g)\b", re.IGNORECASE)
UNIT_RE = re.compile(r"\b(kcal|kj|mg|g)\b", re.IGNORECASE)
BASIS_RE = re.compile(r"\b(?:per\s*|amount\s*[/i]\s*)(?:(100)\s*(g|grams?|ml|millilit(?:er|re)s?)|(serv(?:e|ing)|portion)|([0-9]+(?:[.,][0-9]+)?)\s*(g|grams?|ml|millilit(?:er|re)s?))\b", re.IGNORECASE)
SERVING_SIZE_RE = re.compile(
    r"\b(?:serving\b|serve\b|serv[.,]|portion\b)[ \t]*(?:size)?[ \t]*[:=]?[^\n]*?(?P<amount>\d+(?:[.,]\d+)?)[ \t]*(?P<unit>g|grams?|ml|millilit(?:er|re)s?)\b",
    re.IGNORECASE,
)

LABELS = (
    ("energy", re.compile(r"(?<![a-z])(?:energy|calories|calorific\s*value)(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("added_sugar", re.compile(r"(?<![a-z])added\s*sugars?(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("saturated_fat", re.compile(r"(?<![a-z])(?:saturat(?:ed|e)\s*fat(?:ty\s*acids?)?s?|sat\.?\s*fat|^\s*[-~]?\s*saturated)(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("trans_fat", re.compile(r"(?<![a-z])trans\s*fat(?:ty\s*acids?)?(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("total_fat", re.compile(r"(?<![a-z])(?:total\s*fat|fat\s*,\s*total)(?=\s|[(/:=0-9]|$)|(?<![a-z])fat(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("sodium", re.compile(r"(?<![a-z])sodium(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("salt", re.compile(r"(?<![a-z])salt(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("sugar", re.compile(r"(?<![a-z])(?:total\s*sugars?|sugars?)(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("protein", re.compile(r"(?<![a-z])protein(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("potassium", re.compile(r"(?<![a-z])potassium(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
    ("fibre", re.compile(r"(?<![a-z])(?:dietary\s*)?(?:fibre|fiber)(?=\s|[(/:=0-9]|$)", re.IGNORECASE)),
)

# Unsupported fields still delimit a row. Their quantities must never be
# attached to the preceding supported nutrient (e.g. sodium ... potassium).
OTHER_LABEL_RE = re.compile(
    r"\b(?:cholesterol|carbohydrates?|vitamin\s+[a-z0-9]+|calcium|iron|"
    r"mono(?:un)?saturated\s*fat|poly(?:un)?saturated\s*fat|serving\s*size)\b",
    re.IGNORECASE,
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
    """Read a declared mass/volume beside an explicit serving heading.

    OCR can reverse a heading and its amount. Only inspect adjacent header
    lines, never borrow a nutrient quantity, and reject conflicting sizes.
    """
    lines = (text or "").splitlines()
    candidates = []

    def prefix_before_nutrient(value):
        ends = [start for start, *_ in _label_matches(value)]
        other = OTHER_LABEL_RE.search(value)
        if other:
            ends.append(other.start())
        return value[:min(ends)] if ends else value

    for index, line in enumerate(lines):
        marker = re.search(r"\b(?:serving\b|serve\b|serv[.,]|portion\b)[ \t]*(?:size)?", line, re.IGNORECASE)
        if not marker:
            continue
        if "size" not in marker.group(0).casefold() and (
                _label_matches(line) or re.search(r"\bper\s*$", line[:marker.start()], re.IGNORECASE)
                or re.match(r"\s*(?:per|and)\b", line[marker.end():], re.IGNORECASE)):
            continue  # A column heading or nutrient row is not a serving size.
        tail = prefix_before_nutrient(line[marker.end():])
        candidate = line[marker.start():marker.end()] + tail
        source = candidate
        if "size" in marker.group(0).casefold() and not SERVING_SIZE_RE.search(candidate):
            # Prefer the normal forward declaration. An amount before the
            # heading is admitted only when the next line is not its amount.
            for following_line in lines[index + 1:index + 3]:
                if not re.search(r"[a-z0-9]", following_line, re.IGNORECASE):
                    continue
                following = prefix_before_nutrient(following_line)
                if re.match(r"\s*[=(]*\s*\d", following) or re.search(r"\(\s*\d+(?:[.,]\d+)?\s*(?:g|ml)\s*\)", following, re.IGNORECASE):
                    candidate += " " + following
                    source += "\n" + following
                break
            if not SERVING_SIZE_RE.search(candidate):
                preceding = line[:marker.start()].strip()
                if not preceding and index:
                    preceding = lines[index - 1].strip()
                # Keep an actual portion declaration (e.g. 1 cup (227g)).
                # A nutrient or arbitrary product quantity is not a serving.
                if (not _label_matches(preceding) and not OTHER_LABEL_RE.search(preceding)
                        and re.match(r"^[=(]*\s*\d", preceding)):
                    candidate = marker.group(0) + " " + preceding
                    source = preceding + "\n" + marker.group(0)
        match = SERVING_SIZE_RE.search(candidate)
        if match:
            amount = _number(match.group("amount"))
            unit = _unit(match.group("unit"))
            if math.isfinite(amount) and amount > 0:
                candidates.append({"amount": amount, "unit": unit, "source_span": source})
    if len({(item["amount"], item["unit"]) for item in candidates}) != 1:
        return None
    return candidates[0]


def _has_prepared_columns(text):
    """Recognize an explicit preparation header, without inferring its values."""
    header = []
    for line in (text or "").splitlines():
        if _label_matches(line):
            break
        header.append(line)
    return bool(re.search(
        r"\bserv(?:ing|e)\s+with\b|\bwith\s+\d.*?\b(?:milk|water)\b|\bcereal\s+skim\s+milk\b",
        " ".join(header), re.IGNORECASE,
    ))


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


def screening_threshold(key, basis, serving_size=None):
    """Select a documented rule for the actual basis; never assume g == ml."""
    if key == "added_sugar":
        rule = dict(config.ADDED_SUGAR_THRESHOLD)
        if basis == "per_serving":
            return rule
        required_unit = {"100g": "g", "100ml": "ml"}.get(basis)
        if not serving_size or serving_size["unit"] != required_unit or serving_size["amount"] <= 0:
            return None
        factor = 100 / serving_size["amount"]
        rule.update(basis=basis, medium_above=rule["medium_above"] * factor, high_above=rule["high_above"] * factor)
        return rule
    if basis == "100ml":
        return config.LIQUID_NUTRITION_THRESHOLDS.get(key)
    return config.NUTRITION_THRESHOLDS.get(key)


def _threshold_status(key, value, basis, unit, metadata, serving_size=None):
    if key in config.INFORMATIONAL_NUTRIENTS:
        if key == "energy":
            return "Informational", "Shown for context only because no verified energy screening threshold is available.", None
        return "Informational", "Shown for context only; this nutrient does not reduce the screening score.", None
    threshold = screening_threshold(key, basis, serving_size)
    if threshold is None:
        return "not comparable", "No supported screening rule is available for this nutrient and basis; added sugar needs a stated serving size or serving basis.", None
    if unit != threshold["unit"]:
        return "not comparable", f"This value uses {unit}; the screening value is shown in {threshold['unit']}.", threshold
    if basis != threshold["basis"]:
        return "not comparable", f"The extracted basis is {basis}; this screening threshold uses {threshold['basis']}.", threshold
    if value > threshold["high_above"] or (threshold.get("high_inclusive") and value == threshold["high_above"]):
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
            if key == "total_fat" and match.group(0).casefold() == "fat" and re.search(r"[a-z]\s*$", line[:match.start()], re.IGNORECASE):
                continue  # An unknown qualifier (or damaged "trans") is not total fat.
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
    # A row's stated basis and RDA percentages are metadata, not values.
    span = BASIS_RE.sub("", span)
    complete = [(match.group("number"), _unit(match.group("unit"))) for match in NUMBER_UNIT_RE.finditer(span)]
    if complete:
        return complete
    # Labels sometimes print the unit before the number, e.g. "Energy (kcal) 425".
    before = re.match(r"\s*[:=(]*\s*(kcal|kj|mg|g)\s*[):=]*\s*(\d+(?:[.,]\d+)?)\b", span, re.IGNORECASE)
    if before:
        return [(before.group(2), _unit(before.group(1)))]
    return []


def _logical_lines(text):
    """Join only a label-only line and its immediately following quantity row."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if (re.fullmatch(r"\s*calories\s*", line, re.IGNORECASE)
                and index + 1 < len(lines)
                and re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", lines[index + 1])):
            line += "\n" + lines[index + 1]
            index += 1
        if (_label_matches(line) and not _values_in_span(line[_label_matches(line)[-1][1]:])
                and index + 1 < len(lines)
                and re.fullmatch(r"\s*(?:[<>~]?\s*\d+(?:[.,]\d+)?\s*(?:kcal|kj|mg|g)\s*(?:\d+(?:[.,]\d+)?\s*%)?\s*)+", lines[index + 1], re.IGNORECASE)):
            line += "\n" + lines[index + 1]
            index += 1
        yield line
        index += 1


def _ocr_uncertainty(span, ocr_context, number=None, minimum=None):
    if not ocr_context:
        return None
    confidences = []
    source = normalize_text(span)
    for line in ocr_context.get("lines", []):
        if normalize_text(line["text"]) in source or source in normalize_text(line["text"]):
            confidences.extend(
                word["confidence"] for word in line.get("words", [])
                if re.search(r"\d", word["text"]) and word.get("confidence") is not None
                and normalize_text(word["text"]).strip(" ,;:()").replace(" ", "") in source.replace(" ", "")
                and (number is None or ("%" not in word["text"] and any(_number(token) == _number(number)
                    for token in re.findall(r"\d+(?:[.,]\d+)?", word["text"]))))
            )
            if not confidences and line.get("confidence") is not None and (number is None or not line.get("words")):
                confidences.append(line["confidence"])
    if not confidences and ocr_context.get("mean_confidence") is not None:
        confidences.append(ocr_context["mean_confidence"])
    if confidences and min(confidences) < (config.OCR_MIN_NUMERIC_CONFIDENCE if minimum is None else minimum):
        return "OCR confidence is low for this reading; check the value and basis against the photo."
    return None


def _right_column_basis(line, value_match, ocr_context, header_bases):
    """Identify a lone value only when OCR coordinates put it in the 100-unit column."""
    if not ocr_context or len(header_bases) != 2 or header_bases[0] != "per_serving" or header_bases[1] not in {"100g", "100ml"}:
        return None
    rows = ocr_context.get("lines", [])
    columns = None
    for row in rows:
        words = row.get("words", [])
        right = next((word for word in words if re.fullmatch(r"100\s*(?:g|ml)", word.get("text", ""), re.IGNORECASE) and word.get("box")), None)
        left = next((word for word in words if re.fullmatch(r"serv(?:ing|e)", word.get("text", ""), re.IGNORECASE) and word.get("box")), None)
        if left and right:
            left_x = left["box"][0] + left["box"][2] / 2
            right_x = right["box"][0] + right["box"][2] / 2
            if right_x > left_x:
                columns = left_x, right_x
                break
    if not columns:
        return None
    raw_number, _unit_name = value_match
    matches = []
    for row in rows:
        row_text = normalize_text(row.get("text", ""))
        source = normalize_text(line)
        if not row_text or not (row_text in source or source in row_text):
            continue
        for word in row.get("words", []):
            box = word.get("box")
            match = NUMBER_UNIT_RE.fullmatch(word.get("text", "").strip(" ,;:()"))
            if box and match and match.group("number") == raw_number:
                matches.append(box[0] + box[2] / 2)
    if len(matches) != 1:
        return None
    left_x, right_x = columns
    return header_bases[1] if matches[0] >= left_x + 0.6 * (right_x - left_x) else None


def _coordinate_rows(ocr_context):
    """Recover a simple explicit nutrition table from TSV word geometry.

    No unit, decimal or serving column is guessed. Missing/overlapping columns,
    multiple products and rows containing multiple quantities stay unresolved.
    """
    if not ocr_context:
        return []
    words = [word for line in ocr_context.get("lines", []) for word in line.get("words", [])
             if word.get("box") and len(word["box"]) == 4 and min(word["box"][2:]) > 0]
    if not words:
        return []
    headings = [word for word in words if word["text"].casefold().strip(":") in {"nutrition", "nutritional"}]
    if len(headings) != 1:
        return []
    heading_y = headings[0]["box"][1]
    groups = []
    for word in sorted(words, key=lambda item: item["box"][1] + item["box"][3] / 2):
        x, y, width, height = word["box"]
        if y < heading_y:
            continue
        cy = y + height / 2
        group = next((row for row in reversed(groups[-3:]) if abs(row[0] - cy) <= min(row[1], height) * 0.45), None)
        if group is None:
            groups.append([cy, height, [word]])
        else:
            group[2].append(word)
    for group in groups:
        group[2].sort(key=lambda item: item["box"][0])
    columns, header_y, header_words = [], None, []
    for cy, height, row in groups:
        text = " ".join(word["text"] for word in row)
        if _label_matches(text) or "size" in text.casefold():
            continue
        for i, word in enumerate(row):
            token = word["text"].casefold().strip("()[]:.")
            direct = re.fullmatch(r"100\s*(g|ml)", token)
            if token == "100" and i + 1 < len(row) and row[i + 1]["text"].casefold().strip("()[]:.") in {"g", "ml"}:
                direct = re.fullmatch(r"100\s*(g|ml)", token + row[i + 1]["text"].casefold().strip("()[]:."))
            if direct:
                columns.append((word["box"][0] + word["box"][2] / 2, "100" + direct.group(1), word))
                header_y, header_words = cy, row
        if columns:
            # A serving header must be on this same header row; do not borrow
            # "serving size" from a separate declaration above the table.
            for word in row:
                if re.fullmatch(r"(?:per\s*)?serv(?:e|ing)|portion", word["text"].casefold().strip("()[]:.")):
                    columns.append((word["box"][0] + word["box"][2] / 2, "per_serving", word))
            break
    if not columns or len({basis for _, basis, _ in columns}) != len(columns):
        return []
    columns.sort(key=lambda column: column[0])
    output = []
    for cy, height, row in groups:
        if cy <= header_y:
            continue
        text = " ".join(word["text"] for word in row)
        labels = _label_matches(text)
        if len(labels) != 1:
            continue
        start, end, _, key = labels[0]
        # Unit in a row label, e.g. Sodium(mg), is explicit source evidence.
        explicit_unit = re.match(r"\s*\(\s*(kcal|kj|mg|g)\s*\)", text[end:], re.IGNORECASE)
        label_words = [word for word in row if word["box"][0] < columns[0][0] - height]
        if not label_words:
            continue
        label = text[start:end].strip()
        for index, (cx, basis, header_word) in enumerate(columns):
            radius = min(abs(cx - other[0]) for other in columns if other[0] != cx) * 0.45 if len(columns) > 1 else max(header_word["box"][2] * 1.5, height * 2)
            quantities = []
            for wi, word in enumerate(row):
                wx, wy, ww, wh = word["box"]
                if abs(wx + ww / 2 - cx) > radius or word in label_words:
                    continue
                raw = word["text"].strip("()[]:;,")
                match = re.fullmatch(r"([-<>≤≥~]?\d+(?:[.,]\d+)?)\s*(kcal|kj|mg|g)?", raw, re.IGNORECASE)
                if not match:
                    continue
                unit = match.group(2) or (explicit_unit.group(1) if explicit_unit else None)
                value_words = [word]
                if unit is None and wi + 1 < len(row):
                    neighbor = row[wi + 1]
                    if UNIT_RE.fullmatch(neighbor["text"]) and neighbor["box"][0] - (wx + ww) <= height:
                        unit = neighbor["text"]
                        value_words.append(neighbor)
                if unit:
                    number = match.group(1)
                    if (wi > 0 and row[wi - 1]["text"] in {"<", ">", "≤", "≥", "~", "-"}
                            and wx - (row[wi - 1]["box"][0] + row[wi - 1]["box"][2]) <= height):
                        number = row[wi - 1]["text"] + number
                        value_words.insert(0, row[wi - 1])
                    quantities.append((number, unit, value_words))
            if len(quantities) != 1:
                continue
            number, unit, quantity_words = quantities[0]
            basis_text = "per serving" if basis == "per_serving" else "per 100 " + basis[3:]
            assembled = f"{label} {basis_text} {number} {unit}"
            output.append({"text": assembled, "words": [*label_words, header_word, *quantity_words],
                           "source_span": text, "source_boxes": [word["box"] for word in [*label_words, *quantity_words]], "key": key})
    return output



def comparable_nutrients(nutrients):
    """Validate at the scoring boundary; a status string alone is not evidence."""
    grouped = {}
    for nutrient in nutrients or []:
        key = nutrient.get("name")
        threshold = screening_threshold(key, nutrient.get("basis"), nutrient.get("serving_size"))
        value = nutrient.get("value")
        if (key in config.INFORMATIONAL_NUTRIENTS or not threshold
                or isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0
                or nutrient.get("verified") is False or nutrient.get("estimated")
                or nutrient.get("status", "").casefold() in {"not comparable", "unverified"}
                or nutrient.get("unit") != threshold["unit"]
                or nutrient.get("basis") != threshold["basis"]):
            continue
        mass = value / 1000 if threshold["unit"] == "mg" else value
        if threshold["basis"] == "100g" and mass > 100:
            continue
        grouped.setdefault(key, []).append(nutrient)
    return {
        key: items[0] for key, items in grouped.items()
        if len({round(item["value"], 3) for item in items}) == 1
    }


def parse_nutrition(nutrition_text, nutrition_limit_records=None, *, ocr_context=None, context_text=None, _use_geometry=True):
    """Extract supported values; retain source spans and never guess a basis."""
    text = nutrition_text or ""
    limit_records = nutrition_limit_records or []
    metadata_by_key = {item.get("config_key", item.get("nutrient")): item for item in limit_records}
    all_bases = _basis_occurrences(text)
    distinct_bases = list(dict.fromkeys(item[2] for item in all_bases))
    global_conflict = len(distinct_bases) > 1
    global_basis = distinct_bases[0] if len(distinct_bases) == 1 else None
    serving_size = _serving_size(context_text or text)
    serving_warning = _ocr_uncertainty(
        serving_size["source_span"], ocr_context, number=f"{serving_size['amount']:g}"
    ) if serving_size else None
    if (serving_warning and serving_size and ocr_context
            and not _ocr_uncertainty(serving_size["source_span"], ocr_context,
                                     number=f"{serving_size['amount']:g}", minimum=config.OCR_MIN_CONFIDENCE)
            and [serving_size["amount"], serving_size["unit"]] in ocr_context.get("corroborated_serving_sizes", [])):
        serving_warning = None
    # Explicit serving-size declarations identify the nutrition basis only when
    # no other basis is printed. Do not infer the size from nutrient quantities.
    if global_basis is None and not global_conflict and serving_size:
        global_basis = "per_serving"
    extracted = []

    # Column order is trusted only when explicitly present in a header.
    header_bases = []
    for header in text.splitlines():
        if not _label_matches(header):
            header_bases.extend(item[2] for item in _basis_occurrences(header))
    header_bases = list(dict.fromkeys(header_bases))
    # OCR often splits the two header lines: "per ... per" / "serving ... 100g".
    # Recognize only the explicit ordered serving/100-unit header, not a bare
    # 100g appearing elsewhere in the product text.
    header_lines = []
    for line in text.splitlines():
        if _label_matches(line):
            break
        header_lines.append(line)
    header_text = " ".join(header_lines)
    if (len(header_bases) < 2 and re.search(r"\bper\b", header_text, re.IGNORECASE)
            and re.search(r"\bserv(?:ing|e)\b.*?\b100\s*(?:g|ml)\b", header_text, re.IGNORECASE)):
        unit = re.search(r"\bserv(?:ing|e)\b.*?\b100\s*(g|ml)\b", header_text, re.IGNORECASE).group(1).lower()
        header_bases = ["per_serving", "100" + unit]
    # A prepared-food column (for example cereal with milk) is a different
    # composition, not another unit basis for the same product. Counting values
    # cannot establish their column when OCR drops quantities or header spacing.
    prepared_columns = _has_prepared_columns(text) or bool((ocr_context or {}).get("prepared_columns"))
    basis_warning = next((
        warning for line in text.splitlines() if _basis_occurrences(line)
        for warning in [_ocr_uncertainty(line, ocr_context)] if warning
    ), None)

    for line in _logical_lines(text):
        if not line.strip():
            continue
        labels = _label_matches(line)
        for label_index, (label_start, label_end, _priority, selected_key) in enumerate(labels):
            next_start = labels[label_index + 1][0] if label_index + 1 < len(labels) else len(line)
            other = OTHER_LABEL_RE.search(line, label_end, next_start)
            if other:
                next_start = other.start()
            suffix = line[label_end:next_start]
            value_matches = _values_in_span(suffix)
            confidence_start = label_start
            if not value_matches and selected_key == "energy" and re.fullmatch(r"calories", line[label_start:label_end], re.IGNORECASE):
                calorie_suffix = re.sub(r"^\s*/[^0-9\n]+", " ", suffix)
                calories = re.match(r"\s*[:=]?\s*(\d+(?:[.,]\d+)?)(?![\d.])(?:\s|$)", calorie_suffix)
                if calories:
                    value_matches = [(calories.group(1), "kcal")]
            if not value_matches and selected_key == "added_sugar":
                includes = re.search(r"\bincludes?\s*(\d+(?:[.,]\d+)?)\s*(g|mg)\s*$", line[:label_start], re.IGNORECASE)
                if includes:
                    value_matches = [(includes.group(1), _unit(includes.group(2)))]
                    confidence_start = includes.start()
            if not value_matches:
                extracted.append({
                    "name": selected_key, "value": None, "unit": None, "basis": global_basis or "unknown",
                    "original_value": None, "original_unit": None, "original_basis": global_basis or "unknown",
                    "source_span": line.strip(), "status": "not comparable", "verified": False,
                    "reason": "The nutrient name was read, but its value or unit could not be verified.",
                    "estimated": False, "threshold_source": metadata_by_key.get(selected_key, {}).get("source"),
                })
                continue
            local_bases = [item[2] for item in _basis_occurrences(line)]
            column_bases = local_bases if local_bases else header_bases
            line_bases = column_bases if len(column_bases) > 1 and len(column_bases) == len(value_matches) else []
            if not line_bases and not local_bases and len(value_matches) == 1:
                right_basis = _right_column_basis(line, value_matches[0], ocr_context, header_bases)
                if right_basis:
                    line_bases = [right_basis]
            uncertain = None
            if not _basis_occurrences(line) and basis_warning:
                uncertain = "The OCR reading of the comparison basis is uncertain; check the panel heading."
            if re.search(r"(?:[<>≤≥~]|(?<!\w)-)\s*\d|\b(?:about|approx(?:imately)?)\b", suffix, re.IGNORECASE):
                uncertain = "This reading is a bound, approximation, or negative value; an exact nutrient value could not be verified."
            if len(value_matches) > 1 and not line_bases:
                uncertain = "Multiple quantities were read without an explicit matching column header; the value association is uncertain."
            elif len(value_matches) == 1 and len(header_bases) > 1 and not local_bases and not line_bases:
                uncertain = "The panel has multiple columns and the OCR did not identify which column this value belongs to."
            if prepared_columns and not local_bases:
                uncertain = ("The panel includes a prepared-food column; the OCR could not verify "
                             "which values describe this product alone. Crop to the product-only column.")
            for index, (raw_number, raw_unit) in enumerate(value_matches):
                value_uncertainty = _ocr_uncertainty(line[confidence_start:next_start].strip(), ocr_context, number=raw_number)
                row_uncertainty = uncertain or value_uncertainty
                original_value = _number(raw_number)
                value = original_value
                expected = config.NUTRITION_THRESHOLDS.get(selected_key, {}).get("unit", raw_unit)
                if selected_key in {"energy", "potassium"}:
                    expected = "kcal" if selected_key == "energy" else "mg"
                converted = _convert_unit(value, raw_unit, expected)
                original_basis = "unknown"
                if converted is None:
                    status = "not comparable"
                    reason = f"The unit {raw_unit} cannot be converted safely to {expected}."
                    basis, _basis_error = _basis_for_line(line, global_basis, global_conflict)
                    original_basis = basis
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
                            if denominator > 0:
                                basis = "100g" if base_unit == "g" else "100ml"
                                value = value * 100 / denominator
                                converted_from = original_basis
                            else:
                                basis_error = "The stated portion size is zero, so this value cannot be converted."
                    elif basis == "per_serving" and serving_size and serving_size["unit"] in {"g", "ml"}:
                        basis = "100g" if serving_size["unit"] == "g" else "100ml"
                        value = value * 100 / serving_size["amount"]
                        converted_from = "per_serving"
                        if serving_warning:
                            row_uncertainty = "The serving size could not be verified by OCR; check the panel before comparing this value."
                    if basis_error:
                        status, reason, threshold = "not comparable", basis_error, None
                    else:
                        status, reason, threshold = _threshold_status(
                            selected_key, value, basis, expected, metadata_by_key.get(selected_key, {}), serving_size
                        )
                        if status == "not comparable" and basis == "unknown":
                            reason = "The panel does not state whether this value is per 100 g, per 100 ml, or per serving."
                        elif converted_from and status != "not comparable":
                            reason += f" Converted from {converted_from} using the stated serving size."
                mass = value / 1000 if expected == "mg" else value
                if not math.isfinite(value):
                    row_uncertainty = "The extracted number is not a finite quantity; check the photo."
                if basis == "100g" and expected in {"g", "mg"} and mass > 100:
                    row_uncertainty = "This reading exceeds the total mass per 100 g; check the OCR value and decimal point."
                # A borderline numeric token may be supported by independent
                # OCR attempts which agree on the exact number, unit and basis.
                # This is not used to override a basis/serving/column warning.
                if (value_uncertainty and row_uncertainty == value_uncertainty and ocr_context
                        and not _ocr_uncertainty(line[confidence_start:next_start].strip(), ocr_context,
                                                 number=raw_number, minimum=config.OCR_MIN_CONFIDENCE)):
                    signature = [selected_key, original_value, raw_unit, original_basis,
                                 serving_size["amount"] if serving_size else None,
                                 serving_size["unit"] if serving_size else None]
                    if signature in ocr_context.get("corroborated_readings", []):
                        row_uncertainty = None
                if row_uncertainty:
                    status, reason, threshold = "not comparable", row_uncertainty, None
                item = {
                    "name": selected_key,
                    "value": value if math.isfinite(value) else None,
                    "unit": expected if converted is not None else raw_unit,
                    "basis": basis,
                    "original_value": original_value if math.isfinite(original_value) else None,
                    "original_unit": raw_unit,
                    "original_basis": original_basis,
                    "source_span": line.strip(),
                    "status": status,
                    "reason": reason,
                    "estimated": False,
                    "verified": status != "not comparable",
                    "serving_size": serving_size,
                    "threshold_source": threshold.get("source") if threshold and threshold.get("source") else metadata_by_key.get(selected_key, {}).get("source"),
                }
                # Retain the last printed digit's half-step so per-serving and
                # per-100 declarations can be checked without penalizing normal
                # rounding. Never use this to repair a missing OCR digit.
                decimals = len(raw_number.replace(",", ".").partition(".")[2])
                half_step = 0.5 * 10 ** (-decimals)
                unit_step = _convert_unit(half_step, raw_unit, expected)
                if unit_step is not None:
                    if original_basis == "per_serving" and serving_size and basis in {"100g", "100ml"}:
                        unit_step *= 100 / serving_size["amount"]
                    item["rounding_tolerance"] = unit_step
                if threshold:
                    item["thresholds"] = {
                        "medium_above": threshold["medium_above"],
                        "high_above": threshold["high_above"],
                        "basis": threshold["basis"],
                        "unit": threshold["unit"],
                        "high_inclusive": threshold.get("high_inclusive", False),
                    }
                if value_matches and len(value_matches) > 1:
                    item["column_index"] = index
                extracted.append(item)

    if _use_geometry and not prepared_columns:
        for row in _coordinate_rows(ocr_context):
            row_context = {**ocr_context, "lines": [*ocr_context.get("lines", []), row]}
            recovered = parse_nutrition(row["text"], limit_records, ocr_context=row_context,
                                        context_text=context_text or text, _use_geometry=False)
            if any(item.get("verified") for item in recovered):
                extracted = [item for item in extracted if item["name"] != row["key"] or item.get("verified")]
                for item in recovered:
                    item.update(source_span=row["source_span"], source_boxes=row["source_boxes"], coordinate_association=True)
                extracted.extend(recovered)

    present_keys = {item["name"] for item in extracted}
    salt = next((item for item in extracted if item["name"] == "salt" and item.get("value") is not None), None)
    if salt and "sodium" not in present_keys:
        estimated_value = salt["value"] * 0.4
        estimated_basis = salt["basis"]
        status, reason, threshold = _threshold_status(
            "sodium", estimated_value * 1000, estimated_basis, "mg", metadata_by_key.get("sodium", {})
        )
        reason = "Estimated sodium is about 40% of the declared salt amount; it is an estimate, not a measured sodium value. " + reason
        if not salt.get("verified"):
            status, reason, threshold = "not comparable", "The salt reading could not be verified, so its sodium estimate is also unverified.", None
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
            "verified": False,
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
    # Prefer an explicitly declared per-100 value when the per-serving value
    # agrees within their printed rounding intervals. Disagreement remains
    # unverified; it is never resolved by guessing which OCR number is right.
    for key in {item["name"] for item in extracted}:
        items = [item for item in extracted if item["name"] == key and not item["estimated"] and item.get("verified")]
        direct = next((item for item in items if item["original_basis"] in {"100g", "100ml"}), None)
        if not direct:
            continue
        for item in items:
            if item is direct or item["original_basis"] != "per_serving" or item["basis"] != direct["basis"] or item["unit"] != direct["unit"]:
                continue
            tolerance = item.get("rounding_tolerance", 0) + direct.get("rounding_tolerance", 0)
            if item["value"] != direct["value"] and abs(item["value"] - direct["value"]) <= tolerance + 1e-9:
                extracted.remove(item)

    # Conflicting duplicate readings are not silently reduced to the first row.
    for key in {item["name"] for item in extracted}:
        items = [item for item in extracted if item["name"] == key and not item["estimated"] and item.get("verified")]
        values = {(item["basis"], item["unit"], round(item["value"], 9)) for item in items}
        if len(values) > 1:
            for item in items:
                item.update(status="not comparable", verified=False, reason="Conflicting readings were extracted for this nutrient; check the photo.")
                item.pop("thresholds", None)
    return extracted

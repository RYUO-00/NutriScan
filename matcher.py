"""Deterministic additive, ingredient-flag, and allergen matching."""

import difflib
import re

import config


CODE_WITH_PREFIX = re.compile(
    r"(?<![A-Z0-9])(?:E|INS)\s*[-\u2010-\u2015]?\s*"
    r"(?P<code>\d{3,4}[A-Z]{0,4}(?:\s*\(\s*[IVX]+\s*\))?)(?![A-Z0-9])",
    re.IGNORECASE,
)
CODE_WITH_SUFFIX = re.compile(
    r"(?<![A-Z0-9])(?P<code>\d{3,4}[A-Z]{1,4}(?:\s*\(\s*[IVX]+\s*\))?)(?![A-Z0-9])",
    re.IGNORECASE,
)
BARE_CODE_CONTEXT = re.compile(
    r"\b(?:preservative|colour|color|antioxidant|emulsifier|thickener|stabilizer|stabiliser|flavour\s+enhancer|acidity\s+regulator)"
    r"\s*\([^)]*?(?P<code>\d{3,4})[^)]*\)",
    re.IGNORECASE,
)
ANNOTATED_CODE_SUFFIX = re.compile(
    r"\s*\((?P<code>(?:(?:E|INS)\s*[-\u2010-\u2015]?\s*)?"
    r"\d{3,4}[A-Z]{0,4}(?:\s*\(\s*[IVX]+\s*\))?)\)\s*$",
    re.IGNORECASE,
)


def normalize_term(value):
    value = str(value or "").casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_additive_code(value):
    """Normalize E/INS code syntax to digits and optional letters."""
    raw = str(value or "").strip().casefold()
    raw = re.sub(r"^(?:e|ins)\s*[- ]*", "", raw)
    raw = re.sub(r"\s+", "", raw)
    return re.sub(r"[()]", "", raw)


def _code_occurrences(text):
    candidates = []
    for pattern, priority in ((CODE_WITH_PREFIX, 0), (CODE_WITH_SUFFIX, 1), (BARE_CODE_CONTEXT, 2)):
        for match in pattern.finditer(text or ""):
            raw_code = match.group("code")
            code = normalize_additive_code(raw_code)
            if not code:
                continue
            candidates.append((match.start("code"), match.end("code"), priority, code, match.group(0)))
    # Prefer prefixed/more-specific captures when patterns overlap; keep each span once.
    candidates.sort(key=lambda item: (item[0], item[1] - item[0], item[2]))
    selected = []
    seen = set()
    for start, end, priority, code, matched_text in candidates:
        key = (start, end, code)
        if key in seen:
            continue
        if any(start < old_end and old_start < end and old_priority < priority for old_start, old_end, old_priority, *_ in selected):
            continue
        seen.add(key)
        selected.append((start, end, priority, code, matched_text))
    return selected


def decode_additives(text, additive_records):
    by_code = {record["ins_code"].casefold(): record for record in additive_records}
    decoded_by_code = {}
    unknown = []
    for start, end, _priority, code, matched_text in _code_occurrences(text):
        record = by_code.get(code)
        span = {"start": start, "end": end, "text": matched_text}
        if record:
            item = decoded_by_code.setdefault(code, {**record, "matched_code": code, "source_spans": []})
            item["source_spans"].append(span)
        else:
            unknown.append({
                "code": code,
                "label": "Unrecognised additive code",
                "source_span": span,
            })
    return list(decoded_by_code.values()), unknown


def _aliases(record, is_additive):
    primary = [record.get("name", "")] if is_additive else [record.get("keyword", "")]
    synonyms = record.get("synonyms", []) if is_additive else []
    return [normalize_term(value) for value in primary if value], [normalize_term(value) for value in synonyms if value]


def match_ingredient_tokens(tokens, additive_records, flag_records, fuzzy_threshold=None):
    """Match each token at most once: primary name, synonym, then fuzzy."""
    threshold = config.FUZZY_THRESHOLD if fuzzy_threshold is None else fuzzy_threshold
    candidates = []
    for is_additive, records in ((True, additive_records), (False, flag_records)):
        for record in records:
            primary, synonyms = _aliases(record, is_additive)
            candidates.append((is_additive, record, primary, synonyms))
    code_lookup = {record["ins_code"].casefold(): record for record in additive_records}
    additive_matches, flag_matches, unrecognized = [], [], []

    for token in tokens:
        key = normalize_term(token)
        if not key:
            continue
        token_code = normalize_additive_code(token)
        if token_code in code_lookup:
            continue  # The code decoder already reports this finding.
        annotation = ANNOTATED_CODE_SUFFIX.search(token)
        if annotation and normalize_additive_code(annotation.group("code")) in code_lookup:
            # Match the ingredient's name while leaving its code to the decoder.
            key = normalize_term(token[:annotation.start()].strip(" :-"))
            if not key:
                continue

        match = None
        tier = None
        # Stage 1: exact primary keyword/name.
        for candidate in candidates:
            if key in candidate[2]:
                match, tier = candidate, "exact"
                break
        # Stage 2: exact synonym.
        if match is None:
            for candidate in candidates:
                if key in candidate[3]:
                    match, tier = candidate, "synonym"
                    break
        # Stage 3: highest fuzzy score; list order breaks ties deterministically.
        if match is None:
            best_score = 0.0
            for candidate in candidates:
                for alias in candidate[2] + candidate[3]:
                    score = 100 * difflib.SequenceMatcher(None, key, alias).ratio()
                    if score > best_score:
                        best_score, match = score, candidate
            if match is not None and best_score >= threshold:
                tier = "fuzzy"
            else:
                match = None
        if match is None:
            unrecognized.append(token)
            continue
        is_additive, record, _primary, _synonyms = match
        finding = {**record, "matched_token": token, "match_type": tier}
        (additive_matches if is_additive else flag_matches).append(finding)
    return additive_matches, flag_matches, unrecognized


def _keyword_pattern(keyword):
    pieces = [re.escape(piece) for piece in keyword.split()]
    return re.compile(r"(?<![a-z0-9])" + r"\s+".join(pieces) + r"(?![a-z0-9])", re.IGNORECASE)


def _find_keyword(text, record):
    keyword = record["keyword"]
    if keyword.casefold() == "soy lecithin":
        # Lecithin alone is context-dependent; only explicit soy phrasing alerts Soy.
        pattern = re.compile(r"(?<![a-z0-9])(?:soy|soya|soybean)\s+lecithin(?![a-z0-9])|(?<![a-z0-9])lecithin\s*\(\s*(?:soy|soya|soybean)\s*\)", re.IGNORECASE)
    else:
        pattern = _keyword_pattern(keyword)
    return pattern.search(text or "")


def match_allergens(ingredient_text, contains_text, allergen_records, selected_allergens=None):
    """Return one alert per group with matched keyword, section, and preference state."""
    selected = {normalize_term(group) for group in (selected_allergens or [])}
    grouped = {}
    for section_name, text in (("ingredients", ingredient_text), ("contains", contains_text)):
        for record in allergen_records:
            found = _find_keyword(text or "", record)
            if not found:
                continue
            group = record["allergen_group"]
            group_key = group.casefold()
            item = grouped.setdefault(group_key, {
                "allergen_group": group,
                "matched_keywords": [],
                "source_sections": [],
                "sources": [],
                "selected": normalize_term(group) in selected,
            })
            if record["keyword"] not in item["matched_keywords"]:
                item["matched_keywords"].append(record["keyword"])
            if section_name not in item["source_sections"]:
                item["source_sections"].append(section_name)
            if record.get("source") and record["source"] not in item["sources"]:
                item["sources"].append(record["source"])
    alerts = list(grouped.values())
    for alert in alerts:
        alert["severity"] = "critical" if alert["selected"] else "warning"
    return sorted(alerts, key=lambda item: (not item["selected"], item["allergen_group"].casefold()))

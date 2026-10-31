"""OCR text normalization and label-section extraction."""

import re


HEADING_RE = re.compile(
    r"(?P<heading>ingredients?|nutrition(?:al)?(?:\s+(?:facts|information))?|"
    r"may\s+contain|contains?|allergens?|allergen\s+information|"
    r"best\s+before|manufactured(?:\s+by)?)\s*[:\-]?",
    re.IGNORECASE,
)
STOP_HEADINGS = {"best before", "manufactured", "manufactured by"}
NUTRITION_VALUE_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:kcal|kj|mg|g)\b", re.IGNORECASE)


def correct_ocr_confusions(text):
    """Correct common letter/number confusions only inside alphabetic words."""
    def correct_words(segment):
        segment = re.sub(r"(?<![A-Za-z0-9])0(?=[A-Za-z]{2,}(?![A-Za-z0-9]))", "o", segment)
        for pattern, replacement in (
            (r"(?<=[A-Za-z])0(?=[A-Za-z])", "o"),
            (r"(?<=[A-Za-z])[1|](?=[A-Za-z])", "l"),
            (r"(?<=[A-Za-z])5(?=[A-Za-z])", "s"),
        ):
            segment = re.sub(pattern, replacement, segment)
        return segment

    pieces = []
    cursor = 0
    for match in NUTRITION_VALUE_RE.finditer(text or ""):
        pieces.append(correct_words(text[cursor:match.start()]))
        pieces.append(match.group(0))
        cursor = match.end()
    pieces.append(correct_words((text or "")[cursor:]))
    return "".join(pieces)


def normalize_text(text):
    corrected = correct_ocr_confusions(text or "")
    lines = [re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in corrected.splitlines()]
    return "\n".join(line for line in lines if line).casefold()


def _section_key(heading):
    normalized = re.sub(r"\s+", " ", heading.casefold()).strip()
    if normalized.startswith("ingredient"):
        return "ingredients"
    if normalized.startswith("nutrition"):
        return "nutrition"
    if normalized.startswith("may contain") or normalized.startswith("contain") or normalized.startswith("allergen"):
        return "contains"
    if normalized in STOP_HEADINGS:
        return "stop"
    return None


def _append_section(sections, current, text):
    value = text.strip(" \t:;-\r\n")
    if current and value:
        sections[current].append(value)


def _extract_sections(text):
    sections = {"ingredients": [], "contains": [], "nutrition": []}
    preamble = []
    current = None
    for line in (text or "").splitlines():
        matches = list(HEADING_RE.finditer(line))
        if not matches:
            _append_section(sections, current, line)
            if current is None and line.strip():
                preamble.append(line.strip())
            continue
        cursor = 0
        for match in matches:
            before = line[cursor:match.start()]
            _append_section(sections, current, before)
            if current is None and before.strip():
                preamble.append(before.strip())
            current = _section_key(match.group("heading"))
            cursor = match.end()
            # A stop heading disables collection until another recognized section.
            if current == "stop":
                current = None
        tail = line[cursor:]
        _append_section(sections, current, tail)
    return {key: "\n".join(values).strip() for key, values in sections.items()}, "\n".join(preamble)


def split_ingredient_tokens(ingredient_text):
    """Split at commas, semicolons, and line breaks outside bracket groups."""
    tokens = []
    buffer = []
    depth = 0
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = set(pairs.values())
    for char in ingredient_text or "":
        if char in pairs:
            depth += 1
        elif char in closers and depth:
            depth -= 1
        if char in ",;\n\r" and depth == 0:
            token = "".join(buffer).strip(" \t:;,.\r\n")
            if token:
                tokens.append(token)
            buffer = []
        else:
            buffer.append(char)
    token = "".join(buffer).strip(" \t:;,.\r\n")
    if token:
        tokens.append(token)
    return tokens


def parse_label_text(raw_text):
    """Preserve source OCR and return normalized text plus independent sections."""
    raw_text = raw_text or ""
    corrected_for_sections = correct_ocr_confusions(raw_text)
    sections, preamble = _extract_sections(corrected_for_sections)
    ingredient_text = sections["ingredients"]
    nutrition_text = sections["nutrition"]
    contains_text = sections["contains"]

    # If OCR misses the Nutrition heading, retain the full text for numeric parsing;
    # the nutrient parser still requires a numeric value and matching basis.
    if not nutrition_text and re.search(r"\b(?:energy|calories|total\s+fat|sodium|protein|fibre|fiber)\b", raw_text, re.IGNORECASE):
        nutrition_text = raw_text

    return {
        "raw_text": raw_text,
        "normalized_text": normalize_text(raw_text),
        "preamble": preamble,
        "ingredient_text": ingredient_text,
        "ingredient_tokens": split_ingredient_tokens(ingredient_text),
        "contains_text": contains_text,
        "nutrition_text": nutrition_text,
        "sections": sections,
    }

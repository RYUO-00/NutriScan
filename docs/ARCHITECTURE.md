# NutriScan Architecture

## Three layers

1. **Browser frontend:** offline HTML, CSS, and JavaScript for upload/camera input, allergen preferences, scan progress, result views, comparison, and history.
2. **Flask backend:** thin routes validate requests and orchestrate the nine processing stages through focused modules.
3. **Local data and files:** four UTF-8 JSON knowledge arrays, JSON scan history, and controlled local uploads. The first release is single-process and single-user.

## Nine-stage pipeline and module contracts

| Stage / module | Input → output | Failure behaviour |
|---|---|---|
| 1. Upload (`app.py`, `config.py`) | Multipart image + selected allergen groups → validated upload path and safe ID | Friendly 400 for missing/empty, unsupported, oversized, or undecodable images; never use raw filename as a path |
| 2. Preprocess (`preprocess.py`) | Image path/array → original and processed image paths/arrays plus resize, transform, and fallback diagnostics | Raise a specific image-processing error for unreadable input; skip unreliable perspective correction safely |
| 3. OCR (`ocr.py`) | Processed and original grayscale image → raw OCR text and confidence diagnostics | Retry once if fewer than 30 non-whitespace characters; friendly OCR error if still empty; friendly setup error if Tesseract is unavailable |
| 4. Clean and section (`parser.py`) | Raw OCR text → preserved raw text, normalized copy, ingredient tokens, contains text, nutrition block | Return empty sections when headings are absent; preserve text and useful bracket contents |
| 5. Ingredient matching (`matcher.py`) | Tokens + flag records → unique matched flags and unrecognized tokens | Deterministic exact, synonym, then configured fuzzy matching; one token resolves to at most one record |
| 6. Additive decoding (`matcher.py`) | OCR/ingredient text + additive records → normalized codes, decoded records, unknown codes | Unknown codes remain visible as `Unrecognised additive code`; avoid bare-number matches outside additive-class brackets |
| 7. Nutrition parsing (`nutrition.py`) | Nutrition text + configured limits → values with unit, basis, source span, comparability, status, and reason | Keep ambiguous values with a not-comparable reason; never silently convert salt to sodium |
| 8. Score and alerts (`scoring.py`, `matcher.py`) | Additives, flags, nutrient statuses, selected allergens → bounded score, band, breakdown, separate allergen alerts | Deterministic configured deductions; an alert never depends on score |
| 9. Report and save (`app.py`, `storage.py`) | Complete result → saved history item and browser result | Friendly storage error; history write uses lock, same-directory temp file, and atomic replace |

## Storage swap point

All persistence goes through `storage.py`: `load_knowledge()` loads and validates all four arrays, `get_history()` reads history, `add_scan(scan)` performs locked atomic read-modify-write, and `get_scan_by_id(scan_id)` reopens a saved result. Processing modules consume returned records and never read JSON files directly. Reimplementing these functions is the future JSON-to-MySQL migration boundary.

## Result object

The result object has `scan_id`, `scanned_at`, sanitized display `image_name`, `image_path`, `processed_image_path`, `user_allergens`, `raw_text`, `normalized_text`, `ingredient_tokens`, `ingredient_text`, `contains_text`, `nutrition_text`, `additives`, `unknown_additive_codes`, `ingredient_flags`, `allergen_alerts`, `nutrients`, `health_score`, `score_band`, `score_breakdown`, `score_totals`, `unrecognised_tokens`, `diagnostics`, and `disclaimer`. Each nutrient retains `name`, `value`, `unit`, `basis`, `source_span`, `status`, `reason`, and threshold source where available. Each alert retains group, matched keywords, source sections, and whether the group was selected. Diagnostic fields include preprocessing steps/fallbacks, OCR confidence/retry information, and processing time; no absolute file-system paths are returned.

## Routes

- `GET /`: scan page.
- `POST /scan`: multipart image plus selected allergens; returns the result object as JSON or renders the result page.
- `GET /history`: history page.
- `GET /api/history`: JSON scan summaries.
- `GET /api/history/<scan_id>`: saved result JSON, or 404.
- `GET /uploads/<path:filename>`: serves only files beneath the controlled local upload directory for result-image comparison.
- Standard 404 and friendly error responses; no stack traces in user-facing pages.

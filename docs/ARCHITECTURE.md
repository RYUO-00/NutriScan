# NutriScan Architecture

## Three layers

1. **Browser frontend:** offline HTML, CSS, and JavaScript for photo selection (with browser-provided camera capture where available), allergen preferences, scan progress, result views, comparison, and history.
2. **Flask backend:** thin routes validate requests and orchestrate the nine processing stages through focused modules.
3. **Local data and files:** four UTF-8 JSON knowledge arrays, JSON scan history, and controlled local uploads. The first release is single-process and single-user.

## Local and optional LAN startup

- `python app.py` is the default and binds Flask to `127.0.0.1:5000`, keeping access on the laptop.
- `python app.py --lan` is an explicit opt-in that binds to `0.0.0.0:5000` so another device on the same private Wi-Fi can connect using the laptop's IPv4 address. Startup prints a network-access warning.
- Both modes keep Flask debug mode and the reloader disabled. The application does not edit firewall rules. LAN mode is intended only for a trusted private network; see the README and `docs/SECURITY.md` before using it.
- Templates generate application paths with Flask `url_for()`. Frontend requests and navigation therefore use the host from which the page was opened, including a laptop's LAN address.

## Nine-stage pipeline and module contracts

| Stage / module | Input → output | Failure behaviour |
|---|---|---|
| 1. Upload (`app.py`, `config.py`) | Multipart image + selected allergen groups → validated upload path and safe ID | Friendly 400 for missing/empty, unsupported, oversized, or undecodable images; never use raw filename as a path |
| 2. Preprocess (`preprocess.py`) | Image path/array → original and processed image paths/arrays plus resize, transform, and fallback diagnostics | Raise a specific image-processing error for unreadable input; skip unreliable perspective correction safely |
| 3. OCR (`ocr.py`) | Processed and original grayscale image → whole-page OCR plus optional separately recorded nutrition-panel retry and confidence diagnostics | Up to three whole-page attempts and four bounded panel attempts if an OCR heading and suitable light panel identify a crop; friendly empty/setup errors |
| 4. Clean and section (`parser.py`) | Raw OCR text → preserved raw text, normalized copy, ingredient tokens, contains text, nutrition block | Preserve full nutrient-bearing text when headings are absent; retain empty ingredient sections and useful bracket contents |
| 5. Ingredient matching (`matcher.py`) | Tokens + flag records → unique matched flags and unrecognized tokens | Deterministic exact, synonym, then configured fuzzy matching; one token resolves to at most one record |
| 6. Additive decoding (`matcher.py`) | OCR/ingredient text + additive records → normalized codes, decoded records, unknown codes | Unknown codes remain visible as `Unrecognised additive code`; avoid bare-number matches outside additive-class brackets |
| 7. Nutrition parsing (`nutrition.py`) | Nutrition text + configured limits → values with unit, basis, source span, comparability, status, and reason | Keep ambiguous values with a not-comparable reason; never silently convert salt to sodium |
| 8. Score and alerts (`scoring.py`, `matcher.py`) | Additives, flags, validated nutrient values, selected allergens → score/status, breakdown, separate allergen alerts | Recheck configured cutoffs at the scoring boundary; no comparable data means no score/band; partial data is provisional; alerts remain independent |
| 9. Report and save (`app.py`, `storage.py`) | Complete result → saved history item and browser result | Friendly storage error; history write uses lock, same-directory temp file, and atomic replace |

## Storage swap point

All persistence goes through `storage.py`: `load_knowledge()` loads and validates all four arrays, `get_history()` reads history, `add_scan(scan)` performs locked atomic read-modify-write, and `get_scan_by_id(scan_id)` reopens a saved result. Processing modules consume returned records and never read JSON files directly. Reimplementing these functions is the future JSON-to-MySQL migration boundary.

## Result object

The result object has `scan_id`, `scanned_at`, sanitized display `image_name`, `image_path`, `processed_image_path`, `user_allergens`, `raw_text`, `normalized_text`, `ingredient_tokens`, `ingredient_text`, `contains_text`, `nutrition_text`, `additives`, `unknown_additive_codes`, `ingredient_flags`, `allergen_alerts`, `nutrients`, `health_score`, `score_band`, `score_breakdown`, `score_totals`, `unrecognised_tokens`, `diagnostics`, and `disclaimer`. Each nutrient retains `name`, `value`, `unit`, `basis`, `source_span`, `status`, `reason`, and threshold source where available. Each alert retains group, matched keywords, source sections, and whether the group was selected. Diagnostic fields include preprocessing steps/fallbacks, OCR confidence/retry information, and processing time; no absolute file-system paths are returned.

## Routes

Results also retain `analysis_version`, `score_status`, and `data_completeness` (recognized/comparable/missing/unverified nutrients, core-field coverage, section availability, and explanation messages). `health_score` and `score_band` are null when no numeric score can be supported. New reports keep their versioned calculation when reopened. Legacy report reads re-analyze stored OCR in memory and expose the previous score as historical metadata; they do not re-run OCR or alter storage. See `docs/SCORING.md` for the admission policy and methodology audit.

Revision 3 retains serving metadata, separate solid/liquid threshold selection, FDA serving-based added-sugar comparison, percentage coverage, and qualitative confidence (plus the optional mean OCR diagnostic). Missing information is not a numeric value or penalty. Majority core coverage or a validated nutritional concern supports a score; partial scores remain provisional. Total/added sugar share one strongest deduction. Full precision is retained through comparison and display rounding is separate from calculation.

Revision 4 keeps whole-page OCR as the source for allergens and ingredients even when a separately captured nutrition panel yields better nutrient evidence. The panel text and OCR diagnostics are retained for report reopening and displayed in the OCR disclosure. Multi-column values require explicit matching columns or a supported OCR-position match; compatible rounded serving/100-unit readings prefer the directly stated per-100 reading. Borderline numeric OCR can be used only when independent attempts agree on the exact value, unit, basis, and serving size; this is a heuristic, not a guarantee. Historical reports are re-evaluated from their available stored evidence without modifying their files.

- `GET /`: scan page.
- `POST /scan`: multipart image plus selected allergens; returns the result object as JSON or renders the result page.
- `GET /history`: history page.
- `GET /api/history`: JSON scan summaries.
- `GET /api/history/<scan_id>`: saved result JSON, or 404.
- `GET /uploads/<path:filename>`: serves only files beneath the controlled local upload directory for result-image comparison.
- Standard 404 and friendly error responses; no stack traces in user-facing pages.

## Revision 5 OCR evidence recovery

An incomplete panel may receive two additional bordered grayscale whole-page attempts (PSM 6 and 4), even if one earlier nutrient was usable. Full-page selection ranks distinct comparable core fields before confidence/text length. Whole-page attempts remain bounded at five, panel attempts at four; each invocation has a configurable 15-second timeout. A supplementary crop can use an OCR nutrition heading and several row coordinates when there is no distinct light panel. Optional timeout failures retain prior readable text. No recognized nutrient scalar values are pooled across different candidates.

Nutrition parsing accepts adjacent reversed serving-size headers, split Calories and English anchors on bilingual panels. Borderline serving sizes require repeated exact mass/volume evidence above the existing minimum confidence gate. Prepared-food columns require an explicit resolved row basis; unresolved values are not scored as the product alone. Report OCR diagnostics retain corroborated_serving_sizes as well as corroborated_readings. Analysis version 5 changes extraction/evidence review; score weights and thresholds remain unchanged.

## Revision 6 — separate OCR resolution and score scope

preprocess_image retains original_gray at native resolution up to OCR_MAX_LONG_SIDE (4500). Its independently resized display_gray and binary processed preview use PREPROCESS_LONG_SIDE (1800). Production OCR starts on original_gray, never the resized preview. Panel contour detection is limited to the display long side and maps bounding boxes to native pixels; TSV boxes from rescaled retries are also mapped back before detecting panels.

After the first pass, retry scaling targets median confident alphanumeric word height OCR_TARGET_WORD_HEIGHT (30 px). The 4500 px bound includes retry borders. A missing TSV word-height estimate uses the existing bounded size fallback; a measured small font may scale beyond the legacy 3x limit to reach 30 px within the pixel cap. Incomplete pages can use block/single-column grayscale plus illumination flattening by cv2.divide(gray, GaussianBlur(gray), scale=255), with the same word-size normalization. At most six whole-page and four panel attempts are available. Each Tesseract invocation retains its 15-second timeout. Diagnostics record native OCR dimensions, first median word height, retry scale and variants.

Scoring now distinguishes sufficient, provisional, ingredient-only and insufficient. When nutrition cannot meet the existing minimum but matched additive/flag records exist, ingredient-only applies the existing ingredient/additive weights and caps and excludes nutrient contributions. Nutrition status stays insufficient in data_completeness.nutrition_status. No matches and insufficient nutrition still return no score. Provisional UI reports based on N of 5 nutrients. Below 60% coverage its band cannot exceed Moderate; ingredient-only is also capped at Moderate. Caps change the band, not points or ledger arithmetic. Policy constants remain in config.py. Result/history/API routes and element IDs are retained; reports use analysis version 6.

## Main integration — revision 7

Retain the remote optional trained-data selectors/fallback, LSTM OEM 1, vocabulary hints, deskew helper, page/word TSV metadata, coordinate-based nutrition-row association, bracket-aware ingredients, and original benchmark control/model/matrix/pipeline modes. Manifest replay is an additional CLI dispatched through scripts/benchmark_replay.py. Production initial OCR follows the native grayscale requirement; OCR_PRIMARY_VARIANT is a retained legacy configuration name, not permission to substitute the display preview. Recognition diagnostics include both actual invocation/model/timing fields and native-size/word-height/serving/preparation metadata. Current default limits are six whole-page attempts and two panel attempts, with earlier readable evidence retained on an optional timeout. All scoring contributions remain in the existing scorer with revision-6 scope rules.

# NutriScan Test Plan

## Tesseract enhancement benchmark — 20 Nov 2026

`scripts/benchmark_ocr.py` compares installed/official best/official fast English packs with OEM 1 and identical grayscale PSM 6 controls; a separate matrix evaluates grayscale, CLAHE, legacy preprocessing, Otsu, gentle adaptive, deskew and bounded deskew/enlargement with PSM 6/11/3. Vocabulary is a paired optional comparison, and `--numeric-probe` restricts characters only on an explicitly numeric line using PSM 7. Model files are pinned/checksummed and remain ignored. `tests/ocr_real_labels.json` contains manually checked fields from eight user-supplied real-label images; their images are supplied with `--real-dir` and are not redistributed. Five bundled synthetic categories provide full text for CER/WER. These development data do not support representative accuracy claims.

Recognition CER/WER, raw parsed-field accuracy, verified end-to-end fields, ingredient/additive/allergen recall, false positives, serving extraction, timing and failures are separate measurements. Missing/ambiguous fields remain misses and unverified values cannot earn correctness credit. Baseline verified values are evaluated from the original saved capture rather than recomputed through changed parsing. JSON sidecars include input/model/source hashes, individual outputs and errors. The legacy `evaluate.py` now uses the same confidence-aware analysis and panel evidence as Flask.

New automated cases cover optional-model absence/corruption, strict benchmark model selection, Windows paths, OCR timeout, curated vocabulary, known-value real OCR with each available model, preprocessing input preservation, conservative deskew, coordinate recovery with either column order, explicit row units, ambiguous/multiple panels, bounds, percentages, low-confidence values, and complete accounting of panel retries. Existing route, upload, scoring, history and JSON checks remain in the suite. Browser QA covers fresh clear/weak/ingredient-only scans, invalid/unreadable input, OCR disclosure, scores/alerts, image loading, history reopening, console/server logs, and desktop/360 px layouts.

Completed verification: **168 pytest tests passed**, 300 knowledge records validated, 403 benchmark runs plus six numeric probes, and ten legacy evaluation runs with no scan failures. The actual in-app browser checks and inspected 1440×900/360×844 captures are recorded in [the final report](../results/ocr_summary.md#browser-verification). Both a fresh 68-point sample and an older stored 78-point cereal report reopened successfully. Invalid/unreadable uploads restored controls with 400/422 errors; no Flask 500 or browser console error was observed. Unresolved real-photo and rounding failures are retained in the benchmark, not counted as passes in extraction metrics.

## Evaluation metrics

- Ingredient/OCR recall against manually checked ingredient ground truth.
- Additive detection precision and recall.
- Nutrition extraction accuracy within an explicit numeric tolerance, with correct unit and basis.
- Allergen group/keyword detection against ground truth.
- Median and average processing time; compare preprocessing disabled and enabled on the same images.
- Report false positives and failures honestly; do not tune thresholds to hide them.

## Image categories

Clear and flat; slightly tilted; curved pouch or bottle; uneven lighting or glare; low-light or mildly blurry. Synthetic Pillow fixtures cover clear, tilted, noisy, low-contrast, and glare-like cases until real photos are added.

## Functional and unit coverage

- Valid combined label, ingredient-only label, nutrition-only label; unreadable/non-label image.
- Empty, unsupported, oversized, MIME-mismatched, and undecodable uploads; safe generated filenames.
- Additive formats E211, E 211, E-211, INS211, INS 211, E160a(i), 150d; unknown and context-sensitive bare codes.
- Matching order exact → synonym → fuzzy; configured threshold, one-record-per-token, and unrecognized output.
- Allergen groups, ingredient/advisory sections, selected critical alerts and non-selected warnings; context-dependent lecithin.
- Nutrition per 100 g, per 100 ml, per serving; mixed g/mg; nutrient aliases; serving conversions; salt versus sodium estimate; ambiguous/not-comparable values and source spans.
- Score hand-calculations for risk deductions, caps, beneficial offsets, bands, clamping, and full contribution reasons.
- JSON load counts/schema/enums/duplicate IDs/codes; malformed/missing knowledge file startup; malformed history; locked atomic history write, replacement, lookup, missing scan, and write failure.
- Every route: scan page, valid and invalid scan, history page/API, saved result reopen, and 404s. Confirm errors are friendly and no stack trace is exposed.
- Run `scripts/validate_data.py` in pytest and directly; verify `DATA_REVIEW.md` enumerates every assumed record.

## Evaluation artifacts

`scripts/make_sample_labels.py` creates deterministic synthetic images and matching JSON under `tests/ground_truth/`. `evaluate.py` processes the sample set with preprocessing off/on and writes `results/evaluation.md` and `results/evaluation.csv` with metrics, timing, and failures.

## Always-100 regression cases — 20 Nov 2026

`tests/test_pipeline_regressions.py` injects known OCR transcripts into real Flask uploads, preserving preprocessing, parsing, matching, scoring, JSON storage, saved API reads, report rendering, and image-route checks. This makes the following results deterministic; it does not claim OCR accuracy on ten real photographs. Separate existing Tesseract tests and a manual re-read of the four distinct failing original uploads cover OCR behavior.

| Case | Fixture result | Status | Verification |
|---|---:|---|---|
| High sugar, 35 g/100 g | 85 | Sufficient | Existing 15-point high deduction |
| High saturated fat, 8 g/100 g | 85 | Sufficient | Existing 15-point high deduction |
| High sodium, 900 mg/100 g | 85 | Sufficient | Existing 15-point high deduction |
| Trans fat, 3 g/100 g | 85 | Sufficient | Existing 15-point high deduction |
| Four high nutrient concerns | 40 | Sufficient | Four 15-point deductions |
| No readable nutrition | No score | Insufficient | Null score/band; no applied contributions |
| Incomplete OCR; only sugar can be verified | 85 | Provisional | Missing/unverified fields listed |
| Valid nutrients without additive matches | 64 | Sufficient | Three medium plus one high deduction |
| Hazelnuts, skim milk, tree-nut declaration | No score | Insufficient | Selected Tree nut alert and separate Milk warning remain visible |
| Potassium 170mg on an otherwise low panel | 100 | Sufficient | No false additive code; sodium keeps its own value |

All ten pass. Every published numeric result reconciles with the contribution sum. Additional cases cover low-confidence numbers and basis, unlabelled columns, conflicting readings, unsafe serving conversion, explicit zero versus missing values, status-only inputs, partial perfect-score withholding, salt/sodium double counting, OCR retry selection, and legacy history review without rewriting stored data. Full suite: 108 passed.

Manual OCR re-reading of the four distinct original failing uploads returned insufficient data for all four, with available allergen matches retained. These photos still lack enough verified value/basis information for a numeric score. The bundled sample's real OCR still yields 68, with 5/5 core readings verified and a contribution sum of 68. The in-app browser was disabled in Work settings during this pass; current status HTML is covered by route tests, but a fresh visual browser inspection remains unperformed.

## Revision 3 reference and partial-data regression — 20 Nov 2026

`tests/test_reference_scoring.py` covers the eight requested profiles through real Flask upload, analysis, persistence, API and HTML rendering. OCR transcripts are controlled in these route cases; a separate clean image generated from the supplied Nutella reference runs real OpenCV/Tesseract. The healthy reference is the [manufacturer's 150 g plain nonfat yogurt panel](https://usa.fage/products/yogurt/fage-total-0), checked 20 Nov 2026 (80 kcal, zero total/saturated/trans fat, 55 mg sodium, 5 g total sugar, no added sugar, 16 g protein, 230 mg potassium). This records a nutrition fixture, not a general health or allergen-safety endorsement.

| Case | Score | Status | Result |
|---|---:|---|---|
| Nutella reference, 37 g serving | 55 | Sufficient | Pass |
| Plain nonfat yogurt manufacturer reference | 100 | Sufficient | Pass |
| High-sugar fixture | 85 | Sufficient | Pass |
| High-sodium fixture | 85 | Sufficient | Pass |
| Unreadable nutrition | None | Insufficient | Pass |
| One missing nutrient with reliable high sugar | 85 | Provisional | Pass |
| Identical duplicate nutrient rows | 85 | Sufficient | Pass; one deduction |
| Complete Nutella nutrition without ingredients | 55 | Sufficient | Pass |

Additional tests cover four reliable low readings with 80% coverage, a single unverified/conflicting field, stated-serving normalization for liquids, the exact FDA added-sugar high boundary, configurable point weights, split/interleaved serving metadata, and ambiguous “Fat” qualifiers. Every published score equals the contribution sum. Missing/empty data and a lone low reading cannot automatically produce 100. Real OCR of the complete reference returns 55; OCR of the original blurry photo recovers 37 g and reliable fat values, yielding 70 provisional at 40% core coverage. Right-column values are not inserted from the transcript. Full suite: **128 passed**.

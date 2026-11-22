# NutriScan Test Plan

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

## Comparison and mobile photo-picker regression

- Verify the desktop frame shows the uploaded original on the left and the preprocessed image on the right; moving the slider toward 95% reveals more processed image.
- Verify the narrow layout shows the complete original above the complete processed image and allocates the row heights consistently with the slider.
- Verify the upload control accepts JPG/PNG without a forced `capture` attribute, allowing mobile users to select saved photos. Browser-provided camera options may vary by device.

## Revision 5 verification — 22 Nov 2026

New automated cases cover reversed same-line/preceding-line serving amounts, conflicting or borrowed serving quantities, bilingual English anchors, split unitless Calories, fatty-acid labels, confidence isolated to serving amount, exact repeated borderline serving evidence (including rejection below the minimum), bounded rescue for partial and empty OCR, optional timeout preservation, coordinate-crop admission and unresolved prepared-food columns. Existing score, normalization, allergen, history and route cases remain enabled.

Real replay uses six distinct existing uploaded images, with before/after OCR and analysis written only to ignored uploads/.ocr-review. These were selected difficult examples, not a representative accuracy benchmark. The clear 227 g panel changes from insufficient to 79 with 100% core coverage (100 - 21); the bilingual chips panel changes from insufficient to provisional 78 with 80% coverage (100 - 22). Missing saturated-fat units on the latter remain unverified. A blurry pastry panel and glare-covered jar still cannot support a score. Prepared-with-milk cereal values are excluded if their column cannot be placed, including a previously published provisional 78 whose value association could not be defended. The three-column cereal is also withheld. All published numeric ledgers reconcile; no known product transcript fills unreadable image values.

In-app browser verification uses a separate local server on port 5012 and isolated history/uploads: fresh 227 g and bilingual chips uploads show the above results, wheat selected before the chips scan produces a red alert, soy remains separate, both comparison images load, and saved reports reopen. Screenshots are stored under ignored uploads/.ocr-review. Physical phone use is not tested.

Final automated run: **161 passed in 14.19 s** using .venv/Scripts/python.exe -m pytest -q. A further browser fresh scan on the final server confirmed insufficient data for the unresolved product/with-milk table, with the preparation-column reason and independent selected-allergen alerts retained. Preparation warnings are tested to survive an OCR retry that drops the heading.

## Revision 6 verification and reproducible OCR benchmark

New regressions verify independent native/display resolution (3200 retained, 5000 capped to 4500), first-pass native grayscale, observed median-based scale including small fonts beyond 3x, pixel-bound handling, missing TSV fallback, illumination gradient reduction without losing dark ink, and retry-coordinate mapping back to native panels. Scoring tests cover ingredient-only weights/ledger, caution-only scope, no-evidence refusal, 20% band limiting, and the exact 60% boundary. Upload/save/reopen/history tests check ingredient-only warnings and provisional N-of-5 labels. The clean real-Tesseract Nutella test continues to require 55/sufficient and reads the selected separate panel evidence when present, as the production pipeline does.

The benchmark script was absent and has now been added. Before editing OCR/scoring, run:

    .venv/Scripts/python.exe scripts/benchmark_ocr.py --manifest results/ocr_benchmark_manifest.json --output results/ocr_before_v6.json

After changes, run:

    .venv/Scripts/python.exe scripts/benchmark_ocr.py --manifest results/ocr_benchmark_manifest.json --output results/ocr_after_v6.json --compare results/ocr_before_v6.json

The saved before report records version 5; the after report records version 6. SHA-256 joins ensure identical source bytes, duplicate inputs are not double counted, failed/unmatched inputs cannot become fabricated zero-count comparisons, and the script isolates Flask startup/history in temporary storage. Ten package photos plus two separately identified reference images are included. Counts mean distinct parser-admitted comparable core fields out of five, not manually confirmed correctness. No OCR failures occurred in either final run. Total 12/60 to 12/60; ten photos 3/50 to 3/50. Per-image counts and reasons are in results/ocr_after_v6.md and the JSON nutrient arrays. Gains: pastry 0 to 1 and bilingual chips 4 to 5. Regressions: cream 3 to 2 and clear graphic 5 to 4. Remaining eight images unchanged. This diagnostic set demonstrates mixed recovery and persistent limitations, not a general accuracy gain.

Full pytest after the phase's code/test changes: 174 passed in 45.57 s. Browser verification uses port 5012 and uploads/.ocr-review-v6 with isolated history; original scan history is not used for test writes.

Browser evidence: real ingredient photo = 97 ingredient-only with explicit nutrition warning; pastry = 93 provisional, based on 1 of 5, band Moderate. Checked the result at 360 px (no horizontal overflow) and history scope labels. Screenshots retained under ignored uploads/.ocr-review-v6. No physical-phone connection was tested.

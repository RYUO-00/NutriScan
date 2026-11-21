# OCR enhancement verification — 20 Nov 2026

## Scope and reproducibility

The pre-enhancement capture and final runs use five bundled synthetic images and eight user-provided photos. The photos are not redistributed. There are 78 manually checked nutrient fields across the 13 images; incomplete reference sets are explicitly marked in `tests/ocr_real_labels.json`. Full transcripts exist only for the five synthetic fixtures, so CER/WER below describe those fixtures only. Ingredient/allergen/additive figures are recall, not general accuracy or safety guarantees. Missing and unverified readings are misses. The data helped select the configuration and are not held-out validation.

Run the commands in [docs/OCR.md](../docs/OCR.md#reproduce-the-measurements). Detailed evidence is in the [model comparison](ocr_models_final.md), [preprocessing/PSM matrix](ocr_matrix_final.md), [complete runtime comparison](ocr_pipeline_final.md), and their JSON sidecars. Sidecars record executable version, model/input/source hashes, individual text/field outputs, errors and timings. The baseline is evaluated from its saved original analysis in `ocr_baseline.json`, not reprocessed by the new parser. Its raw parsed-field accuracy was not measured.

## Controlled model comparison

All three packs use identical original grayscale images, English, OEM 1, PSM 6, no vocabulary, and two runs per image. Extraction means verified nutrient field correctness, requiring the correct nutrient/value/unit/basis. This is a single-pass control, not the runtime retry policy.

| Model | CER | WER | Verified extraction | Raw parsed fields | Mean OCR seconds |
|---|---:|---:|---:|---:|---:|
| Installed | 3.5% | 24.8% | 30.8% | 46.2% | 0.764 |
| tessdata_best | 2.4% | 20.5% | 28.2% | 42.3% | 2.338 |
| tessdata_fast | 3.5% | 24.8% | 30.8% | 46.2% | 0.845 |

The installed pack is byte-identical to the pinned official fast pack (4,113,088 bytes). Best is 15,400,601 bytes; standard tessdata is 23,466,654 bytes. Standard tessdata was inspected/downloaded but is not included in the three-model accuracy comparison. Best improved synthetic recognition errors while worsening verified field extraction and latency. Its four incorrect verified readings in the repeated control represent two distinct cases: a wrong comparison basis on the green pouch and a lost fibre decimal on a cereal. Installed remains the default; best is an explicit optional choice, not an assumed upgrade. Installed/fast timing differences reflect local measurement variability despite identical recognition output.

## Full runtime: before and after

| Metric | Saved previous pipeline | Final installed pipeline |
|---|---:|---:|
| Synthetic CER | 8.5% | 3.0% |
| Synthetic WER | 25.3% | 22.2% |
| Verified nutrient fields | 38/78 (48.7%) | 45/78 (57.7%) |
| Incorrect verified reference fields | 1 | 1 |
| Ingredient term recall | 69.1% | 76.5% |
| Allergen group recall | 83.3% | 86.1% |
| Additive identity recall | 50.0% | 53.3% |
| Serving-size accuracy | 54.5% | 72.7% |
| Mean OCR elapsed seconds | 5.552 | 5.203 |
| Mean preprocessing + OCR + analysis seconds | 5.698 | 5.415 |

Final installed runtime averages 3.62 actual recognition calls per image, including panel calls. The old counter omitted panel calls, so its 2.62 average is not comparable. Runtime best reached 43.6% verified fields at 10.112 seconds mean OCR; runtime fast matched installed's 57.7% at 4.859 seconds. No benchmark run raised an unhandled scan failure; successful execution does not mean successful extraction. Several photos still return insufficient data.

These are descriptive local CPU measurements, not an independently controlled speed study. OCR elapsed time includes subprocess startup/model loading and retry assessment. Full benchmark time excludes upload/history writes. Each pytesseract call starts a separate Tesseract process and loads its pack; persistent model loading is not implemented. Isolated model-loading overhead and peak native/Tesseract RAM were not measured. Optional `--python-memory` instrumentation excludes those allocations and must not be represented as total scanning memory.

Per-image changes include:

- Clear/glare fixtures retain 8/8 verified fields and score 68. No scoring thresholds or point weights changed.
- Low contrast improves 5 → 7 verified fields; noisy improves 6 → 8 and score 82 → 68; tilted improves 2 → 4 and score 92 → 82. The corresponding parsed tilted values are 8/8, but four do not pass confidence admission.
- The gum ingredient photo improves 0 → 5 checked ingredient terms. Parenthesized `contains soybean lecithin` no longer truncates the ingredient paragraph. It correctly remains unscored because it has no nutrition table.
- Both cereal panels and cream still have partial extraction. The first cereal remains 90. The second changes 78 → 71; cream changes 67 → 70 as recognized evidence changes. These are not asserted to be ground-truth product scores. Cream's checked ingredient recall regresses 2 → 0 and the second cereal's 4 → 3; these misses remain visible in the sidecars rather than being removed from the denominator.
- Curved bottle, green/brown folded pouches and the very small Nutella image still have no verified reference nutrition fields. The Nutella image also misses visible allergen text. Better photos/manual label review remain necessary.

## Retained and rejected options

Gray PSM 6 raises single-pass verified fields from legacy adaptive PSM 6's 15.4% to 30.8%, with no incorrect verified fields in that control. Conservative deskew PSM 6 reaches 35.9%; it is used only when structure is incomplete and line-angle evidence agrees. PSM 11 is useful as a bounded retry; it is not universally superior. Gentle contrast and bounded small-text enlargement remain conditional. The matrix retains measurements for all investigated options, not mandatory runtime stages.

Paired vocabulary produced identical CER, WER and field extraction, so it stays disabled by default. The numeric-only PSM 7 probe worsened installed/fast CER from 5.3% to 26.3%; it is not enabled in the application. No whole-label digit whitelist, aggressive mandatory thresholding, missing decimal repair, unit invention or product-specific score was introduced.

## Browser verification

The application was started normally with `python app.py` (127.0.0.1:5000, debug disabled) and tested in the built-in in-app browser, not Chrome automation.

| Browser case | Observed outcome |
|---|---|
| Fresh `clear_flat.png` upload | 68/100, Moderate, 100% coverage; 100 − 34 + 2 = 68; eight actual nutrient values; protein/fibre/energy informational |
| Independent allergen/additive checks | Selected Peanut red; Milk/Soy/Wheat separately amber; INS 211 preservative and INS 322 emulsifier |
| OCR disclosure and images | Actual highlighted OCR text opens; both images have nonzero natural dimensions; slider changes 50 → 51 |
| Gum photo | Full ingredient paragraph retained, selected Soy red, no invented nutrition or score; selected deskew/enlargement PSM 6, three whole-image calls |
| Weak curved bottle | Deskew retry, three whole-image calls; low-confidence quantity is not comparable; no numeric score |
| Blank valid PNG | Friendly no-readable-text message; HTTP 422; controls restored |
| Invalid PNG contents | Friendly cannot-decode-image message; HTTP 400; controls restored |
| Fresh history reopening | Clear scan reopens at stored 68 with 100% coverage |
| Older history reopening | Existing cereal reopens at stored 78, 60% coverage; both original/processed images load |
| Logo navigation | Returns to the scan landing page |
| Responsive review | 1440×900 and 360×844 screenshots captured and visually inspected; nutrient/additive text readable, comparison stacked on mobile, no horizontal overflow |
| Logs | Browser console warnings/errors empty on checks; Flask result/image/history responses successful, no 500/traceback; expected 400/422 and initial progress-poll 404 observed |

The browser temporarily timed out during the extra older-history check, recovered, and the check was completed. Viewport override was reset and original Peanut-only preferences restored. Browser scans used this worktree's ignored history/uploads, not the original checkout's history. Screenshots are local ignored artifacts under `design-review/ocr-browser/`: desktop/mobile full-page captures plus mobile summary/nutrients/additives/comparison and desktop comparison captures. They are intentionally outside project Git changes.

## Remaining review items

One installed-pipeline field differs from the exact printed per-100 reference: cereal total fat 0.8 g per 25 g normalizes to 3.2 g/100 g, whereas the printed per-100 value is 3.0 g and OCR omitted its unit. The valid serving reading is retained, but its rounding can cross the 3 g screening boundary. This is an existing normalization/rounding limitation, not a repaired missing unit. It remains in the error count and `DATA_REVIEW.md`; resolving threshold uncertainty from printed rounding needs a separate scoring-methodology decision. Other missed/uncertain units, decimals, basis and allergens remain limitations. Confidence and agreement are not proof of correctness.

## Automated checks and repository state

- `python -m pytest -q`: **168 passed** in 28.46 seconds, including real OCR checks for all three installed optional/control packs.
- `python scripts/validate_data.py`: **300 records passed** (180 additives, 45 allergens, 65 ingredient flags, 10 nutrition limits).
- `python evaluate.py`: ten synthetic off/on regression runs, zero failed scans; 35/40 verified nutrient fields in each mode. Both use gray-first runtime, so this legacy report does not isolate preprocessing effects.
- `git diff --check`: clean at verification.

This enhancement was committed and pushed to `codex/tesseract-ocr-enhancement`, based on `c584e16`. The original checkout remains on `codex/food-label-laboratory`; no branch merge or automatic copy was made. The unrelated untracked ZIP/design-review files were preserved outside the commit. No system-wide Tesseract modification was performed. The phase-specific file list is in [docs/OCR.md](../docs/OCR.md#files-in-this-enhancement).

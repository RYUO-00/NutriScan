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

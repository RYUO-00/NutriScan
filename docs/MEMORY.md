# Project Memory

## Current status

Phase 7 and the follow-up correction set are complete: the local Flask application, validated 300-record JSON knowledge base, OCR/preprocessing and full report pipeline, accessible offline UI, history storage, tests, synthetic evaluation, and cross-platform README are complete. Source guide and project documents were reviewed before implementation.

## Last done

Created the required project notes before code, then built all seven phases. The pins include NumPy 2.2.6, which supports Python 3.10+; the local `.venv` was verified on Python 3.11.9. Tesseract 5.4.0.20240606 with English data is configured and detected. The four knowledge files contain 180 additive, 45 allergen, 65 ingredient-flag, and 10 nutrition metadata records; all 300 assumption-marked records are in `DATA_REVIEW.md`. Follow-up work replaced broad additive categories with code-specific functional classes; 12 ambiguous or multi-function additive records are listed for review. Protein and fibre are informational and do not affect scoring; energy is informational while its threshold is unverified. The sample result now explains the 100-to-68 score change. Source strings are deduplicated in a collapsed result section, caution flags have distinct one-line reasons, selected allergen alerts are separated from other detected allergens, timestamps are formatted only in the UI, and comparison labels sit outside a shared image viewport. Startup creates an empty local history array when missing, and Git ignores local scan history and uploads. The latest full suite passes (57 tests); direct data validation passes (300 records), `pip check` is clean, and `evaluate.py` writes CSV/Markdown for five synthetic categories with preprocessing off/on (10 successful runs). The generated report records imperfect nutrition results and a degraded noisy-image case with preprocessing enabled. The local browser sample scan was run end to end with Peanut selected; the saved result reopens with additive `211` and name-matched `322`, separate allergen alerts, nutrient table, score explanation, and comparison images. No absolute local image path is included in the saved result object.

## Latest fresh-scan correction — 31 Oct 2026

The image comparison uses an explicit shared frame and viewport, separate caption badges, and a responsive stacked layout on narrow screens; the existing slider remains active. Score breakdowns show the point changes in plain language, and energy, protein, and fibre stay informational even when legacy saved data labels them High. The fresh local sample scan and HTML checks passed. Screenshots at 1440 px and 360 px were not available because Work settings disabled local in-app browser access; no visual screenshot inspection was performed.

## Open issues

- The 300-record dataset includes project assumptions. Review `DATA_REVIEW.md` against current FSSAI and other applicable sources before submission.
- Twelve additive functional-class entries remain explicitly unresolved pending a decision on which listed Codex function to show for the group entry.
- Real label photos are not supplied; synthetic fixtures cannot establish real-world OCR performance. Add real labels and manually checked ground truth before making performance claims.
- Nutrition cutoffs, risk classifications, and the score remain draft screening assumptions; numeric thresholds are centralized in `config.py`.
- History is single-user local JSON with indefinite retention. The README documents manual cleanup.

## Next step

Manual next step: review the 300-row assumption queue and test with real package photos/ground truth. Keep any source corrections in the data review workflow, regenerate evaluation artifacts, and rerun the suite before submission.

## Prompt B — `design-impeccable` branch — 31 Oct 2026

The scan, result, history, and error pages now follow the “page is the label” direction: warm paper, heavy rules, compact monospace labels, a strong score stamp, semantic alert colors, an original local logo, and page-specific metadata. Existing routes, element IDs, and core interactions remain covered. Scan progress comes from the real server-side pipeline stages; OCR marks and related report cards link by keyboard and pointer. Actual sample-label scans were inspected in the in-app browser. Captures for scan, result, and history at 1440 px and 360 px were visually reviewed; no horizontal overflow remained, mobile comparison images stack, and the screenshot review caught and fixed hidden-state and OCR disclosure layout issues. Branch test suite: 59 passed. Screenshot evidence is local and ignored under `design-review/design-impeccable/`.

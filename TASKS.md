# NutriScan Phase Checklist

Work one phase at a time. Mark a phase done only after its tests pass; update this file and `docs/MEMORY.md` at each phase boundary.

- [x] **Phase 1 — Skeleton and environment.** Required modules/folders exist, Python dependencies are pinned after an install, Flask app starts with one command, and Tesseract configuration is explicit. Done when startup checks pass. Verified in `.venv` on Python 3.11.9; Tesseract 5.4.0.20240606 with English data responds from the configured path; Flask served `/` with HTTP 200; pytest: 2 passed.
- [x] **Phase 2 — JSON knowledge base and validation.** Four UTF-8 knowledge arrays meet target counts; validator checks schema, counts, enums, duplicate IDs/codes; assumptions are enumerated in `DATA_REVIEW.md`. Done when validator and its pytest coverage pass. Direct validator and pytest passed; 300 records are present and all 300 are listed for review.
- [x] **Phase 3 — OCR and preprocessing.** Upload-safe image preprocessing, diagnostics, perspective fallback, Tesseract confidence and retry, and clear OCR failures. Done when image/OCR unit cases and sample checks pass. Resize/grayscale/denoise/CLAHE/adaptive threshold and optional quadrilateral correction are implemented; weak OCR retries once; pytest: 11 passed, including a generated clear-label OCR check.
- [x] **Phase 4 — Parsing, matching, and decoding.** Section extraction, tokenization, additive code formats, exact/synonym/fuzzy matching, allergens, and unknown visibility are integrated in an end-to-end path. Done when unit cases and pipeline checks pass. Verified by the full 49-test suite and the live sample scan; recognized parenthetical additive names are matched without losing raw text.
- [x] **Phase 5 — Nutrition and scoring.** Unit/basis-aware parsing and explainable configured score with caps/bands. Done when hand-calculated cases and comparison safeguards pass. Full suite passes; mixed units/bases and per-serving safeguards are covered; every active weight/cutoff is configured centrally.
- [x] **Phase 6 — Routes, UI, and history.** Scan/result/history experience, sample button, accessibility, offline assets, friendly failures, atomic persistence and reopening. Done when route and interaction tests pass. Route suite passes; sample button was exercised in the browser with a remembered selected allergen, and the saved result reopened with its original/processed images.
- [x] **Phase 7 — Tests, evaluation, and README.** Full requested test suite, synthetic image/ground-truth generator, preprocessing-on/off evaluation outputs, cross-platform setup, assumptions, and limitations. Done when pytest, data validation, evaluation, and startup checks pass. Final checks: pytest 49 passed, validator 300 records, dependency check clean, evaluation 10/10 scans without OCR/preprocess failures, and the final local app/sample path returned a saved result.

## Follow-up corrections — 31 Oct 2026

- [x] Protein and fibre are informational and do not reduce the score; energy is informational while its cutoff remains an assumption. The sample label score is shown as 100 before configured scoring rules and 68 after.
- [x] Additive functional classes use code-specific Codex entries. Twelve multi-function or otherwise unclear records are explicitly queued in `DATA_REVIEW.md`.
- [x] Source strings remain in the JSON data and are shown once per unique string in the result disclosure. Result and history timestamps are human-readable while saved/API values remain ISO.
- [x] The comparison slider uses one shared image viewport with captions outside the image area. Selected allergen matches use the red alert section; other matches use the amber “Also contains” section.
- [x] Caution flags have distinct ingredient-specific reasons. Git ignores local history and uploads, and startup creates an empty history array when missing.
- [x] Verification after these changes: `pytest` — 55 passed.

## Fresh-scan regression follow-up — 31 Oct 2026

- [x] The comparison now has a positioned, explicitly sized shared frame; its caption badges occupy a separate row, both images share the same viewport on wide screens, and the existing slider adjusts the stacked panels on narrow screens. Ingredient and additive lists use the same card width.
- [x] Energy, protein, and fibre render as informational text without status chips or score deductions. The sample scan shows 100 before scoring and 68 after: −6 additive points, −28 from total fat/saturated fat/sugar/sodium, and +2 for whole wheat flour.
- [x] The rendered source strings remain intact in data and appear only inside the collapsed source disclosure. User-facing calculation copy no longer exposes configuration wording.
- [x] Fresh scan confirmed INS 211 as Preservative and INS 322 as Emulsifier. All 12 unresolved or multi-function additive classes remain listed in `DATA_REVIEW.md`; caution flag reasons are specific.
- [x] Fresh local sample scan returned HTTP 200. Full verification: `pytest` — 57 passed; data validation — 300 records.
- [x] The 31 Oct correction pass had no screenshot capture; the follow-on redesign closed that visual-review gap with local Chromium captures and inspection at 1440×900, 1024×768, 390×844, and 360×844.

## Food Label Laboratory redesign — complete

- [x] Safety preflight: started from clean `main` at `f948930`; work is isolated on `codex/food-label-laboratory`.
- [x] Read the brief and project guidance; added `PRODUCT.md` and `docs/DESIGN_REVIEW.md` with baseline findings, constraints, direction candidates, and a screen plan.
- [x] Rendered and inspected baseline scan, result, and history pages at 1440 px and 360 px using local headless Chromium; the in-app browser bridge is disabled by Work settings.
- [x] Verified the complete brand anchor returns to `/` from scan, history, and result. Verified saved original and processed files exist and both media routes return HTTP 200; the reported navigation/image failures were not reproduced.
- [x] Replaced timer-cycled progress labels at the backend with a six-stage in-memory progress API, including completion and friendly failure state; added route coverage. Full suite: 59 passed.
- [x] Direction round resolved: the user selected the competitive Airport Wayfinding challenger; the Food Label Laboratory identity and safety semantics remain pinned in `.impeccable/surfaces/templates-index-html.md`.
- [x] Redesign the scan page with the selected route bands, photo drop zone, removable preview, allergen preferences, sample label specimen, and accurate six-stage progress; full suite: 59 passed.
- [x] Redesign the result report and history archive. The report now leads with the score, selected alerts, comparable nutrient bars, matched findings, a reconciled score ledger, image evidence, and source/OCR disclosures. History now shows readable timestamps, thumbnails, score bands, allergen state, and reopen actions.
- [x] Final redesign verification — 1 Nov 2026: `.venv` pytest 62 passed; `scripts/validate_data.py` passed all 300 records; `evaluate.py` completed 10 runs with 0 failed scans; `git diff --check` passed.
- [x] Render and inspect scan, result, and history at 1440×900, 1024×768, 390×844, and 360×844. Result-section captures cover nutrients, findings, and image comparison at desktop plus the stacked comparison at 360 px. Browser checks found no horizontal overflow or page errors; original and processed sample images both returned HTTP 200; the slider and logo navigation worked.
- [x] Fix two issues found in fresh visual QA: the desktop comparison panels had zero dimensions despite loaded image files, and the mobile history score overlapped the product row. The comparison now has explicitly sized layers within one shared frame; the history score occupies its own mobile row.
- [x] Finish review returned `ship`; its single requested contract fix was resolved by removing the raw seed key from both direction FORM blocks. Recaptured all 17 screenshots; the reviewer validated them and accepted the user-provided quality bar.
- [x] Refreshed `docs/DESIGN.md` from the shipped UI after the user chose refresh, and wrote `.impeccable/design.json` as its token/component sidecar.

## Optional mobile access over local Wi-Fi — 1 Nov 2026

- [x] Preserve laptop-only startup as the default (`127.0.0.1:5000`) and add explicit `python app.py --lan` binding (`0.0.0.0:5000`), with a terminal warning and debug/reloader disabled in both modes.
- [x] Generate navigation, scan, progress, sample-label, result, and image routes through Flask URLs so they use the host that served the page.
- [x] Document exact Windows Wi-Fi/IP steps, Private-profile-only firewall commands, and trusted-network/public-exposure boundaries in README.md; update architecture and security notes.
- [x] Add startup binding/debug tests, route-based original/processed upload checks, and frontend host-literal checks. Verification: `\.venv\Scripts\python.exe -m pytest -q` — 65 passed. Both real startup modes returned HTTP 200 locally, including LAN mode via the machine's interface IPv4.

## Final result dashboard refinement — 1 Nov 2026

- [x] Lead the result report with the dynamic backend score and band; keep the filename as metadata and label the score as informational. Add starting/deduction/credit/final totals and a waterfall derived from the same score contributions while retaining the detailed ledger.
- [x] Preserve threshold bars and show energy, protein, and fibre as informational rows without status chips or score effects.
- [x] Render and inspect the fresh sample at 1440×900 and 360×844, plus desktop/mobile score and image-comparison sections. Verify alerts, nutrient values, image responses, slider, logo, history reopening, and no horizontal overflow or browser errors.
- [x] Final verification: `.venv` pytest 67 passed; the browser score summary reconciles to the saved backend result (100 − 34 + 2 = 68).

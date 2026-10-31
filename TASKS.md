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
- [ ] 1440 px and 360 px screenshots could not be captured because Work settings disable local in-app browser access. Result HTML and responsive CSS assertions passed; visual screenshot inspection remains unavailable in this session.

## Prompt B — `design-impeccable` branch — 31 Oct 2026

- [x] Applied the “page is the label” direction to scan, result, history, and error pages, including the original logo, local favicon assets, page metadata, and the existing information hierarchy.
- [x] Preserved existing routes, element IDs, and scan/result/history interactions. Scan progress now reports server-side pipeline stages instead of cycling through simulated progress; OCR findings can be followed between the report and recognized text.
- [x] Captured and visually reviewed scan, result, and history pages at 1440 px and 360 px in `design-review/design-impeccable/`. The review caught and fixed idle-state preview visibility and a narrow OCR disclosure layout issue. Layout metrics show no horizontal overflow at either width; the image comparison stacks on mobile.
- [x] Verification on this branch: `.venv\Scripts\python.exe -m pytest` — 59 passed.

# Project Memory

## Current status

Phase 7, the follow-up correction set, and the visual redesign are complete: the local Flask application, validated 300-record JSON knowledge base, OCR/preprocessing and report pipeline, accessible offline UI, history storage, tests, synthetic evaluation, cross-platform README, and refreshed design-system files are complete. The independent finish review returned `ship`.

## Last done

Created the required project notes before code, then built all seven phases. The pins include NumPy 2.2.6, which supports Python 3.10+; the local `.venv` was verified on Python 3.11.9. Tesseract 5.4.0.20240606 with English data is configured and detected. The four knowledge files contain 180 additive, 45 allergen, 65 ingredient-flag, and 10 nutrition metadata records; all 300 assumption-marked records are in `DATA_REVIEW.md`. Follow-up work replaced broad additive categories with code-specific functional classes; 12 ambiguous or multi-function additive records are listed for review. Protein and fibre are informational and do not affect scoring; energy is informational while its threshold is unverified. The sample result explains the 100-to-68 score change. Source strings are deduplicated in a collapsed result section, caution flags have distinct one-line reasons, selected allergen alerts are separated from other detected allergens, timestamps are formatted only in the UI, and the comparison uses an explicitly sized shared image frame. Startup creates an empty local history array when missing, and Git ignores local scan history and uploads. The latest full suite passes (67 tests); direct data validation passes (300 records), `pip check` is clean, and `evaluate.py` completed ten synthetic runs with zero failed scans. The browser sample scan reopens with additive `211` and name-matched `322`, separate allergen alerts, nutrient table, score explanation, and comparison images. No absolute local image path is included in the saved result object.

## Latest fresh-scan correction — 31 Oct 2026

The image comparison uses an explicit shared frame and viewport, separate caption badges, and a responsive stacked layout on narrow screens; the existing slider remains active. Score breakdowns show the point changes in plain language, and energy, protein, and fibre stay informational even when legacy saved data labels them High. The fresh local sample scan and HTML checks passed. Screenshots at 1440 px and 360 px were not available during this 31 Oct correction pass; the later redesign QA below supersedes that visual-verification limitation.

## Open issues

- The 300-record dataset includes project assumptions. Review `DATA_REVIEW.md` against current FSSAI and other applicable sources before submission.
- Twelve additive functional-class entries remain explicitly unresolved pending a decision on which listed Codex function to show for the group entry.
- Real label photos are not supplied; synthetic fixtures cannot establish real-world OCR performance. Add real labels and manually checked ground truth before making performance claims.
- Nutrition cutoffs, risk classifications, and the score remain draft screening assumptions; numeric thresholds are centralized in `config.py`.
- History is single-user local JSON with indefinite retention. The README documents manual cleanup.

## Next step

Manual next step: review the 300-row assumption queue and test with real package photos/ground truth. Keep any source corrections in the data review workflow, regenerate evaluation artifacts, and rerun the suite before submission.

## Optional mobile access over local Wi-Fi — 1 Nov 2026

Added an explicit `--lan` startup option while preserving loopback-only default behavior. Both startup modes use port 5000 with debug and the reloader disabled; LAN mode warns that other network devices can reach the unauthenticated prototype. Templates generate route URLs through Flask, including scan submission, progress polling, sample-label loading, result reopening, navigation, and saved-image requests. README now documents the Windows `ipconfig` workflow, actual laptop IPv4 usage, same-Wi-Fi limitations, and optional Private-profile firewall rule/removal. No firewall changes are made by the application. Verification: startup tests cover both bindings and debug settings; route tests check original and processed images through `/uploads/`; frontend checks reject hardcoded host literals. `.venv` pytest: 65 passed. Both app modes were launched and returned HTTP 200 from the host; LAN mode also answered on the host's Wi-Fi/LAN interface address. A physical phone connection was not tested.

## Food Label Laboratory redesign — 31 Oct 2026

The complete visual redesign is being developed separately from `main` on `codex/food-label-laboratory`; `main` remains at the clean pre-redesign baseline. The attached brief and all project docs were reviewed. `PRODUCT.md` and `docs/DESIGN_REVIEW.md` capture confirmed product context, baseline findings, functional risks, proposed hierarchy, and visual-source candidates. Baseline scan/result/history screenshots were rendered in local headless Chromium and inspected at 1440 px and 360 px because Work settings disabled the in-app browser bridge. The logo anchor worked from all three routes, and both saved comparison images existed and returned HTTP 200, so neither reported issue reproduced. The timer-driven frontend progress sequence was a verified defect; it now uses actual pipeline stage updates through `/api/scan-progress/<id>` with a ten-minute in-memory TTL and friendly error state. Route tests cover all six completed stages. The user selected the Airport Wayfinding challenger; its route-band rhythm and committed navigation yellow are adapted to NutriScan, while the Food Label Laboratory identity and allergen warning colors stay fixed. Full suite after progress work: 59 passed.

### Scan-page redesign phase — 31 Oct 2026

Replaced the scan page with the selected route-band composition, local Source Sans 3 variable font (OFL included), paper/ink typography, custom file drop zone, filename preview with removal, remembered allergen chips, bundled synthetic specimen, and a six-step pipeline list. The progress UI now polls actual backend stages using a per-request UUID and displays only reported work; it no longer invents stage timing. Preserved all existing scan-page IDs and sample, drag/drop, mobile capture, and submit behavior. Updated route/CSS assertions; `.venv` pytest passes: 59 tests. The remaining pages joined the same system in the 1 Nov completion pass.

### Result, history, and responsive QA — 1 Nov 2026

Completed the result report and scan archive redesign. The report uses actual score contributions, comparable nutrient thresholds, code-specific additive findings, ingredient flags, saved original/preprocessed images, raw OCR, and sources. It keeps non-selected allergens amber and selected allergens red; with no saved preference, the sample result had no red alert. History entries show readable timestamps, thumbnails, score bands, allergen state, and reopen actions.

Fresh Chromium inspection exposed two defects: the desktop comparison viewport and its absolutely positioned images collapsed to zero size, and narrow history rows placed the score over the filename. The comparison frame and both panels now receive explicit shared dimensions; mobile history places score and product on separate rows. Scan, result, and history screenshots were rendered and inspected at 1440×900, 1024×768, 390×844, and 360×844. Result section captures cover nutrient bars, matched findings, and desktop/mobile image comparison. Captures live under ignored `design-review/redesign/` and `.impeccable/review/`.

The sample result scored 68. Energy, protein, and fibre were informational; four other detected allergen groups appeared in amber; both comparison images loaded with HTTP 200. The range slider moved by keyboard, and the brand anchor navigated to `/` from scan, result, and history. Browser checks reported no JavaScript errors, failed requests, or horizontal overflow at the four target widths. Impeccable detector returned no primary findings, but warned that it could not resolve the Jinja stylesheet expression from `base.html`; the stylesheet was included as a separate target.

Final verification: `.venv` pytest 62 passed; `scripts/validate_data.py` passed all 300 records; `evaluate.py` completed 10 runs with zero failed scans; `git diff --check` passed. The independent finish review returned `ship`; its single raw-seed-key finding was removed from both FORM contracts and scored resolved in the recapture verdict pass. The user chose to refresh the existing `docs/DESIGN.md`; the documenter wrote it from the shipped UI and created `.impeccable/design.json`. No UI issues remained open in the reviewer verdict.

### Final result dashboard refinement — 1 Nov 2026

The result hero now gives the dynamic backend Health Score and band visual priority, with the uploaded filename in secondary metadata. The hero shows the starting and final score; the breakdown summarizes starting value, total deductions, total credits, and final score, then visualizes those same aggregates as a waterfall above the detailed contribution ledger. Both totals and chart use the stored scoring engine contributions, including any range adjustment when present. On the sample label the arithmetic is 100 − 34 + 2 = 68. Energy, protein, and fibre remain informational, with no status chips or score contributions. The existing warm paper, ink, yellow, serif/sans typography, allergen treatments, and threshold bars remain intact.

Fresh sample QA was rendered and visually inspected at 1440×900 and 360×844; separate captures cover score breakdown, nutrient rows, and desktop/stacked mobile comparison. Browser checks found one selected red allergen, three separate amber detections, actual nutrient values, reconciled score totals, both image routes returning HTTP 200, working slider/logo/history reopening, and no page errors or horizontal overflow at 1440, 1024, 390, and 360 px. The result HTML check confirmed source and assumption strings remain only in the collapsed sources disclosure. Final `.venv` pytest: 67 passed.

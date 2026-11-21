# Tesseract configuration and accuracy evaluation

## Audit and boundaries

NutriScan retains Flask, OpenCV, pytesseract, JSON knowledge/history, routes and the existing report design. Tesseract is the only recognition engine. This work changes recognition/configuration and necessary nutrient association; nutrient thresholds, scoring weights, credits, allergen policy and knowledge records are unchanged.

The audited Windows installation is Tesseract **5.4.0.20240606**, Leptonica 1.84.1, with `eng` and `osd` in `C:\Program Files\Tesseract-OCR\tessdata`. Its 4,113,088-byte English pack has SHA-256 `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2`, identical to the pinned official `tessdata_fast` English pack. The embedded model version is `4.00.00alpha:eng:synth20170629`; that is a data version, not the executable version. The previous pipeline used OEM 3, PSM 6 initially, PSM 11 on grayscale retry and PSM 3 on a bounded enlargement. It already retained TSV boxes and performed light-panel crops. It chose mainly by comparable nutrient count/confidence and omitted crop calls from `attempt_count`.

The three official collections differ: [`tessdata_best`](https://github.com/tesseract-ocr/tessdata_best) and [`tessdata_fast`](https://github.com/tesseract-ocr/tessdata_fast) provide LSTM models; [`tessdata`](https://github.com/tesseract-ocr/tessdata) also contains legacy data and integerized larger LSTM models. Controlled comparisons and the application use **OEM 1**. See the official [CLI reference](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html) and [image-quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html). No retraining, alternative OCR engine, GPU or external runtime service is introduced.

## Optional model installation

From the repository root, with the project environment active:

```powershell
python scripts/install_ocr_models.py tessdata_best tessdata_fast
```

The installer downloads English packs from pinned official GitHub revisions and verifies byte size and SHA-256 against `data/ocr/models.json`. It writes under `.local/ocr/`, which is ignored by Git. It never edits the system Tesseract installation. The standard `tessdata` pack can also be installed with the same command and its name. The downloaded binaries use the official repositories' Apache 2.0 licence. Do not commit them.

The default is the **installed** model. To select an alternative for one PowerShell session:

```powershell
$env:NUTRISCAN_OCR_MODEL = "tessdata_best"
python app.py
Remove-Item Env:NUTRISCAN_OCR_MODEL
```

Named choices are `installed`, `tessdata_best`, `tessdata_fast` and `tessdata`. For another data directory, set `NUTRISCAN_TESSDATA_DIR` to the directory containing `eng.traineddata`; relative paths resolve against the project root. `TESSERACT_CMD` still selects the executable. Missing optional data falls back to the installed pack and records a diagnostic. A pack that fails to load is not repeatedly retried until its file changes. Benchmark mode requires the named pack and refuses a silent fallback. A Windows/pytesseract quoting limitation is handled with existing Windows short paths; if the volume does not support them, use a directory without spaces. Unsupported paths produce a clear configuration error.

## Vocabulary and numeric restrictions

`data/ocr/food_words.txt` is a small, unique lowercase list selected from the existing knowledge base and nutrition terminology, rather than a copy of all records. `food_patterns.txt` supplies E/INS three-digit forms. Neither replaces Tesseract's normal dictionary. Enable the optional comparison with:

```powershell
$env:NUTRISCAN_OCR_VOCABULARY = "1"
python app.py
Remove-Item Env:NUTRISCAN_OCR_VOCABULARY
```

Vocabulary remains disabled by default unless measurements support a benefit. A numeric/units whitelist is tested only on an explicitly numeric synthetic line with PSM 7 through `--numeric-probe`; it is never applied to a whole label. It cannot reconstruct missing decimal points or quantities.

## Preprocessing, selection and retries

The existing binary preprocessing image and original upload are preserved for comparison/history. The benchmark compares original grayscale, gentle CLAHE grayscale, the existing median/CLAHE/adaptive output, Otsu, adaptive thresholding without median filtering, and deskewing, with PSM 6/11/3. Alternatives are constructed only when requested. Thresholding is not assumed to be beneficial for thin type or decimal points.

Runtime starts with original grayscale and PSM 6, selected from the controlled comparison. The existing binary image remains available for comparison and the `legacy_adaptive` primary configuration. Structurally weak output can trigger a grayscale PSM 11 retry. When several near-horizontal edges agree on a modest tilt, a deskewed grayscale attempt is available. Evidence of small print can trigger a bounded enlargement (at most 3×, long side 2400 px). A gentle contrast retry is available for unresolved panels. There are at most four whole-page image attempts. A light region containing an OCR nutrition heading, or at least three distinct nutrient labels, may receive at most two additional panel attempts, capped at 3000 px. Crops never replace whole-page ingredient/allergen OCR. Each subprocess has a 20-second timeout. Failed optional attempts are retained as diagnostics while usable whole-page evidence remains available; empty OCR produces the existing friendly failure state.

Selection uses a lexicographic structural comparison: unique comparable core fields, comparable nutrients, verified readings, identified sections, meaningful food vocabulary, suspicious numeric tokens, then confidence/text coverage. There is no weighted health-score adjustment for recognition quality. Confidence and agreement between separate passes remain heuristics, not independent statistical proof. Missing fields stay missing, and incomplete evidence retains the existing provisional/insufficient states.

Diagnostics retain selected model, OEM, preprocessing variant, PSM, duration, retry/fallback status, whole/panel attempt counts and per-attempt failures. `attempt_count` now includes panel OCR and model fallback calls. Pytesseract starts a subprocess and loads its model on each recognition call; no persistent model cache is claimed. System/model path checks and parsed assessments are reused within a scan where possible. Ordinary result pages retain their existing presentation.

## Nutrition geometry

TSV words retain page, block, paragraph, line and word identifiers, confidence and `[x, y, width, height]`. Boxes belong to the image/variant used for that OCR pass. Transformed boxes are never used as if they were original-image coordinates for crop selection.

A small table adapter groups aligned words below one recognized nutrition heading and identifies explicit 100g/100ml and same-row serving headers. Either column order is supported. A numeric cell needs its own unit, an adjacent unit, or an explicit unit in the nutrient row such as `Sodium(mg)`. Percentages do not become quantities; bounds remain bounds; multiple candidate values, missing units, uncertain headers, low confidence or multiple products are not repaired by guessing. Original text spans/boxes remain attached to coordinate-associated readings. Existing conflict, unit/basis, rounding and serving conversion checks still apply. `Fat, total`, `Saturated Fats(g)`, and `Trans fatty acids(g)` aliases support common labels without changing thresholds.

One separate parser defect was found with the gum photo: `gum base (contains soybean lecithin)` prematurely ended the ingredient section. A parenthesized `contains` now remains ingredient text, while a clear standalone `Contains:` declaration still recovers correctly even after a damaged bracket. This fixes section preservation; it does not infer allergens from a product name or change the scoring methodology.

## Reproduce the measurements

```powershell
python scripts/benchmark_ocr.py --mode control --repeat 2 --numeric-probe --real-dir "PATH_TO_UNPROCESSED_LABELS" --output results/ocr_models_final
python scripts/benchmark_ocr.py --mode matrix --real-dir "PATH_TO_UNPROCESSED_LABELS" --output results/ocr_matrix_final
python scripts/benchmark_ocr.py --mode pipeline --real-dir "PATH_TO_UNPROCESSED_LABELS" --output results/ocr_pipeline_final
python -m pytest -q
```

Omit `--real-dir` to run only the bundled synthetic images. Real photos are user-supplied and are not redistributed. `tests/ocr_real_labels.json` records manually checked visible fields, excluded/ambiguous fields and image names; each benchmark output records input hashes. Synthetic full transcripts come from the fixture generator. CER/WER are measured only where complete reference text exists. Parsed-field and confidence-admitted end-to-end accuracy are reported separately. Missing/unverified values count as misses. Reference values require the correct nutrient/unit/basis within 1% relative or 0.05 absolute tolerance. Recall and per-image false positives are recorded separately for ingredient/additive/allergen checks. Non-exhaustive real references do not support precision claims.

JSON sidecars retain model hashes, source hashes, individual outputs, timings and errors. `results/ocr_baseline.json` is the pre-enhancement capture evaluated from its saved analysis, not rerun through the new parser; old attempt counts omitted panel retries and cannot be compared directly. These development examples are a small convenience set, not a held-out or representative accuracy study. A model which improves synthetic CER can still worsen field extraction on real packaging.

`--python-memory` optionally measures Python traced memory only; it excludes native OpenCV memory and the Tesseract subprocess. Reported OCR time includes process/model-loading overhead. Isolated loading time and subprocess peak RAM are not measured. End-to-end benchmark time includes preprocessing and analysis, excluding upload and history persistence.

## Known limits

The completed [measurement and browser report](../results/ocr_summary.md) records all final numbers, regressions and verification. On this development set the installed full pipeline recovered 45/78 verified nutrient fields versus 38/78 in the saved baseline. Best lowered synthetic CER but reduced field correctness and increased latency; installed remains the default. Controlled comparisons, matrix and runtime reports are separate to avoid confusing recognition with extraction.

Curved shiny bottles, folded pouches, clipped columns, small low-resolution labels and uncommon layouts can still produce insufficient data or miss allergens. The model name, vocabulary, confidence and repeated recognition cannot establish that a reading is correct. Real images with no reliable nutrition remain unscored; an ingredient-only image is not assigned a healthy score. Existing reports reopen from stored evidence, and new recognition settings apply to fresh scans. The source, score and allergen disclaimers remain in place.

Printed serving rounding can also straddle a screening boundary when the explicit per-100 quantity is unreadable. The cereal example and checked ingredient regressions are documented in the report and review queue; this OCR phase does not silently change the scoring methodology to conceal them.

## Files in this enhancement

- Runtime: `config.py`, `ocr.py`, `preprocess.py`, `nutrition.py`, `parser.py`, `app.py`, and the OCR-evidence wording in `templates/result.html`.
- Configuration/data: `.gitignore`, `data/ocr/models.json`, `data/ocr/food_words.txt`, `data/ocr/food_patterns.txt`.
- Evaluation: `evaluate.py`, `scripts/install_ocr_models.py`, `scripts/benchmark_ocr.py`, `tests/ocr_real_labels.json`, `results/evaluation.csv`, `results/evaluation.md`, and the `results/ocr_*` reports/JSON sidecars.
- Tests: `tests/test_ocr.py`, `tests/test_ocr_configuration.py`, `tests/test_preprocess.py`, `tests/test_nutrition_layout.py`, `tests/test_parser.py`, `tests/test_evaluate.py`.
- Notes: `README.md`, `docs/OCR.md`, `docs/ARCHITECTURE.md`, `docs/TEST_PLAN.md`, `docs/MEMORY.md`, append-only `docs/DECISIONS.md`, `TASKS.md`, `DATA_REVIEW.md`.

The working tree already contained earlier scoring/redesign changes and unrelated untracked files before this task. They were preserved. The reviewed implementation was subsequently published on `codex/tesseract-ocr-enhancement`, based on `c584e16`; it was not merged into the original branch.

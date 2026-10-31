# NutriScan

NutriScan is a local Flask prototype that reads an English JPG or PNG food label, decodes configured additive codes, flags ingredient keywords, checks selected allergen groups, and reports unit-aware nutrient statuses with an explainable screening score. Processing stays on this computer: there is no account, cloud service, machine-learning model, or external runtime asset.

## Requirements

- Python 3.10 or later (the pinned environment was installed and checked with Python 3.11.9).
- Tesseract OCR 5 with the English (`eng`) language data.
- Windows, macOS, or a Linux distribution with a package manager.

OpenCV, NumPy, Pillow, Flask, pytesseract, and pytest are installed from the pinned `requirements.txt`. Tesseract itself is a separate system program.

## Install

### Windows PowerShell

Install Tesseract 5 and English language data from the [UB Mannheim Windows installer](https://github.com/UB-Mannheim/tesseract/wiki). If `winget` is available, the package can also be installed with:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

From the project folder, create the Python environment and install the pinned packages:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The default Tesseract path in `config.py` is `C:\Program Files\Tesseract-OCR\tesseract.exe`. If your install uses another location, edit `TESSERACT_CMD` in `config.py`, or set the `TESSERACT_CMD` environment variable to the executable path before launching the app.

### macOS

Install Tesseract 5 and English data with [Homebrew](https://formulae.brew.sh/formula/tesseract):

```sh
brew install tesseract
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Homebrew normally exposes Tesseract as `tesseract` on `PATH`. If NutriScan cannot find it, set its absolute path in `config.py` (`/opt/homebrew/bin/tesseract` on many Apple Silicon systems or `/usr/local/bin/tesseract` on many Intel systems), or export `TESSERACT_CMD` to that path.

### Linux (Debian or Ubuntu)

Install Tesseract 5 and English language data, then set up the environment:

```sh
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The executable is commonly `/usr/bin/tesseract`. If it is not found automatically, set `TESSERACT_CMD` in `config.py` or export that environment variable before starting NutriScan.

## Run

On Windows:

```powershell
.\.venv\Scripts\python.exe app.py
```

On macOS or Linux, with the virtual environment activated:

```sh
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The server binds only to the local computer. Use **Try a sample label** to run the bundled image through upload, OCR, parsing, matching, scoring, and local history. You can also upload a label photo (JPG or PNG, up to 5 MB). The mobile file picker can use the device camera when the browser supports it.

History and both image versions are kept locally so saved results can be reopened without running OCR again. NutriScan does not automatically delete scans. To clear all local scan data, stop the server, replace `data/scan_history.json` with an empty JSON array (`[]`), and remove the scan image files from `uploads/` and `uploads/processed/`. Keep the `.gitkeep` files if you use Git.

## Validate, test, and evaluate

Run these from the project root:

```sh
python scripts/validate_data.py
python -m pytest -q
python scripts/make_sample_labels.py
python evaluate.py
```

On Windows, use `.\.venv\Scripts\python.exe` in place of `python` if the virtual environment is not activated. The generator writes five synthetic image categories and JSON ground truth under `tests/`. Evaluation runs each category with preprocessing off and on and writes `results/evaluation.md` plus `results/evaluation.csv`. The generated labels are useful for repeatable regression checks; they are not real product labels and cannot establish performance on retail packaging.

## Assumptions

- The 180 additive code/name records use Codex INS nomenclature for identity only. A Codex INS entry is not evidence that an additive is approved for a particular food or safe at any particular dose. See [Codex CXG 36-1989](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%3A%2F%2Fworkspace.fao.org%2Fsites%2Fcodex%2FStandards%2FCXG+36-1989%2FCXG_036e.pdf) and the [FSSAI product standards](https://fssai.gov.in/standards/product-standards) for the source boundary.
- Provisional additive risk labels, ingredient flags, keyword expansions, and all numeric nutrient screening cutoffs are project assumptions pending review against applicable Indian standards. Unsupported claims use a conservative neutral description. The complete 300-record review queue is in [DATA_REVIEW.md](DATA_REVIEW.md).
- All numeric nutrient screening cutoffs and score weights live in `config.py`. They are prototype screening rules, not official dietary limits. Salt-to-sodium conversion, when needed, is explicitly labelled as an estimate of about 40%.
- Allergen groups are informed by the FSSAI labelling compendium's allergen declaration groups; expanded keyword variants and keyword-only matching remain assumptions. See the [FSSAI labelling and display compendium](https://fssai.gov.in/upload/uploadfiles/files/Compendium_Labelling_Display_23_09_2021.pdf). A missing keyword match does not establish that a product is allergen-safe.
- The synthetic fixture set uses one English label layout. Evaluation tolerance is configured centrally in `config.py` and is not an official measurement standard.
- Local scan history has no automatic retention limit. Users control cleanup using the steps above.

## Known limitations

- OCR and keyword matching can miss text due to glare, blur, folds, curvature, small print, unsupported languages, or OCR errors. Review the raw OCR text and original/processed comparison.
- The knowledge base is intentionally reviewable and is not a comprehensive or legally authoritative list. Some of its identity, risk, ingredient, and allergen interpretations are unverified.
- The score is a configured heuristic. It does not account for serving frequency, ingredient quantity, a person's health needs, or the overall diet. Allergen alerts do not affect the score and remain visible separately.
- Nutrition status is produced only when the extracted unit and basis can be compared with the configured per-100-g screen. Values per serving are converted only when a serving size is stated clearly; per-100-ml remains incomparable to per-100-g thresholds.
- History is a single-user local JSON file. It is not designed for concurrent multi-process serving or recovery from external disk failure.
- Synthetic evaluation fixtures are not a representative real-photo test set.

## Local assets

The bundled Source Serif 4 font is served from `static/fonts/` so the interface does not rely on a font CDN. It is distributed under the SIL Open Font License 1.1; the license is included as `static/fonts/OFL.txt`. The font source and license are available in the [Adobe Source Serif repository](https://github.com/adobe-fonts/source-serif).

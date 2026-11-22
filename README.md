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

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The server binds only to the local computer. Use **Try a sample label** to run the bundled image through upload, OCR, parsing, matching, scoring, and local history. You can also upload a label photo (JPG or PNG, up to 5 MB). On phones, the file picker lets you select a saved photo and may also offer a camera option, depending on the browser.

## Access NutriScan from a Mobile Device

LAN access is optional. Use it only on a trusted private Wi-Fi network. NutriScan has no login because it is a local, single-user academic prototype; while LAN mode is running, other devices on that network may be able to use it and view locally stored scan results.

On Windows:

1. Connect the laptop and phone to the same Wi-Fi network.
2. Open **Command Prompt** on the laptop.
3. Execute:

   ```text
   ipconfig
   ```

4. Under **Wireless LAN adapter Wi-Fi**, locate the **IPv4 Address**. Use the laptop's actual address from that section.
5. In the NutriScan project folder, start the app in LAN mode:

   ```text
   python app.py --lan
   ```

   The terminal prints a warning that LAN mode allows other devices on the network to access NutriScan. Flask debug mode remains disabled.
6. Open Chrome on the phone and navigate to `http://LAPTOP_IPV4_ADDRESS:5000`, replacing the placeholder with the laptop's actual IPv4 address.

For example only, if `ipconfig` reports `192.168.1.105` for the laptop, open `http://192.168.1.105:5000` on the phone. This is an example address, not your actual IP. The phone must use the laptop's actual IPv4 address; do not use `127.0.0.1` or `0.0.0.0` on the phone.

Both devices must remain on the same Wi-Fi network. Guest Wi-Fi networks may isolate connected devices, and VPNs can interfere with local network access. The laptop must remain powered on and the Flask terminal must remain running while you use the app.

### Optional Windows Firewall rule

If Windows Firewall blocks the phone's connection, an administrator can open PowerShell and add this narrowly scoped inbound rule:

```powershell
Get-NetConnectionProfile
```
```powershell
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private
```
```powershell

New-NetFirewallRule -DisplayName "NutriScan LAN" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
```

PowerShell may need administrator privileges. The rule applies only to the **Private** network profile. Remove it when LAN access is no longer required:

```powershell
Remove-NetFirewallRule -DisplayName "NutriScan LAN"
```

Do not disable Windows Firewall. NutriScan never changes firewall settings automatically. Do not configure router port forwarding, public internet exposure, tunnels, or cloud hosting for this prototype.

History and both image versions are kept locally so saved results can be reopened without running OCR again. NutriScan does not automatically delete scans. To clear all local scan data, stop the server, replace `data/scan_history.json` with an empty JSON array (`[]`), and remove the scan image files from `uploads/` and `uploads/processed/`. Keep the `.gitkeep` files if you use Git.

## Validate, test, and evaluate

For optional `tessdata_best`/`tessdata_fast` packs, project-local model selection, food vocabulary, OCR retry diagnostics and reproducible model/preprocessing benchmarks, see [Tesseract configuration and evaluation](docs/OCR.md). The default uses the installed English pack with LSTM OEM 1 and falls back to it if an optional pack is unavailable. Model binaries stay outside Git and the system installation is unchanged.

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
- Provisional additive risk labels, ingredient flags, keyword expansions, and legacy trans-fat bins remain project assumptions. Solid/liquid concentration categories use the cited UK front-of-pack guidance; added sugar uses FDA per-serving Daily Value interpretation. These are screening references, not a claim of Indian regulatory compliance. Original knowledge-record source notes remain in [DATA_REVIEW.md](DATA_REVIEW.md).
- All numeric nutrient screening cutoffs and score weights live in `config.py`. They are prototype screening rules, not official dietary limits. Salt-to-sodium conversion, when needed, is explicitly labelled as an estimate of about 40%.
- Allergen groups are informed by the FSSAI labelling compendium's allergen declaration groups; expanded keyword variants and keyword-only matching remain assumptions. See the [FSSAI labelling and display compendium](https://fssai.gov.in/upload/uploadfiles/files/Compendium_Labelling_Display_23_09_2021.pdf). A missing keyword match does not establish that a product is allergen-safe.
- The synthetic fixture set uses one English label layout. Evaluation tolerance is configured centrally in `config.py` and is not an official measurement standard.
- Local scan history has no automatic retention limit. Users control cleanup using the steps above.

## Known limitations

Results distinguish **Sufficient**, **Provisional**, **Ingredient-only**, and **Insufficient data**. A nutritional assessment needs a majority of core fields or a verified nutritional concern. Empty/unreadable nutrition and a lone low reading cannot generate a nutritional score of 100. Known additive/ingredient matches can instead support a clearly labelled ingredient-only score, with nutrition explicitly unassessed. Reliable partial readings remain usable and are labelled provisional with coverage and confidence. Four verified low fields may produce a provisional 100 at 80% coverage; that score describes the assessed readings only. The report lists missing/unverified information and every applied contribution. Older reports are reviewed from their stored OCR without changing history files. See [the current scoring audit and coverage policy](docs/SCORING.md).

- OCR and keyword matching can miss text due to glare, blur, folds, curvature, small print, unsupported languages, or OCR errors. Review the raw OCR text and original/processed comparison.
- The knowledge base is intentionally reviewable and is not a comprehensive or legally authoritative list. Some of its identity, risk, ingredient, and allergen interpretations are unverified.
- The score is a configured heuristic. It does not account for serving frequency, ingredient quantity, a person's health needs, or the overall diet. Allergen alerts do not affect the score and remain visible separately.
- Values per serving are normalized only with a stated serving mass or volume. Per-100-ml readings use separate liquid thresholds; no g/ml density is guessed. FDA added-sugar screening uses its stated serving basis. Total and added sugar share one deduction rather than counting the same sugar twice.
- History is a single-user local JSON file. It is not designed for concurrent multi-process serving or recovery from external disk failure.
- Synthetic evaluation fixtures are not a representative real-photo test set.

## Local assets

The bundled Source Serif 4 font is served from `static/fonts/` so the interface does not rely on a font CDN. It is distributed under the SIL Open Font License 1.1; the license is included as `static/fonts/OFL.txt`. The font source and license are available in the [Adobe Source Serif repository](https://github.com/adobe-fonts/source-serif).

### OCR recovery and difficult labels

Incomplete scans now try additional enlarged grayscale block/single-column readings with a border; each Tesseract call has a 15-second timeout. Parsing supports serving amounts immediately before their heading and English nutrient names beside translated labels. Recognition confidence is a heuristic, not a guarantee. Weights and screening thresholds are unchanged.

For a difficult package, photograph one flat nutrition panel closely, keeping its serving-size and per-100/serving heading visible. Avoid glare and include the ingredient/allergen text where possible. For tables that also list prepared food (for example cereal with milk), use a clear product-only column with its heading: unresolved columns are excluded rather than mixed. Missing/unreadable values remain unverified. Restart the running Flask process after updating the code and submit a fresh scan to use the new OCR; reopening an older report only reviews the OCR evidence already stored.

### Native OCR and limited score scope

OCR reads native grayscale up to a 4500 px long side. The comparison preview and panel detector use their own 1800 px display bound. Retry size is based on observed word height (target 30 px), with grayscale and illumination-flattened variants. These improve the available choices but do not guarantee better readings on every image.

If nutrition is insufficient but known additive/ingredient flags were matched, an Ingredient-only score describes only those matches. It does not assess nutrition. No evidence still means no score. Provisional results show based on N of 5 nutrients; below 60% coverage the band is capped at Moderate while the numeric ledger is unchanged. Ingredient-only is also capped at Moderate. Review the stated scope, actual fields and missing information.

For reproducible local OCR evaluation, use scripts/benchmark_ocr.py with the manifest and commands in docs/TEST_PLAN.md. The current ten-package-photo set shows no aggregate verified-field gain; results/ocr_after_v6.md records both gains and regressions. Restart the Flask process and make fresh scans to use the new OCR.

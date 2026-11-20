# NutriScan synthetic-label evaluation

Generated from 5 bundled synthetic label categories, each run with preprocessing off and on. These fixtures are not real retail packaging and do not establish real-world OCR or food-safety performance.

The same five ground-truth files are used for both modes. Ingredient recall uses normalized ingredient-token equality. Additive precision/recall count normalized INS identities reported from an explicit code or a known additive name; allergen precision/recall count detected groups. Nutrition accuracy requires the expected nutrient, unit, basis, and a value within the absolute/relative tolerance configured in `config.py`. Processing time covers preprocessing, OCR, parsing, and lookups; startup and disk persistence are excluded.
The current runtime starts from original grayscale in both off/on modes, and counts only verified nutrition readings. This legacy comparison therefore does not isolate the effect of a single preprocessing image. Use scripts/benchmark_ocr.py --mode matrix for controlled image-variant and PSM comparisons.

## Aggregate results

| Preprocessing | Ingredient recall | Additive precision | Additive recall | Nutrition accuracy | Allergen precision | Allergen recall | Mean / median seconds | Failed scans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Off | 100.0% (40/40) | 100.0% | 100.0% (TP 10, FP 0, FN 0) | 87.5% (35/40) | 100.0% | 100.0% (TP 20, FP 0, FN 0) | 3.447 / 2.012 | 0/5 |
| On | 100.0% (40/40) | 100.0% | 100.0% (TP 10, FP 0, FN 0) | 87.5% (35/40) | 100.0% | 100.0% (TP 20, FP 0, FN 0) | 1.890 / 1.867 | 0/5 |

## Per-image detail

| Mode | Image | Ingredient recall | Additive P / R | Nutrition accuracy | Allergen P / R | Seconds | Error |
|---|---|---:|---:|---:|---:|---:|---|
| Off | clear_flat.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 2.133 | — |
| Off | glare_like.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 1.279 | — |
| Off | low_contrast.png | 100.0% (8/8) | 100.0% / 100.0% | 87.5% (7/8) | 100.0% / 100.0% | 1.610 | — |
| Off | noisy.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 2.012 | — |
| Off | slightly_tilted.png | 100.0% (8/8) | 100.0% / 100.0% | 50.0% (4/8) | 100.0% / 100.0% | 10.201 | — |
| On | clear_flat.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 2.743 | — |
| On | glare_like.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 1.236 | — |
| On | low_contrast.png | 100.0% (8/8) | 100.0% / 100.0% | 87.5% (7/8) | 100.0% / 100.0% | 1.356 | — |
| On | noisy.png | 100.0% (8/8) | 100.0% / 100.0% | 100.0% (8/8) | 100.0% / 100.0% | 1.867 | — |
| On | slightly_tilted.png | 100.0% (8/8) | 100.0% / 100.0% | 50.0% (4/8) | 100.0% / 100.0% | 2.248 | — |

## Interpretation limits

- Synthetic text is cleanly typeset and does not model package curvature, camera variation, multilingual labels, regulatory edge cases, or the variety of commercial packaging.
- The fixture set is intentionally small. Results are descriptive regression checks, not a statistically representative benchmark.
- Failed OCR or preprocessing runs remain in the denominator as misses and are listed in the table; no threshold was adjusted to improve these results.
- The score, risk categories, allergen keyword expansion, and nutrition screening values remain project assumptions documented in `DATA_REVIEW.md`.

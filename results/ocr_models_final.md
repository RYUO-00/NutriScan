# Tesseract OCR benchmark

Mode control; OEM 1, English; repetitions 2. Control uses original grayscale, PSM 6, no vocabulary for all models.

CER/WER apply only to the five synthetic images with complete transcripts. Real-photo metrics use only manually checked visible fields. Parsed accuracy excludes OCR confidence admission; verified accuracy applies the full application pipeline. Both require correct nutrient, value, unit and basis (1% relative or 0.05 absolute tolerance). Missing/unverified readings are misses, never zero. Ingredient/additive/allergen metrics are recall, with false positives reported per image when references are exhaustive. The small development set is not a held-out or representative performance claim.

| Profile | CER | WER | Parsed fields | Verified fields | Wrong verified | Ingredients | Allergens | Serving | OCR s | Full s | Attempts | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 3.5% | 24.8% | 46.2% | 30.8% | 0 | 63.2% | 80.6% | 63.6% | 0.764 | 0.860 | 1.00 | 0 |
| tessdata_best | 2.4% | 20.5% | 42.3% | 28.2% | 4 | 67.6% | 77.8% | 63.6% | 2.338 | 2.446 | 1.00 | 0 |
| tessdata_fast | 3.5% | 24.8% | 46.2% | 30.8% | 0 | 63.2% | 80.6% | 63.6% | 0.845 | 0.937 | 1.00 | 0 |

## Per-image evidence

| Profile | Image | Parsed / verified fields | Wrong verified | OCR s | Score / status | Error |
|---|---|---:|---:|---:|---|---|
| installed | clear_flat.png | 8 / 5 of 8 | 0 | 1.150 | 82 / provisional |  |
| installed | glare_like.png | 8 / 5 of 8 | 0 | 0.874 | 82 / provisional |  |
| installed | low_contrast.png | 8 / 5 of 8 | 0 | 0.583 | 82 / provisional |  |
| installed | noisy.png | 7 / 6 of 8 | 0 | 1.115 | 82 / provisional |  |
| installed | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.416 | 89 / provisional |  |
| installed | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.535 | None / insufficient |  |
| installed | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.214 | None / insufficient |  |
| installed | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.912 | None / insufficient |  |
| installed | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.232 | None / insufficient |  |
| installed | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.998 | None / insufficient |  |
| installed | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 0.926 | 93 / provisional |  |
| installed | images (3).jpg | 2 / 0 of 4 | 0 | 0.714 | None / insufficient |  |
| installed | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.452 | None / insufficient |  |
| installed | clear_flat.png | 8 / 5 of 8 | 0 | 0.453 | 82 / provisional |  |
| installed | glare_like.png | 8 / 5 of 8 | 0 | 0.452 | 82 / provisional |  |
| installed | low_contrast.png | 8 / 5 of 8 | 0 | 0.516 | 82 / provisional |  |
| installed | noisy.png | 7 / 6 of 8 | 0 | 0.671 | 82 / provisional |  |
| installed | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.438 | 89 / provisional |  |
| installed | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.595 | None / insufficient |  |
| installed | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.575 | None / insufficient |  |
| installed | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.310 | None / insufficient |  |
| installed | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.894 | None / insufficient |  |
| installed | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.827 | None / insufficient |  |
| installed | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 1.007 | 93 / provisional |  |
| installed | images (3).jpg | 2 / 0 of 4 | 0 | 0.566 | None / insufficient |  |
| installed | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.436 | None / insufficient |  |
| tessdata_best | clear_flat.png | 8 / 5 of 8 | 0 | 1.334 | 75 / provisional |  |
| tessdata_best | glare_like.png | 8 / 5 of 8 | 0 | 1.446 | 75 / provisional |  |
| tessdata_best | low_contrast.png | 8 / 6 of 8 | 0 | 1.426 | 68 / provisional |  |
| tessdata_best | noisy.png | 8 / 5 of 8 | 0 | 1.445 | 75 / provisional |  |
| tessdata_best | slightly_tilted.png | 0 / 0 of 8 | 0 | 1.330 | None / insufficient |  |
| tessdata_best | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.243 | None / insufficient |  |
| tessdata_best | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.102 | None / insufficient |  |
| tessdata_best | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 1 | 2.746 | None / insufficient |  |
| tessdata_best | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 2.413 | None / insufficient |  |
| tessdata_best | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 2.376 | None / insufficient |  |
| tessdata_best | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 1 | 2.576 | 93 / provisional |  |
| tessdata_best | images (3).jpg | 0 / 0 of 4 | 0 | 2.167 | None / insufficient |  |
| tessdata_best | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 1.162 | None / insufficient |  |
| tessdata_best | clear_flat.png | 8 / 5 of 8 | 0 | 2.536 | 75 / provisional |  |
| tessdata_best | glare_like.png | 8 / 5 of 8 | 0 | 1.370 | 75 / provisional |  |
| tessdata_best | low_contrast.png | 8 / 6 of 8 | 0 | 1.244 | 68 / provisional |  |
| tessdata_best | noisy.png | 8 / 5 of 8 | 0 | 2.012 | 75 / provisional |  |
| tessdata_best | slightly_tilted.png | 0 / 0 of 8 | 0 | 1.175 | None / insufficient |  |
| tessdata_best | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.424 | None / insufficient |  |
| tessdata_best | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.772 | None / insufficient |  |
| tessdata_best | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 1 | 2.446 | None / insufficient |  |
| tessdata_best | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 4.028 | None / insufficient |  |
| tessdata_best | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 5.017 | None / insufficient |  |
| tessdata_best | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 1 | 6.659 | 93 / provisional |  |
| tessdata_best | images (3).jpg | 0 / 0 of 4 | 0 | 6.478 | None / insufficient |  |
| tessdata_best | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 1.859 | None / insufficient |  |
| tessdata_fast | clear_flat.png | 8 / 5 of 8 | 0 | 0.706 | 82 / provisional |  |
| tessdata_fast | glare_like.png | 8 / 5 of 8 | 0 | 0.430 | 82 / provisional |  |
| tessdata_fast | low_contrast.png | 8 / 5 of 8 | 0 | 0.360 | 82 / provisional |  |
| tessdata_fast | noisy.png | 7 / 6 of 8 | 0 | 0.472 | 82 / provisional |  |
| tessdata_fast | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.407 | 89 / provisional |  |
| tessdata_fast | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.821 | None / insufficient |  |
| tessdata_fast | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.795 | None / insufficient |  |
| tessdata_fast | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.640 | None / insufficient |  |
| tessdata_fast | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.314 | None / insufficient |  |
| tessdata_fast | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 2.672 | None / insufficient |  |
| tessdata_fast | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 1.969 | 93 / provisional |  |
| tessdata_fast | images (3).jpg | 2 / 0 of 4 | 0 | 1.169 | None / insufficient |  |
| tessdata_fast | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.535 | None / insufficient |  |
| tessdata_fast | clear_flat.png | 8 / 5 of 8 | 0 | 0.502 | 82 / provisional |  |
| tessdata_fast | glare_like.png | 8 / 5 of 8 | 0 | 0.579 | 82 / provisional |  |
| tessdata_fast | low_contrast.png | 8 / 5 of 8 | 0 | 0.986 | 82 / provisional |  |
| tessdata_fast | noisy.png | 7 / 6 of 8 | 0 | 0.714 | 82 / provisional |  |
| tessdata_fast | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.377 | 89 / provisional |  |
| tessdata_fast | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.632 | None / insufficient |  |
| tessdata_fast | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.603 | None / insufficient |  |
| tessdata_fast | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.062 | None / insufficient |  |
| tessdata_fast | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.730 | None / insufficient |  |
| tessdata_fast | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.844 | None / insufficient |  |
| tessdata_fast | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 0.738 | 93 / provisional |  |
| tessdata_fast | images (3).jpg | 2 / 0 of 4 | 0 | 0.487 | None / insufficient |  |
| tessdata_fast | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.413 | None / insufficient |  |

Each pytesseract call launches a Tesseract subprocess and includes model loading, OCR, TSV parsing and process overhead. Isolated model-loading time and Tesseract subprocess peak RAM are not measured. Optional Python peak memory excludes OpenCV native allocations and the OCR child process. Model identity/file size and input hashes are in the JSON sidecar. Single-pass tests are controlled recognition comparisons, not the bounded runtime retry policy. Pipeline times cover preprocessing and analysis but exclude upload/storage. Timings are descriptive local measurements and can vary with CPU load.

## Numeric-only region probe

| Model | Restriction | CER | WER | Seconds |
|---|---|---:|---:|---:|
| installed | none | 5.3% | 33.3% | 0.166 |
| installed | numeric/units | 26.3% | 100.0% | 0.230 |
| tessdata_best | none | 36.8% | 100.0% | 0.257 |
| tessdata_best | numeric/units | 36.8% | 100.0% | 0.269 |
| tessdata_fast | none | 5.3% | 33.3% | 0.191 |
| tessdata_fast | numeric/units | 26.3% | 100.0% | 0.152 |
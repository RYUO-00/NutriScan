# Tesseract OCR benchmark

Mode pipeline; OEM 1, English; repetitions 1. Control uses original grayscale, PSM 6, no vocabulary for all models.

CER/WER apply only to the five synthetic images with complete transcripts. Real-photo metrics use only manually checked visible fields. Parsed accuracy excludes OCR confidence admission; verified accuracy applies the full application pipeline. Both require correct nutrient, value, unit and basis (1% relative or 0.05 absolute tolerance). Missing/unverified readings are misses, never zero. Ingredient/additive/allergen metrics are recall, with false positives reported per image when references are exhaustive. The small development set is not a held-out or representative performance claim.

| Profile | CER | WER | Parsed fields | Verified fields | Wrong verified | Ingredients | Allergens | Serving | OCR s | Full s | Attempts | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 3.0% | 22.2% | 65.4% | 57.7% | 1 | 76.5% | 86.1% | 72.7% | 5.203 | 5.415 | 3.62 | 0 |
| tessdata_best | 2.0% | 18.2% | 55.1% | 43.6% | 1 | 77.9% | 86.1% | 72.7% | 10.112 | 10.293 | 3.15 | 0 |
| tessdata_fast | 3.0% | 22.2% | 65.4% | 57.7% | 1 | 76.5% | 86.1% | 72.7% | 4.859 | 5.051 | 3.62 | 0 |

## Per-image evidence

| Profile | Image | Parsed / verified fields | Wrong verified | OCR s | Score / status | Error |
|---|---|---:|---:|---:|---|---|
| installed | clear_flat.png | 8 / 8 of 8 | 0 | 2.215 | 68 / sufficient |  |
| installed | glare_like.png | 8 / 8 of 8 | 0 | 1.891 | 68 / sufficient |  |
| installed | low_contrast.png | 8 / 7 of 8 | 0 | 2.317 | 75 / provisional |  |
| installed | noisy.png | 8 / 8 of 8 | 0 | 2.343 | 68 / sufficient |  |
| installed | slightly_tilted.png | 8 / 4 of 8 | 0 | 2.415 | 82 / provisional |  |
| installed | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 2.257 | None / insufficient |  |
| installed | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 2.207 | None / insufficient |  |
| installed | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 2.907 | None / insufficient |  |
| installed | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 12.184 | None / insufficient |  |
| installed | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 4 / 3 of 7 | 0 | 7.450 | 90 / provisional |  |
| installed | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 3 / 4 of 6 | 1 | 12.761 | 71 / provisional |  |
| installed | images (3).jpg | 4 / 3 of 4 | 0 | 13.379 | 70 / provisional |  |
| installed | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 3.311 | None / insufficient |  |
| tessdata_best | clear_flat.png | 8 / 6 of 8 | 0 | 6.765 | 68 / sufficient |  |
| tessdata_best | glare_like.png | 8 / 6 of 8 | 0 | 9.537 | 68 / sufficient |  |
| tessdata_best | low_contrast.png | 8 / 7 of 8 | 0 | 3.516 | 68 / sufficient |  |
| tessdata_best | noisy.png | 8 / 6 of 8 | 0 | 3.537 | 68 / sufficient |  |
| tessdata_best | slightly_tilted.png | 7 / 6 of 8 | 0 | 11.591 | 82 / provisional |  |
| tessdata_best | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 5.929 | None / insufficient |  |
| tessdata_best | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 8.514 | None / insufficient |  |
| tessdata_best | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 1 | 10.579 | None / insufficient |  |
| tessdata_best | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 3.975 | None / insufficient |  |
| tessdata_best | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 2 of 7 | 0 | 31.876 | None / insufficient |  |
| tessdata_best | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 15.700 | 93 / provisional |  |
| tessdata_best | images (3).jpg | 2 / 0 of 4 | 0 | 13.319 | None / insufficient |  |
| tessdata_best | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 6.617 | None / insufficient |  |
| tessdata_fast | clear_flat.png | 8 / 8 of 8 | 0 | 2.751 | 68 / sufficient |  |
| tessdata_fast | glare_like.png | 8 / 8 of 8 | 0 | 2.745 | 68 / sufficient |  |
| tessdata_fast | low_contrast.png | 8 / 7 of 8 | 0 | 2.605 | 75 / provisional |  |
| tessdata_fast | noisy.png | 8 / 8 of 8 | 0 | 3.152 | 68 / sufficient |  |
| tessdata_fast | slightly_tilted.png | 8 / 4 of 8 | 0 | 2.641 | 82 / provisional |  |
| tessdata_fast | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 4.326 | None / insufficient |  |
| tessdata_fast | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 3.048 | None / insufficient |  |
| tessdata_fast | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 2.713 | None / insufficient |  |
| tessdata_fast | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 8.920 | None / insufficient |  |
| tessdata_fast | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 4 / 3 of 7 | 0 | 6.738 | 90 / provisional |  |
| tessdata_fast | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 3 / 4 of 6 | 1 | 8.558 | 71 / provisional |  |
| tessdata_fast | images (3).jpg | 4 / 3 of 4 | 0 | 10.580 | 70 / provisional |  |
| tessdata_fast | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 4.393 | None / insufficient |  |

Each pytesseract call launches a Tesseract subprocess and includes model loading, OCR, TSV parsing and process overhead. Isolated model-loading time and Tesseract subprocess peak RAM are not measured. Optional Python peak memory excludes OpenCV native allocations and the OCR child process. Model identity/file size and input hashes are in the JSON sidecar. Single-pass tests are controlled recognition comparisons, not the bounded runtime retry policy. Pipeline times cover preprocessing and analysis but exclude upload/storage. Timings are descriptive local measurements and can vary with CPU load.

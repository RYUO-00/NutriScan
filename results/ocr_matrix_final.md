# Tesseract OCR benchmark

Mode matrix; OEM 1, English; repetitions 1. Control uses original grayscale, PSM 6, no vocabulary for all models.

CER/WER apply only to the five synthetic images with complete transcripts. Real-photo metrics use only manually checked visible fields. Parsed accuracy excludes OCR confidence admission; verified accuracy applies the full application pipeline. Both require correct nutrient, value, unit and basis (1% relative or 0.05 absolute tolerance). Missing/unverified readings are misses, never zero. Ingredient/additive/allergen metrics are recall, with false positives reported per image when references are exhaustive. The small development set is not a held-out or representative performance claim.

| Profile | CER | WER | Parsed fields | Verified fields | Wrong verified | Ingredients | Allergens | Serving | OCR s | Full s | Attempts | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed/gray/psm6 | 3.5% | 24.8% | 46.2% | 30.8% | 0 | 63.2% | 80.6% | 63.6% | 0.632 | 0.709 | 1.00 | 0 |
| installed/gray/psm11 | 7.9% | 22.8% | 43.6% | 29.5% | 0 | 60.3% | 83.3% | 45.5% | 0.926 | 1.035 | 1.00 | 0 |
| installed/gray/psm3 | 3.5% | 24.8% | 42.3% | 29.5% | 0 | 64.7% | 80.6% | 45.5% | 0.544 | 0.622 | 1.00 | 0 |
| installed/contrast/psm6 | 3.6% | 25.5% | 46.2% | 29.5% | 0 | 66.2% | 72.2% | 45.5% | 0.853 | 0.932 | 1.00 | 0 |
| installed/contrast/psm11 | 9.2% | 25.2% | 47.4% | 28.2% | 2 | 64.7% | 72.2% | 63.6% | 0.707 | 0.803 | 1.00 | 0 |
| installed/contrast/psm3 | 3.5% | 25.0% | 44.9% | 28.2% | 0 | 64.7% | 72.2% | 54.5% | 0.573 | 0.655 | 1.00 | 0 |
| installed/legacy/psm6 | 21.7% | 65.5% | 37.2% | 15.4% | 1 | 69.1% | 75.0% | 54.5% | 0.845 | 0.935 | 1.00 | 0 |
| installed/legacy/psm11 | 5.8% | 32.0% | 35.9% | 21.8% | 0 | 57.4% | 72.2% | 45.5% | 0.579 | 0.650 | 1.00 | 0 |
| installed/legacy/psm3 | 10.9% | 43.8% | 42.3% | 19.2% | 0 | 61.8% | 72.2% | 45.5% | 0.398 | 0.464 | 1.00 | 0 |
| installed/otsu/psm6 | 3.2% | 23.8% | 46.2% | 28.2% | 0 | 66.2% | 77.8% | 54.5% | 0.640 | 0.748 | 1.00 | 0 |
| installed/otsu/psm11 | 8.0% | 23.5% | 41.0% | 28.2% | 4 | 60.3% | 80.6% | 45.5% | 0.717 | 0.804 | 1.00 | 0 |
| installed/otsu/psm3 | 3.0% | 23.5% | 44.9% | 28.2% | 0 | 69.1% | 77.8% | 45.5% | 0.704 | 0.805 | 1.00 | 0 |
| installed/adaptive/psm6 | 18.4% | 47.2% | 26.9% | 19.2% | 2 | 55.9% | 75.0% | 45.5% | 1.848 | 1.984 | 1.00 | 0 |
| installed/adaptive/psm11 | 120.6% | 262.5% | 30.8% | 23.1% | 0 | 50.0% | 75.0% | 36.4% | 2.258 | 2.411 | 1.00 | 0 |
| installed/adaptive/psm3 | 21.4% | 40.2% | 29.5% | 21.8% | 2 | 57.4% | 77.8% | 36.4% | 1.115 | 1.237 | 1.00 | 0 |
| installed/deskew/psm6 | 3.8% | 27.5% | 53.8% | 35.9% | 0 | 63.2% | 83.3% | 63.6% | 0.946 | 1.032 | 1.00 | 0 |
| installed/deskew/psm11 | 2.5% | 18.5% | 51.3% | 33.3% | 0 | 64.7% | 86.1% | 54.5% | 0.697 | 0.786 | 1.00 | 0 |
| installed/deskew/psm3 | 3.8% | 27.5% | 50.0% | 34.6% | 0 | 64.7% | 83.3% | 54.5% | 0.551 | 0.626 | 1.00 | 0 |
| installed/deskew_scaled/psm6 | 3.6% | 26.0% | 55.1% | 34.6% | 0 | 75.0% | 80.6% | 63.6% | 1.222 | 1.334 | 1.00 | 0 |
| installed/deskew_scaled/psm11 | 3.4% | 25.5% | 56.4% | 35.9% | 0 | 73.5% | 83.3% | 81.8% | 1.499 | 1.628 | 1.00 | 0 |
| installed/deskew_scaled/psm3 | 3.4% | 26.0% | 56.4% | 33.3% | 0 | 77.9% | 83.3% | 63.6% | 1.825 | 2.025 | 1.00 | 0 |
| installed/gray/psm6/vocabulary | 3.5% | 24.8% | 46.2% | 30.8% | 0 | 63.2% | 80.6% | 63.6% | 0.821 | 0.977 | 1.00 | 0 |

## Per-image evidence

| Profile | Image | Parsed / verified fields | Wrong verified | OCR s | Score / status | Error |
|---|---|---:|---:|---:|---|---|
| installed/gray/psm6 | clear_flat.png | 8 / 5 of 8 | 0 | 0.376 | 82 / provisional |  |
| installed/gray/psm6 | glare_like.png | 8 / 5 of 8 | 0 | 0.445 | 82 / provisional |  |
| installed/gray/psm6 | low_contrast.png | 8 / 5 of 8 | 0 | 0.411 | 82 / provisional |  |
| installed/gray/psm6 | noisy.png | 7 / 6 of 8 | 0 | 0.524 | 82 / provisional |  |
| installed/gray/psm6 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.407 | 89 / provisional |  |
| installed/gray/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.544 | None / insufficient |  |
| installed/gray/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.593 | None / insufficient |  |
| installed/gray/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.146 | None / insufficient |  |
| installed/gray/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.835 | None / insufficient |  |
| installed/gray/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.860 | None / insufficient |  |
| installed/gray/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 0.908 | 93 / provisional |  |
| installed/gray/psm6 | images (3).jpg | 2 / 0 of 4 | 0 | 0.704 | None / insufficient |  |
| installed/gray/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.464 | None / insufficient |  |
| installed/gray/psm11 | clear_flat.png | 8 / 5 of 8 | 0 | 0.900 | 82 / provisional |  |
| installed/gray/psm11 | glare_like.png | 8 / 5 of 8 | 0 | 1.853 | 82 / provisional |  |
| installed/gray/psm11 | low_contrast.png | 8 / 5 of 8 | 0 | 2.118 | 82 / provisional |  |
| installed/gray/psm11 | noisy.png | 8 / 6 of 8 | 0 | 0.580 | 82 / provisional |  |
| installed/gray/psm11 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.504 | 92 / provisional |  |
| installed/gray/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.954 | None / insufficient |  |
| installed/gray/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.572 | None / insufficient |  |
| installed/gray/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.791 | None / insufficient |  |
| installed/gray/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.874 | None / insufficient |  |
| installed/gray/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.969 | None / insufficient |  |
| installed/gray/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.988 | None / insufficient |  |
| installed/gray/psm11 | images (3).jpg | 0 / 0 of 4 | 0 | 0.491 | None / insufficient |  |
| installed/gray/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.442 | None / insufficient |  |
| installed/gray/psm3 | clear_flat.png | 8 / 5 of 8 | 0 | 0.655 | 82 / provisional |  |
| installed/gray/psm3 | glare_like.png | 8 / 5 of 8 | 0 | 0.416 | 82 / provisional |  |
| installed/gray/psm3 | low_contrast.png | 8 / 5 of 8 | 0 | 0.417 | 82 / provisional |  |
| installed/gray/psm3 | noisy.png | 7 / 6 of 8 | 0 | 0.763 | 82 / provisional |  |
| installed/gray/psm3 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.431 | 89 / provisional |  |
| installed/gray/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.375 | None / insufficient |  |
| installed/gray/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.293 | None / insufficient |  |
| installed/gray/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.488 | None / insufficient |  |
| installed/gray/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.782 | None / insufficient |  |
| installed/gray/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.815 | None / insufficient |  |
| installed/gray/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.935 | None / insufficient |  |
| installed/gray/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.387 | None / insufficient |  |
| installed/gray/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.319 | None / insufficient |  |
| installed/contrast/psm6 | clear_flat.png | 8 / 3 of 8 | 0 | 1.309 | 89 / provisional |  |
| installed/contrast/psm6 | glare_like.png | 8 / 5 of 8 | 0 | 2.008 | 82 / provisional |  |
| installed/contrast/psm6 | low_contrast.png | 8 / 4 of 8 | 0 | 1.408 | 89 / provisional |  |
| installed/contrast/psm6 | noisy.png | 8 / 8 of 8 | 0 | 0.440 | 68 / sufficient |  |
| installed/contrast/psm6 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.376 | 89 / provisional |  |
| installed/contrast/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.515 | None / insufficient |  |
| installed/contrast/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.643 | None / insufficient |  |
| installed/contrast/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.918 | None / insufficient |  |
| installed/contrast/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.694 | None / insufficient |  |
| installed/contrast/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 0 of 7 | 0 | 0.987 | None / insufficient |  |
| installed/contrast/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 0.792 | 93 / provisional |  |
| installed/contrast/psm6 | images (3).jpg | 0 / 0 of 4 | 0 | 0.634 | None / insufficient |  |
| installed/contrast/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.360 | None / insufficient |  |
| installed/contrast/psm11 | clear_flat.png | 8 / 4 of 8 | 0 | 0.600 | 89 / provisional |  |
| installed/contrast/psm11 | glare_like.png | 8 / 5 of 8 | 0 | 1.149 | 89 / provisional |  |
| installed/contrast/psm11 | low_contrast.png | 8 / 4 of 8 | 0 | 0.401 | 89 / provisional |  |
| installed/contrast/psm11 | noisy.png | 8 / 7 of 8 | 0 | 0.490 | 75 / provisional |  |
| installed/contrast/psm11 | slightly_tilted.png | 0 / 0 of 8 | 1 | 0.446 | None / insufficient |  |
| installed/contrast/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.890 | None / insufficient |  |
| installed/contrast/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.656 | None / insufficient |  |
| installed/contrast/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.623 | None / insufficient |  |
| installed/contrast/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.681 | None / insufficient |  |
| installed/contrast/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 2 / 2 of 7 | 1 | 1.317 | 90 / provisional |  |
| installed/contrast/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.851 | None / insufficient |  |
| installed/contrast/psm11 | images (3).jpg | 3 / 0 of 4 | 0 | 0.636 | None / insufficient |  |
| installed/contrast/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.447 | None / insufficient |  |
| installed/contrast/psm3 | clear_flat.png | 8 / 3 of 8 | 0 | 0.465 | 89 / provisional |  |
| installed/contrast/psm3 | glare_like.png | 8 / 5 of 8 | 0 | 0.451 | 82 / provisional |  |
| installed/contrast/psm3 | low_contrast.png | 8 / 4 of 8 | 0 | 0.442 | 89 / provisional |  |
| installed/contrast/psm3 | noisy.png | 8 / 8 of 8 | 0 | 0.483 | 68 / sufficient |  |
| installed/contrast/psm3 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.574 | 89 / provisional |  |
| installed/contrast/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.507 | None / insufficient |  |
| installed/contrast/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.524 | None / insufficient |  |
| installed/contrast/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.450 | None / insufficient |  |
| installed/contrast/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.408 | None / insufficient |  |
| installed/contrast/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 0 of 7 | 0 | 0.962 | None / insufficient |  |
| installed/contrast/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.979 | None / insufficient |  |
| installed/contrast/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.770 | None / insufficient |  |
| installed/contrast/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.433 | None / insufficient |  |
| installed/legacy/psm6 | clear_flat.png | 8 / 3 of 8 | 0 | 0.615 | 89 / provisional |  |
| installed/legacy/psm6 | glare_like.png | 8 / 2 of 8 | 0 | 0.547 | 89 / provisional |  |
| installed/legacy/psm6 | low_contrast.png | 7 / 5 of 8 | 0 | 0.773 | 75 / provisional |  |
| installed/legacy/psm6 | noisy.png | 0 / 0 of 8 | 1 | 0.739 | 81 / provisional |  |
| installed/legacy/psm6 | slightly_tilted.png | 6 / 2 of 8 | 0 | 1.404 | None / insufficient |  |
| installed/legacy/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.063 | None / insufficient |  |
| installed/legacy/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.648 | None / insufficient |  |
| installed/legacy/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.484 | None / insufficient |  |
| installed/legacy/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.988 | None / insufficient |  |
| installed/legacy/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.557 | None / insufficient |  |
| installed/legacy/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.505 | None / insufficient |  |
| installed/legacy/psm6 | images (3).jpg | 0 / 0 of 4 | 0 | 0.339 | None / insufficient |  |
| installed/legacy/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.328 | None / insufficient |  |
| installed/legacy/psm11 | clear_flat.png | 7 / 3 of 8 | 0 | 0.467 | 89 / provisional |  |
| installed/legacy/psm11 | glare_like.png | 7 / 3 of 8 | 0 | 0.382 | 89 / provisional |  |
| installed/legacy/psm11 | low_contrast.png | 7 / 6 of 8 | 0 | 0.380 | 68 / sufficient |  |
| installed/legacy/psm11 | noisy.png | 0 / 0 of 8 | 0 | 0.440 | None / insufficient |  |
| installed/legacy/psm11 | slightly_tilted.png | 6 / 4 of 8 | 0 | 0.424 | 89 / provisional |  |
| installed/legacy/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.638 | None / insufficient |  |
| installed/legacy/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.590 | None / insufficient |  |
| installed/legacy/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.934 | None / insufficient |  |
| installed/legacy/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.234 | None / insufficient |  |
| installed/legacy/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 1 of 7 | 0 | 0.508 | None / insufficient |  |
| installed/legacy/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.541 | None / insufficient |  |
| installed/legacy/psm11 | images (3).jpg | 0 / 0 of 4 | 0 | 0.645 | None / insufficient |  |
| installed/legacy/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.344 | None / insufficient |  |
| installed/legacy/psm3 | clear_flat.png | 8 / 3 of 8 | 0 | 0.379 | 89 / provisional |  |
| installed/legacy/psm3 | glare_like.png | 8 / 2 of 8 | 0 | 0.450 | 89 / provisional |  |
| installed/legacy/psm3 | low_contrast.png | 7 / 5 of 8 | 0 | 0.355 | 75 / provisional |  |
| installed/legacy/psm3 | noisy.png | 4 / 3 of 8 | 0 | 0.426 | 92 / provisional |  |
| installed/legacy/psm3 | slightly_tilted.png | 6 / 2 of 8 | 0 | 0.460 | None / insufficient |  |
| installed/legacy/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.411 | None / insufficient |  |
| installed/legacy/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.330 | None / insufficient |  |
| installed/legacy/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.332 | None / insufficient |  |
| installed/legacy/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.472 | None / insufficient |  |
| installed/legacy/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.578 | None / insufficient |  |
| installed/legacy/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.544 | None / insufficient |  |
| installed/legacy/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.207 | None / insufficient |  |
| installed/legacy/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.225 | None / insufficient |  |
| installed/otsu/psm6 | clear_flat.png | 8 / 4 of 8 | 0 | 0.391 | 75 / provisional |  |
| installed/otsu/psm6 | glare_like.png | 8 / 5 of 8 | 0 | 0.378 | 75 / provisional |  |
| installed/otsu/psm6 | low_contrast.png | 7 / 4 of 8 | 0 | 0.440 | 82 / provisional |  |
| installed/otsu/psm6 | noisy.png | 8 / 5 of 8 | 0 | 0.506 | 75 / provisional |  |
| installed/otsu/psm6 | slightly_tilted.png | 4 / 4 of 8 | 0 | 0.401 | 82 / provisional |  |
| installed/otsu/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.062 | None / insufficient |  |
| installed/otsu/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.456 | None / insufficient |  |
| installed/otsu/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.182 | None / insufficient |  |
| installed/otsu/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.916 | None / insufficient |  |
| installed/otsu/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 0 of 7 | 0 | 0.697 | None / insufficient |  |
| installed/otsu/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.742 | None / insufficient |  |
| installed/otsu/psm6 | images (3).jpg | 0 / 0 of 4 | 0 | 0.636 | None / insufficient |  |
| installed/otsu/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.518 | None / insufficient |  |
| installed/otsu/psm11 | clear_flat.png | 8 / 6 of 8 | 0 | 1.023 | 82 / provisional |  |
| installed/otsu/psm11 | glare_like.png | 8 / 6 of 8 | 0 | 0.449 | 82 / provisional |  |
| installed/otsu/psm11 | low_contrast.png | 8 / 4 of 8 | 0 | 0.648 | 89 / provisional |  |
| installed/otsu/psm11 | noisy.png | 8 / 6 of 8 | 0 | 0.702 | 82 / provisional |  |
| installed/otsu/psm11 | slightly_tilted.png | 0 / 0 of 8 | 4 | 0.520 | 92 / provisional |  |
| installed/otsu/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.625 | None / insufficient |  |
| installed/otsu/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.377 | None / insufficient |  |
| installed/otsu/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.505 | None / insufficient |  |
| installed/otsu/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.795 | None / insufficient |  |
| installed/otsu/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.757 | None / insufficient |  |
| installed/otsu/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.746 | None / insufficient |  |
| installed/otsu/psm11 | images (3).jpg | 0 / 0 of 4 | 0 | 0.782 | None / insufficient |  |
| installed/otsu/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.396 | None / insufficient |  |
| installed/otsu/psm3 | clear_flat.png | 8 / 4 of 8 | 0 | 0.400 | 75 / provisional |  |
| installed/otsu/psm3 | glare_like.png | 8 / 5 of 8 | 0 | 0.484 | 75 / provisional |  |
| installed/otsu/psm3 | low_contrast.png | 7 / 4 of 8 | 0 | 0.435 | 82 / provisional |  |
| installed/otsu/psm3 | noisy.png | 8 / 5 of 8 | 0 | 0.521 | 75 / provisional |  |
| installed/otsu/psm3 | slightly_tilted.png | 4 / 4 of 8 | 0 | 1.110 | 82 / provisional |  |
| installed/otsu/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.514 | None / insufficient |  |
| installed/otsu/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.052 | None / insufficient |  |
| installed/otsu/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.725 | None / insufficient |  |
| installed/otsu/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.748 | None / insufficient |  |
| installed/otsu/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.736 | None / insufficient |  |
| installed/otsu/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.785 | None / insufficient |  |
| installed/otsu/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.359 | None / insufficient |  |
| installed/otsu/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.288 | None / insufficient |  |
| installed/adaptive/psm6 | clear_flat.png | 7 / 5 of 8 | 0 | 0.398 | 82 / provisional |  |
| installed/adaptive/psm6 | glare_like.png | 7 / 5 of 8 | 0 | 0.465 | 82 / provisional |  |
| installed/adaptive/psm6 | low_contrast.png | 7 / 5 of 8 | 0 | 0.516 | 82 / provisional |  |
| installed/adaptive/psm6 | noisy.png | 0 / 0 of 8 | 0 | 2.611 | None / insufficient |  |
| installed/adaptive/psm6 | slightly_tilted.png | 0 / 0 of 8 | 2 | 1.224 | 89 / provisional |  |
| installed/adaptive/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.431 | None / insufficient |  |
| installed/adaptive/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 2.278 | None / insufficient |  |
| installed/adaptive/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 3.952 | None / insufficient |  |
| installed/adaptive/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 5.232 | None / insufficient |  |
| installed/adaptive/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 1.566 | None / insufficient |  |
| installed/adaptive/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 1.813 | None / insufficient |  |
| installed/adaptive/psm6 | images (3).jpg | 0 / 0 of 4 | 0 | 1.846 | None / insufficient |  |
| installed/adaptive/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.691 | None / insufficient |  |
| installed/adaptive/psm11 | clear_flat.png | 7 / 5 of 8 | 0 | 1.556 | 82 / provisional |  |
| installed/adaptive/psm11 | glare_like.png | 7 / 5 of 8 | 0 | 0.517 | 85 / provisional |  |
| installed/adaptive/psm11 | low_contrast.png | 7 / 6 of 8 | 0 | 0.747 | 78 / provisional |  |
| installed/adaptive/psm11 | noisy.png | 0 / 0 of 8 | 0 | 16.855 | None / insufficient |  |
| installed/adaptive/psm11 | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.578 | 89 / provisional |  |
| installed/adaptive/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.805 | None / insufficient |  |
| installed/adaptive/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.950 | None / insufficient |  |
| installed/adaptive/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.399 | None / insufficient |  |
| installed/adaptive/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.091 | None / insufficient |  |
| installed/adaptive/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 0 of 7 | 0 | 1.133 | None / insufficient |  |
| installed/adaptive/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 1.341 | None / insufficient |  |
| installed/adaptive/psm11 | images (3).jpg | 0 / 0 of 4 | 0 | 0.833 | None / insufficient |  |
| installed/adaptive/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.551 | None / insufficient |  |
| installed/adaptive/psm3 | clear_flat.png | 7 / 5 of 8 | 0 | 0.658 | 82 / provisional |  |
| installed/adaptive/psm3 | glare_like.png | 7 / 5 of 8 | 0 | 0.535 | 82 / provisional |  |
| installed/adaptive/psm3 | low_contrast.png | 7 / 5 of 8 | 0 | 0.500 | 82 / provisional |  |
| installed/adaptive/psm3 | noisy.png | 0 / 0 of 8 | 0 | 1.748 | None / insufficient |  |
| installed/adaptive/psm3 | slightly_tilted.png | 0 / 0 of 8 | 2 | 0.501 | 89 / provisional |  |
| installed/adaptive/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.554 | None / insufficient |  |
| installed/adaptive/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.502 | None / insufficient |  |
| installed/adaptive/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 3.733 | None / insufficient |  |
| installed/adaptive/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.089 | None / insufficient |  |
| installed/adaptive/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 2 / 2 of 7 | 0 | 1.566 | None / insufficient |  |
| installed/adaptive/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 1.575 | None / insufficient |  |
| installed/adaptive/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.857 | None / insufficient |  |
| installed/adaptive/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.681 | None / insufficient |  |
| installed/deskew/psm6 | clear_flat.png | 8 / 5 of 8 | 0 | 0.787 | 82 / provisional |  |
| installed/deskew/psm6 | glare_like.png | 8 / 5 of 8 | 0 | 0.448 | 82 / provisional |  |
| installed/deskew/psm6 | low_contrast.png | 8 / 5 of 8 | 0 | 0.622 | 82 / provisional |  |
| installed/deskew/psm6 | noisy.png | 7 / 6 of 8 | 0 | 1.177 | 82 / provisional |  |
| installed/deskew/psm6 | slightly_tilted.png | 8 / 6 of 8 | 0 | 1.800 | 75 / provisional |  |
| installed/deskew/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.310 | None / insufficient |  |
| installed/deskew/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.676 | None / insufficient |  |
| installed/deskew/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.177 | None / insufficient |  |
| installed/deskew/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.027 | None / insufficient |  |
| installed/deskew/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.895 | None / insufficient |  |
| installed/deskew/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 1.154 | 93 / provisional |  |
| installed/deskew/psm6 | images (3).jpg | 2 / 0 of 4 | 0 | 0.728 | None / insufficient |  |
| installed/deskew/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.497 | None / insufficient |  |
| installed/deskew/psm11 | clear_flat.png | 8 / 5 of 8 | 0 | 0.732 | 82 / provisional |  |
| installed/deskew/psm11 | glare_like.png | 8 / 5 of 8 | 0 | 0.471 | 82 / provisional |  |
| installed/deskew/psm11 | low_contrast.png | 8 / 5 of 8 | 0 | 0.412 | 82 / provisional |  |
| installed/deskew/psm11 | noisy.png | 8 / 6 of 8 | 0 | 0.564 | 82 / provisional |  |
| installed/deskew/psm11 | slightly_tilted.png | 8 / 5 of 8 | 0 | 0.494 | 82 / provisional |  |
| installed/deskew/psm11 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.803 | None / insufficient |  |
| installed/deskew/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.661 | None / insufficient |  |
| installed/deskew/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.746 | None / insufficient |  |
| installed/deskew/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.243 | None / insufficient |  |
| installed/deskew/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.961 | None / insufficient |  |
| installed/deskew/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.995 | None / insufficient |  |
| installed/deskew/psm11 | images (3).jpg | 0 / 0 of 4 | 0 | 0.565 | None / insufficient |  |
| installed/deskew/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.413 | None / insufficient |  |
| installed/deskew/psm3 | clear_flat.png | 8 / 5 of 8 | 0 | 0.449 | 82 / provisional |  |
| installed/deskew/psm3 | glare_like.png | 8 / 5 of 8 | 0 | 0.446 | 82 / provisional |  |
| installed/deskew/psm3 | low_contrast.png | 8 / 5 of 8 | 0 | 0.487 | 82 / provisional |  |
| installed/deskew/psm3 | noisy.png | 7 / 6 of 8 | 0 | 0.527 | 82 / provisional |  |
| installed/deskew/psm3 | slightly_tilted.png | 8 / 6 of 8 | 0 | 0.447 | 75 / provisional |  |
| installed/deskew/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.510 | None / insufficient |  |
| installed/deskew/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.493 | None / insufficient |  |
| installed/deskew/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 0.486 | None / insufficient |  |
| installed/deskew/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 0.869 | None / insufficient |  |
| installed/deskew/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 0.869 | None / insufficient |  |
| installed/deskew/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 0.922 | None / insufficient |  |
| installed/deskew/psm3 | images (3).jpg | 0 / 0 of 4 | 0 | 0.403 | None / insufficient |  |
| installed/deskew/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.251 | None / insufficient |  |
| installed/deskew_scaled/psm6 | clear_flat.png | 8 / 6 of 8 | 0 | 0.612 | 82 / provisional |  |
| installed/deskew_scaled/psm6 | glare_like.png | 8 / 6 of 8 | 0 | 0.525 | 82 / provisional |  |
| installed/deskew_scaled/psm6 | low_contrast.png | 8 / 6 of 8 | 0 | 0.698 | 75 / provisional |  |
| installed/deskew_scaled/psm6 | noisy.png | 8 / 5 of 8 | 0 | 1.299 | 82 / provisional |  |
| installed/deskew_scaled/psm6 | slightly_tilted.png | 8 / 3 of 8 | 0 | 0.753 | 82 / provisional |  |
| installed/deskew_scaled/psm6 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.382 | None / insufficient |  |
| installed/deskew_scaled/psm6 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.235 | None / insufficient |  |
| installed/deskew_scaled/psm6 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.669 | None / insufficient |  |
| installed/deskew_scaled/psm6 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 2.629 | None / insufficient |  |
| installed/deskew_scaled/psm6 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 1.500 | None / insufficient |  |
| installed/deskew_scaled/psm6 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 1.592 | 93 / provisional |  |
| installed/deskew_scaled/psm6 | images (3).jpg | 2 / 0 of 4 | 0 | 1.164 | None / insufficient |  |
| installed/deskew_scaled/psm6 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.827 | None / insufficient |  |
| installed/deskew_scaled/psm11 | clear_flat.png | 8 / 6 of 8 | 0 | 0.657 | 82 / provisional |  |
| installed/deskew_scaled/psm11 | glare_like.png | 8 / 6 of 8 | 0 | 0.697 | 82 / provisional |  |
| installed/deskew_scaled/psm11 | low_contrast.png | 8 / 6 of 8 | 0 | 0.691 | 75 / provisional |  |
| installed/deskew_scaled/psm11 | noisy.png | 8 / 4 of 8 | 0 | 1.326 | 89 / provisional |  |
| installed/deskew_scaled/psm11 | slightly_tilted.png | 8 / 4 of 8 | 0 | 0.647 | 82 / provisional |  |
| installed/deskew_scaled/psm11 | photo_1_2026-11-20_16-10-58.jpg | 1 / 1 of 6 | 0 | 1.442 | None / insufficient |  |
| installed/deskew_scaled/psm11 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.174 | None / insufficient |  |
| installed/deskew_scaled/psm11 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.750 | None / insufficient |  |
| installed/deskew_scaled/psm11 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 2.122 | None / insufficient |  |
| installed/deskew_scaled/psm11 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 1 of 7 | 0 | 4.351 | None / insufficient |  |
| installed/deskew_scaled/psm11 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 2.337 | None / insufficient |  |
| installed/deskew_scaled/psm11 | images (3).jpg | 2 / 0 of 4 | 0 | 1.620 | None / insufficient |  |
| installed/deskew_scaled/psm11 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.666 | None / insufficient |  |
| installed/deskew_scaled/psm3 | clear_flat.png | 8 / 6 of 8 | 0 | 0.731 | 82 / provisional |  |
| installed/deskew_scaled/psm3 | glare_like.png | 8 / 6 of 8 | 0 | 1.366 | 82 / provisional |  |
| installed/deskew_scaled/psm3 | low_contrast.png | 8 / 6 of 8 | 0 | 1.961 | 75 / provisional |  |
| installed/deskew_scaled/psm3 | noisy.png | 8 / 5 of 8 | 0 | 2.106 | 82 / provisional |  |
| installed/deskew_scaled/psm3 | slightly_tilted.png | 8 / 3 of 8 | 0 | 1.226 | 82 / provisional |  |
| installed/deskew_scaled/psm3 | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 1.684 | None / insufficient |  |
| installed/deskew_scaled/psm3 | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 1.785 | None / insufficient |  |
| installed/deskew_scaled/psm3 | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 2.271 | None / insufficient |  |
| installed/deskew_scaled/psm3 | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 4.404 | None / insufficient |  |
| installed/deskew_scaled/psm3 | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 1 / 0 of 7 | 0 | 2.769 | None / insufficient |  |
| installed/deskew_scaled/psm3 | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 0 / 0 of 6 | 0 | 1.492 | None / insufficient |  |
| installed/deskew_scaled/psm3 | images (3).jpg | 3 / 0 of 4 | 0 | 1.243 | None / insufficient |  |
| installed/deskew_scaled/psm3 | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 0.680 | None / insufficient |  |
| installed/gray/psm6/vocabulary | clear_flat.png | 8 / 5 of 8 | 0 | 0.364 | 82 / provisional |  |
| installed/gray/psm6/vocabulary | glare_like.png | 8 / 5 of 8 | 0 | 0.423 | 82 / provisional |  |
| installed/gray/psm6/vocabulary | low_contrast.png | 8 / 5 of 8 | 0 | 0.491 | 82 / provisional |  |
| installed/gray/psm6/vocabulary | noisy.png | 7 / 6 of 8 | 0 | 0.478 | 82 / provisional |  |
| installed/gray/psm6/vocabulary | slightly_tilted.png | 2 / 2 of 8 | 0 | 0.472 | 89 / provisional |  |
| installed/gray/psm6/vocabulary | photo_1_2026-11-20_16-10-58.jpg | 0 / 0 of 6 | 0 | 0.563 | None / insufficient |  |
| installed/gray/psm6/vocabulary | photo_2_2026-11-20_16-10-58.jpg | 0 / 0 of 0 | 0 | 0.510 | None / insufficient |  |
| installed/gray/psm6/vocabulary | photo_3_2026-11-20_16-10-58.jpg | 0 / 0 of 8 | 0 | 1.017 | None / insufficient |  |
| installed/gray/psm6/vocabulary | photo_4_2026-11-20_16-10-58.jpg | 0 / 0 of 7 | 0 | 1.256 | None / insufficient |  |
| installed/gray/psm6/vocabulary | prod_img-5076444_p_2_en_au_19310055102849_2509161400_p_2.png | 0 / 0 of 7 | 0 | 1.350 | None / insufficient |  |
| installed/gray/psm6/vocabulary | prod_img-7296121_p_2_en_au_19310055102726_2509161400_p_2.png | 1 / 1 of 6 | 0 | 1.802 | 93 / provisional |  |
| installed/gray/psm6/vocabulary | images (3).jpg | 2 / 0 of 4 | 0 | 0.878 | None / insufficient |  |
| installed/gray/psm6/vocabulary | v2_1ea663e6-4f82-49e1-9180-959a13fb410d.jpg | 0 / 0 of 0 | 0 | 1.071 | None / insufficient |  |

Each pytesseract call launches a Tesseract subprocess and includes model loading, OCR, TSV parsing and process overhead. Isolated model-loading time and Tesseract subprocess peak RAM are not measured. Optional Python peak memory excludes OpenCV native allocations and the OCR child process. Model identity/file size and input hashes are in the JSON sidecar. Single-pass tests are controlled recognition comparisons, not the bounded runtime retry policy. Pipeline times cover preprocessing and analysis but exclude upload/storage. Timings are descriptive local measurements and can vary with CPU load.

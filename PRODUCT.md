# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Consumers who find technical ingredient names, additive codes, nutrition units, or small packaged-food labels difficult to interpret. They use NutriScan while reviewing an English food label.

## Product Purpose

NutriScan turns a JPG or PNG label photo into a readable, traceable summary of the text it can identify. Success means users can review the extracted ingredients, additives, allergen keywords, comparable nutrient values, score contributions, and OCR text while seeing what remains uncertain.

## Positioning

NutriScan is a local academic prototype that combines OCR with inspectable, rule-based label matching and scoring. Its summary is informational screening, not medical advice or a food-safety guarantee.

## Operating Context

The app runs locally in a browser. Users upload a label image, may select allergen groups to watch for, review the scan, and reopen saved results from local history without running OCR again.

## Capabilities and Constraints

- Flask serves scan, result, history, upload, and history API routes.
- OpenCV preprocessing and Tesseract OCR run locally. Knowledge records are validated JSON files.
- Supported uploads are JPG and PNG images up to the configured 5 MB limit.
- Nutrition status requires comparable units and basis. Screening scores, limits, risk labels, and keyword matching are provisional.
- Allergen alerts stay separate from scoring. Results include an informational disclaimer.
- No accounts, cloud processing, barcode scanning, medical recommendations, or multilingual OCR.
- Keep the existing routes, element IDs, and browser interactions working. Do not add external CDN dependencies.

## Brand Commitments

Keep the NutriScan name and use only an original project mark. Do not use an existing company logo, trademark, or third-party artwork.

## Evidence on Hand

- The repository includes a synthetic sample label at `static/images/sample_label.png` for local demonstrations.
- Product behavior and limitations are documented in `docs/PRD.md`, `README.md`, and `DATA_REVIEW.md`.
- No real packaged-food photographs or independently verified OCR benchmark are supplied.

## Product Principles

- Make recognized text and its source visible.
- Preserve uncertainty instead of guessing.
- Separate allergen alerts from screening scores.
- Keep processing local and results understandable.

## Accessibility & Inclusion

Keep controls keyboard-operable, announce scan progress, respect reduced-motion preferences, and pair signal colours with text labels.

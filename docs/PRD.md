# NutriScan Product Requirements

## Problem and users

Consumers find technical ingredient names, additive codes, nutrition units, and small or difficult-to-read packaging labels hard to interpret. NutriScan is a local academic prototype for people who want a readable, traceable summary of an English packaged-food label.

## Main outcome

From one JPG/PNG label photo, return extracted text, decoded known additives, ingredient flags, separate allergen alerts, comparable nutrient statuses, and an explainable informational Health Score.

## MVP features

- Local Flask scan, result, and history pages; safe upload validation and stored result reopening.
- OpenCV preprocessing and Tesseract OCR with a clear retry/failure path.
- Four validated JSON knowledge files with about 180 additive, 45 allergen keyword, 65 ingredient flag, and 10 nutrition-limit records.
- Ingredient/code matching, nutrition parsing with basis and units, configured score breakdown, and visible unknowns.
- Offline-friendly responsive interface and sample-label end-to-end demo.

## Explicit non-goals

- Training machine-learning or deep-learning models.
- Native Android/iOS applications, barcode scanning, live camera streaming or cloud hosting.
- Multilingual OCR and automatic translation of non-English labels.
- User accounts, authentication and simultaneous multi-user operation.
- Medical diagnosis, disease-specific diet recommendations or a guarantee of food safety.
- Perfect reconstruction of text hidden by strong glare, folds, severe blur or extreme curvature.

## Success criteria

- The app starts locally with one documented command and the sample label completes the full scan path.
- Validation accepts only supported, non-empty decoded images within the configured 5 MB limit.
- All four datasets validate at the target counts; every assumed record is reviewable in `DATA_REVIEW.md`.
- Routes and required unit cases pass; history updates atomically and saved results reopen without OCR.
- Evaluation produces CSV and Markdown results for preprocessing off/on and reports failures honestly.
- Every result labels score and nutrient statuses as screening information and displays allergen alerts separately.

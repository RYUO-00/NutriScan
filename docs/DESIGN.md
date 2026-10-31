# NutriScan design

This document records the Hallmark Newsprint variant on `design-hallmark`.

## Audience and task

People checking packaged-food labels use NutriScan to scan a label, review detected ingredients and nutrients, and understand how the result was calculated.

## Visual system

- **Material:** warm paper, dark ink, and ruled rows inspired by printed food labels. Use whitespace and rules to separate report sections; reserve tinted surfaces for allergen alerts.
- **Type:** bundled Archivo Variable for display headings, the system's Source Serif 4/Georgia stack for reading text, and system monospace for measured values and codes. Archivo is licensed under the SIL Open Font License 1.1; its license is bundled at `static/fonts/Archivo-OFL.txt`.
- **Colour:** tokenized paper and ink neutrals; dark teal marks the primary action; red identifies selected allergen matches; amber identifies other detected allergens and caution flags; green identifies beneficial flags. Every state also has a text label.
- **Composition:** the scan page pairs the upload form with the synthetic label specimen. Result pages read as a report: verdict and score, allergen findings, score changes, nutrient readings, additive classes, ingredient flags, recognized text, and image comparison. History is a ruled list that preserves scan date, image name, score, and band.
- **Responsive behaviour:** keep the scan form and specimen in one column on narrow screens, keep the first nutrient column visible while each row becomes a labelled block, and stack the original and processed images within their shared comparison frame.
- **Interaction:** support file selection and drop, remembered allergen choices, sample scans, real scan-stage updates, result links, expandable OCR/source details, and a keyboard-operable image slider. Focus, disabled, loading, error, success, and reduced-motion states are explicit.

## Product invariants

- Preserve every Flask route and existing script/test element ID.
- Keep scoring weights and thresholds in `config.py`, JSON knowledge files as the data source, and source explanations in the result disclosure.
- Keep allergen detection separate from scoring. Red alerts require a group selected before scanning; other detected groups appear in the amber list.
- Show energy, protein, and fibre as informational. Do not add status chips or score changes for them.
- Store timestamps in ISO format and format them only for display.
- Keep the screening disclaimer visible on scan, result, history, and error screens.
- Bundle fonts and other assets locally; do not depend on a CDN.

## Hallmark direction

Newsprint was selected from the three-theme deal for its paper, ink, and ruled-label material. The draw's marketing-page composition was set aside because this repository contains an app screen with an established Flask route structure. The user-directed grotesque headings and monospace measured data take precedence over the theme's slab-serif display face.

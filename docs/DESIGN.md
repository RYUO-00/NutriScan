# NutriScan Interface Draft

First draft for the functional UI phase. Keep this file editable as the interface evolves.

- **Tone:** trustworthy and calm, like a lab report crossed with good packaging design. Use direct labels, explain matches, and keep uncertainty visible.
- **Colour language:** red means high or critical allergen; amber means moderate or caution; green means low or beneficial; blue or neutral means informational. Pair every colour with a word label and explanation.
- **Layout:** start at 360 px wide. Use a clear reading order and compact editorial sections rather than a generic grid of identical cards. Keep comparison, raw OCR, and score reasons easy to find.
- **Scan flow:** obvious upload/drop target, image preview, camera capture on mobile, remembered allergen chips, quality tips, sample label, and live stage progress.
- **Result flow:** score and band, selected-allergen alert, nutrient statuses, decoded additives, ingredient flags, score contributions, unknowns, raw OCR highlights, and original/processed comparison. Repeat the informational disclaimer.
- **Access:** keyboard-operable controls, visible focus, useful status announcements, reduced-motion support, and text labels independent of colour.
- **Runtime:** no external CDN or network asset dependency; provide graceful errors and usable content without JavaScript where practical.

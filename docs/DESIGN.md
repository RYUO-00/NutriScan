# NutriScan Design System

## Direction

**The page is the label.** NutriScan reads packaged-food labels, so its interface should feel like a carefully printed nutrition panel crossed with a receipt. Treat a scan result as one tall, readable label rather than a SaaS dashboard.

## Visual language

- **Surface and rules:** warm paper white, near-black ink, generous white space, and heavy black rules between major sections. Use plain rectangular sections and ruled rows; avoid soft-shadow card grids, gradients, glass effects, and decorative background texture.
- **Colour:** mostly black and white. Red is reserved for selected critical allergen alerts, amber for caution or additional detected allergens, and green for beneficial or low signals. Each colour is paired with a text label. Use one restrained, non-signal accent for primary actions only; never use purple or blue-violet.
- **Typography:** a strong grotesque system sans for headings and interface copy, with a deliberate system fallback. Use a system monospace for codes, units, timestamps, nutrient values, and score arithmetic. Use tabular numerals for data. No external font CDN; use bundled open-licensed fonts only when available and useful.
- **Brand mark:** create an original, monochrome NutriScan wordmark in the heading face with a small label-scan mark. Keep it legible at 24 px and on light or dark surfaces. Use it in the site header on every page, linked to the scan page, with alt text. Add `static/images/favicon.svg` and a PNG fallback when generation is available. Never use a third-party mark or artwork.
- **Page metadata:** each page has a specific title and factual meta description. Set matching Open Graph title and description values without adding unsupported claims.

## Scan page

Use the available width for the upload task instead of leaving an empty hero column. The drop zone has clear idle, drag-over, and selected-file states; keep the native file control accessible and preserve camera capture, sample scan, allergen selection, preview, validation and progress behavior. Selected allergen chips must read as selected without relying on colour alone.

## Result page

Read from top to bottom as a printed report in this order:

1. A verdict block with a large stamp-like score, bold boxed score band, one plain-language sentence, and a small image filename. Count the score up on load and respect reduced-motion preferences.
2. Selected-allergen critical alerts, followed by the amber “Also contains” matches.
3. “What drove your score” with one labelled bar per deduction or credit, preserving the point values and reasons.
4. Compact nutrient rows with the comparable status beside the value. Energy, protein, and fibre remain informational and have no status chip or score effect.
5. Decoded additives and ingredient flags, then readable OCR text, then the original/processed image comparison.
6. The informational disclaimer and collapsible “How this was calculated and sources” disclosure.

Keep the image comparison within its own section. Both images use one aligned frame on wide screens; small badges sit in a dedicated part of the frame, away from image content. Stack the images on narrow screens while keeping the slider functional.

## Interaction and access

- Preserve every existing route, element ID, form name, feature, and JavaScript behavior.
- Show the actual scan stages: preprocessing, reading text, decoding, nutrition, scoring, and saving. Do not claim a stage before the corresponding work begins.
- Hovering or focusing an additive, ingredient flag, or allergen card highlights its matching OCR text. Hovering or focusing matched OCR text highlights the related card.
- Use visible instant focus rings, keyboard-operable controls, useful status announcements, and reduced-motion alternatives. Colour never carries a signal by itself.
- Keep the full source strings in the data and show them once in the collapsed source section. Keep the informational screening disclaimer on every result.
- Do not introduce external CDN or network asset dependencies. Keep routes usable without JavaScript where practical.

## Avoid

No dashboard layout, huge centered hero with an empty side, gradient, glassmorphism, soft-shadow card grid, pill-everything, emoji icons, purple or blue-violet accent, or unsupported health or safety claims.

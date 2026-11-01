---
name: "NutriScan — The Food Label Laboratory"
description: "A local label-screening interface that routes readers from findings to source evidence."
colors:
  warm-paper: "#f4f0e5"
  paper-white: "#fffdf7"
  recessed-paper: "#ebe8dd"
  ink: "#1d2420"
  secondary-ink: "#4c5851"
  fine-rule: "#b9c0b7"
  strong-rule: "#68736b"
  screening-green: "#285544"
  screening-green-soft: "#e5eee7"
  wayfinding-yellow: "#f0d44b"
  yellow-outline: "#614d00"
  caution-amber: "#68460d"
  caution-amber-soft: "#fff2d6"
  selected-alert-red: "#842b24"
  selected-alert-red-soft: "#f8e8e3"
  information-blue: "#24546d"
  information-blue-soft: "#e5eef2"
typography:
  display:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "clamp(3rem, 5vw, 4.2rem)"
    fontWeight: 650
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  headline:
    fontFamily: '"Source Serif 4", Georgia, serif'
    fontSize: "2rem"
    fontWeight: 560
    lineHeight: 1.05
    letterSpacing: "-0.025em"
  title:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "1.45rem"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "0.84rem"
    fontWeight: 720
    lineHeight: 1.2
  navigation:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.5
  wayfinding:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "1rem"
    fontWeight: 740
    lineHeight: 1.2
  chip:
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif'
    fontSize: "0.9rem"
    fontWeight: 650
    lineHeight: 1.2
  data:
    fontFamily: '"Cascadia Mono", "SFMono-Regular", Consolas, monospace'
    fontSize: "0.8rem"
    fontWeight: 600
    lineHeight: 1.35
rounded:
  none: "0px"
  dot: "50%"
components:
  nav-active:
    backgroundColor: "{colors.wayfinding-yellow}"
    textColor: "{colors.ink}"
    typography: "{typography.navigation}"
    padding: "0 16px"
    rounded: "{rounded.none}"
    height: "44px"
  route-step:
    backgroundColor: "{colors.wayfinding-yellow}"
    textColor: "{colors.ink}"
    typography: "{typography.wayfinding}"
    padding: "10px 16px"
    rounded: "{rounded.none}"
    height: "56px"
  route-step-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.wayfinding-yellow}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper-white}"
    typography: "{typography.navigation}"
    rounded: "{rounded.none}"
    padding: "10px 19px"
  button-primary-hover:
    backgroundColor: "{colors.screening-green}"
    textColor: "#ffffff"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.navigation}"
    rounded: "{rounded.none}"
    padding: "10px 19px"
  button-quiet-hover:
    backgroundColor: "{colors.wayfinding-yellow}"
    textColor: "{colors.ink}"
  photo-upload-dropzone:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.secondary-ink}"
    rounded: "{rounded.none}"
    padding: "22px"
  photo-upload-dropzone-focus:
    backgroundColor: "{colors.screening-green-soft}"
  allergen-chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.chip}"
    rounded: "{rounded.none}"
    padding: "6px 12px"
    height: "40px"
  allergen-chip-selected:
    backgroundColor: "{colors.wayfinding-yellow}"
    textColor: "{colors.ink}"
  selected-alert:
    backgroundColor: "{colors.selected-alert-red-soft}"
    textColor: "{colors.selected-alert-red}"
    rounded: "{rounded.none}"
    padding: "16px 18px 18px"
  finding-card:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "14px 15px 15px"
  score-plate:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.none}"
    padding: "21px 24px"
  information-disclaimer:
    backgroundColor: "{colors.information-blue-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "15px 17px"
---

# Design System: NutriScan

## Overview

**Creative North Star: "The Evidence Route"**

The interface behaves like an annotated route through a food label. Yellow wayfinding links make the next step easy to spot; headings and thin section rails keep the report sequence legible; values stay beside their comparison basis; matched text, image views, OCR text, and source notes remain inspectable.

The Food Label Laboratory identity comes through in warm report paper, ink-first typography, fine rules, and tabular metadata. Flat color fields distinguish actions and screening states without turning the report into a stack of floating dashboard tiles. Each alert keeps its own label and meaning visible.

**Key Characteristics:**
- Concise wayfinding through scan steps and report sections.
- A source-first result sequence that keeps findings connected to evidence.
- Functional status colors paired with readable text labels.

## Colors

The palette uses warm paper and dark ink as its base, with yellow for orientation, green for beneficial or low states, blue for information, and separate red and amber alert states.

### Primary
- **Wayfinding Yellow:** marks the current navigation item, scan and report route links, selected allergen preference chips, and score meter accents.
- **Yellow Outline:** gives selected preference chips a visible border against the warm yellow fill.

### Secondary
- **Screening Green:** colors beneficial or low states, positive score contributions, links, and the upload focus/hover state.
- **Soft Screening Green:** supports low and beneficial status labels without replacing their text.

### Tertiary
- **Information Blue:** marks informational or non-comparable readings, scan status, and keyboard focus.
- **Soft Information Blue:** provides a quiet background for informational notes, unknown text, and the required disclaimer.

### Neutral
- **Warm Paper:** is the page ground.
- **Paper White:** holds upload and preview surfaces, finding cards, comparison panels, and text on the score plate.
- **Recessed Paper:** separates image wells and small hover areas from the paper surface.
- **Ink:** carries primary text, strong rules, and the score plate.
- **Secondary Ink:** supports body explanations, timestamps, and metadata.
- **Fine Rule** and **Strong Rule:** define row boundaries and section divisions without enclosing every block in a card.

### Alert Semantics
- **Selected-Alert Red** and its soft fill mark user-selected allergen matches, high or harmful screening labels, and downward score contributions.
- **Caution Amber** and its soft fill mark other detected allergen groups and moderate or caution screening labels.

**The Separate Alert Rule.** Selected allergen matches remain red and independent of the score; other detected allergen groups remain amber. The alert text states what matched and where it appeared.

**The Route Signal Rule.** Yellow marks meaningful navigation and selected controls, while status labels retain their own green, blue, amber, or red meaning.

## Typography

- **Display Font:** Source Sans 3 (with Segoe UI, sans-serif fallback)
- **Body Font:** Source Sans 3 (with Segoe UI, sans-serif fallback)
- **Editorial Font:** Source Serif 4 (with Georgia, serif fallback)
- **Data Font:** Cascadia Mono (with SFMono-Regular, Consolas, monospace fallback)

**Character:** Source Sans 3 keeps controls, labels, and report titles direct and readable. Source Serif 4 adds an editorial voice to section headings and score numerals; monospaced figures keep values, units, dates, and technical details aligned.

### Hierarchy
- **Display** (650, clamp from 3rem to 4.2rem, 0.98 line-height): scan-page and result lead headings, with responsive sizing on narrow screens.
- **Headline** (560, 2rem, 1.05 line-height): serif report-section headings and empty-state titles.
- **Title** (700, 1.45rem): upload-section headings and compact interface titles.
- **Body** (400, 17px, 1.5 line-height): explanatory copy, with paragraphs commonly capped near 60–66ch.
- **Label** (650–760, about 0.78–0.9rem): control labels, statuses, and supporting captions.
- **Data** (600, 0.8–1.08rem, 1.2–1.35 line-height): tabular monospaced values, units, dates, codes, and score contributions.

**The Data Voice Rule.** Keep numeric values and their units or comparison basis together; use tabular figures for values, dates, and technical metadata.

## Layout

The shared content column is capped at 1160px. At desktop widths, the header, main content, and footer share the centered column with 24px side insets. At 700px and below, the side inset narrows to 16px; at 390px and below it narrows to 13px.

The scan view uses a two-part hero, then three route bands, the upload and alert controls, and the review-method list. At 700px and below, the hero and route bands stack in that same reading order. The report begins with filename, timestamp, and score; a six-link section route precedes allergen alerts, nutrient screening, matched findings, score contributions, and image/OCR/source evidence. That route becomes two columns at mobile widths. The history list pairs its timestamp, filename, score, and alert state, then stacks these details at narrow widths.

The main content starts with 32px top padding and 60px bottom padding on wide screens, shifting to 27px and 54px at 700px and below. The system uses recurring 8–24px control gaps and 18–26px section gaps, with thin rules marking changes in report section.

**The Evidence Order Rule.** Lead the report with the scan identity and score, then place alerts and comparable readings before matched findings, score reasoning, and source evidence.

## Elevation & Depth

The interface has no box shadows. Flat paper, white, muted, and ink surfaces establish grouping; borders and horizontal rules carry structure. The dark score plate is the strongest tonal layer, while red, amber, green, and blue fields are reserved for their screening states.

**The Flat Report Rule.** Use tonal fills and rules for hierarchy; do not add floating-card shadows to report sections.

## Shapes

Most elements have square corners. Cards, buttons, route links, alerts, and comparison frames use the browser's zero-radius default; the scan-progress markers are the recurring circular shape. Thin solid or dashed borders distinguish framing, upload affordance, and section boundaries.

## Components

### Navigation
The header navigation is a standard pair of web links. The active item and meaningful route links use the yellow fill; hover inverts them to ink with yellow text. Keyboard focus has a clear blue outline.

### Route Bands
Three numbered scan links lead from photo upload to alert selection and evidence review. The result page uses a compact six-link section route. Keep links short and preserve the order of the content they reveal.

### Buttons
Buttons are square, ink-filled primary actions with a quiet transparent variant. The primary action changes to green on hover; the quiet action changes to yellow. Both retain a visible keyboard focus outline, and disabled scan actions lower opacity while indicating the waiting state.

### Chips
Allergen preference chips are outlined, square toggle buttons. Hover uses a muted paper fill; a pressed chip uses the yellow fill and a darker yellow border. The pressed state remains text-readable.

### Cards / Containers
Finding cards use paper-white fills, fine borders, and compact internal padding. Score information sits in a single dark plate rather than a floating card. Selected allergen alerts and other detected allergens have separate red and amber containers.

### Inputs / Fields
The photo dropzone is a large paper-white label with a dashed rule, centered upload mark, and file action. Hover, focus-within, and drag-over use the green state. The actual file input stays keyboard reachable. The comparison range input spans the report width and uses green as its accent.

### Signature Components
- **Score Plate:** a dark, flat report panel that places the serif score beside the band, scale, and a reconciled before/after summary.
- **Evidence Comparison:** original and processed images share a framed view with a range control; at narrow widths the images stack and the same control adjusts their split.
- **Alert Blocks:** selected allergen findings remain distinct from other detected allergen groups, with readable match and source-section text.

## Do's and Don'ts

### Do:
- **Do** keep yellow for meaningful wayfinding, the active route, selected controls, and score meter accents.
- **Do** show selected allergen matches in red and other detected allergen groups in amber, with text that identifies matches and source sections.
- **Do** keep values and units, thresholds, or bases together and use tabular figures for numeric evidence.
- **Do** preserve the flat report surface, thin rules, and responsive content order.

### Don't:
- **Don't** rely on color alone to explain a screening state.
- **Don't** use red as decoration; reserve it for selected allergen matches and high or harmful screening states.
- **Don't** turn the result into an unprioritized stack of identical panels or add shadowed dashboard cards.
- **Don't** add airport pictograms or imply airport services; only the concise wayfinding grammar is carried into the food-label interface.

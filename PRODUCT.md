# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

People checking packaged-food labels who need a readable explanation of what a photo reveals and where that explanation comes from.

## Product Purpose

NutriScan is a local academic prototype that reads an English packaged-food label photo and returns extracted text, ingredient and additive matches, allergen findings, comparable nutrient screening, and an explainable informational Health Score. Success means helping a person understand the scan result and its sources while making uncertainty visible.

## Positioning

NutriScan combines on-device image preprocessing and OCR with deterministic, reviewable knowledge-base matching and configured screening rules. It shows the evidence and limits behind its findings; it does not certify safety or give medical advice.

## Operating Context

The user selects or captures a JPG or PNG in a browser. A local Flask app processes it, saves the scan and comparison images on the same computer, and allows the saved result to be reopened from history without rerunning OCR. A bundled sample label supports demonstration and evaluation.

## Capabilities and Constraints

- Existing Flask routes, HTML templates, CSS, and vanilla JavaScript are the application interface.
- OpenCV preprocessing and Tesseract OCR feed deterministic ingredient, additive, allergen, nutrition, and score modules.
- Four validated JSON knowledge files and local JSON scan history remain the data sources.
- Preserve upload validation, security checks, result object fields, history reopening, and all existing features.
- The app is offline-friendly: do not add authentication, cloud services, machine-learning models, external CDN dependencies, or an unnecessary frontend framework.
- Results are informational screening, not medical advice or a guarantee of food safety. Real label photos and manually verified OCR ground truth are not currently supplied.

## Brand Commitments

The requested product identity is “NutriScan — The Food Label Laboratory,” drawing on editorial food journalism, contemporary packaging, scientific reports, and Swiss information hierarchy. Headings may be expressive; controls and labels must stay readable; values, units, dates, and technical metadata use a clear data voice. Use a warm paper ground, dark typography, and controlled accents. Red remains reserved for actual selected-allergen alerts or severe screening states.

## Evidence on Hand

- Four local JSON knowledge datasets, with their assumptions tracked in `DATA_REVIEW.md`.
- A generated sample label and synthetic test fixtures.
- A local sample-scan workflow and saved scan history.
- No verified real-world performance benchmark, customer testimonial, or real product-photography set is available; do not invent these.

## Product Principles

- Explain findings with the label text and configured sources that support them.
- Show comparison basis and uncertainty alongside numeric screening.
- Keep allergen alerts independent of the score.
- Preserve unknown text and unsupported values instead of implying certainty.
- Keep the app local, responsive, and operable with keyboard and assistive technology.

## Accessibility & Inclusion

Controls need accessible names and visible keyboard focus. Status meaning must not rely on color alone. Keep scan, comparison, and history workflows usable on narrow mobile screens and honor reduced-motion preferences.

# NutriScan Decisions

Append-only log. Add new decisions below; do not rewrite existing entries.

1. **JSON instead of MySQL:** this is a single-user mini-project with small local datasets. Persistence stays behind `storage.py` functions to keep a future migration possible.
2. **Rule-based instead of ML:** deterministic matching and scoring improve explainability and fit the project scope and feasibility.
3. **No login:** accounts are out of scope for the local demonstration.
4. **Tesseract with OpenCV preprocessing:** both are locally runnable and directly support the required image-to-text pipeline.
5. **Thresholds are screening values, not medical limits:** show source/basis and uncertainty; do not present the score as medical advice.

6. **Nutrition cutoff location:** `nutrition_limits.json` stores the ten nutrient keys, units, basis, and source notes. Numeric cutoffs live only in `config.py` to satisfy the central-configuration constraint and avoid conflicting copies.
7. **Knowledge-base evidence:** additive code/name identity uses Codex CXG 36-1989 as nomenclature, not as proof of Indian permission or safety. Provisional risk classifications, expanded keyword mappings, ingredient flags, and numeric nutrition cutoffs remain marked as assumptions in `DATA_REVIEW.md` until checked against applicable sources.

8. **Local image retention:** retain original and processed images alongside saved scan history so a result can reopen offline. No automatic deletion is performed; the local user can clear the JSON history and paired upload files using the documented cleanup steps.

9. **Parenthetical additive annotations:** when a trailing parenthetical contains a known INS code, strip that annotation only for additive-name lookup; preserve the original ingredient token and let the code decoder report explicit codes. Soy-lecithin name variants are included as reviewable assumptions for INS 322.

10. **Result explanations and classification:** use code-specific Codex functional classes for additives and queue multi-function entries when a single class cannot be selected confidently. Keep complete source strings in the knowledge data and disclose unique sources in one collapsed result section. Treat protein and fibre as informational, and treat energy as informational while its cutoff remains a project assumption. Red allergen alerts are reserved for groups selected before scanning; other matches use an amber “Also contains” list. Show timestamps in readable form in the UI while preserving ISO storage. Create the ignored history JSON as an empty array at startup when absent.

11. **Comparison frame behavior:** keep both image layers inside one explicitly sized shared frame with captions in their own reserved row. At narrow widths, stack the images and let the existing slider adjust the vertical split so labels never cover image content.

12. **Prompt B / Impeccable visual direction:** treat the food label itself as the page’s visual structure—warm paper, ink, heavy rules, tabular data, a stamp-like score, and semantic alert colors. Keep all brand artwork original and local. Report scan stages from the actual pipeline and connect recognized text to its report findings; validate the scan, result, and history at desktop and mobile widths before committing.

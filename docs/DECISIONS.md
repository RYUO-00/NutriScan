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

12. **Scan progress truth:** the existing client timer cycled through processing labels that did not reflect backend work. Progress is now reported from the six actual route/pipeline stages through a request-correlated in-memory endpoint, expires after ten minutes, and records completion or a friendly failure without changing saved result objects.

13. **Visual direction for the 2026-10-31 redesign:** the user selected the Airport Wayfinding challenger for its clear route bands and visible navigation system. Translate those traits to scan/report section wayfinding and use yellow for navigation, while retaining the requested warm paper ground and reserving red/amber for real alert/caution meanings. Airport pictograms and airport-specific claims are not part of NutriScan.

14. **Interface type and assets:** use a locally bundled Source Sans 3 variable font for headings and controls, with the existing Source Serif 4 reserved for expressive score figures and editorial archive titles. Keep the SIL Open Font License beside the font; the browser makes no external font request.

15. **Scan-page route:** the first screen uses three in-page route bands for upload, allergen preferences, and evidence review, followed by the sample-label specimen and six named pipeline stages. During an actual scan, highlight only the stage reported by Flask's request-correlated progress endpoint.

16. **Food Label Laboratory report and archive:** guide the report from score and selected alerts through comparable nutrient readings, matched findings, the reconciled score ledger, image evidence, and source/OCR disclosures. Use threshold ranges from the saved comparable readings; keep energy, protein, and fibre informational. Keep the desktop comparison layers explicitly the same size inside one frame, and stack them at narrow widths. In history, give the timestamp, score, product entry, and alert badge separate responsive positions so the score cannot cover the filename.

17. **Optional local-network access:** keep loopback-only startup as the default and expose the Flask server to the local network only through an explicit `--lan` option. LAN mode warns on the terminal and keeps debug mode and the reloader disabled; firewall changes remain a manual, documented Windows action.

18. **Score-led report explanation:** continue deriving the displayed score only from the existing scoring engine. Summarize its starting value, grouped deductions, grouped credits, any clamp/range adjustment, and final score from the same contribution data; use a grouped waterfall only as a second view of those contributions and retain the full ledger. Keep energy, protein, and fibre informational until a supported scoring basis is established.

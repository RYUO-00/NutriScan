# NutriScan coding rules

- Read `docs/` before coding and consult these project notes before each task.
- Work on one phase or feature at a time. Inspect existing code before editing it.
- Keep the required module layout and thin Flask routes.
- Do not add MySQL, login, machine-learning models, cloud services, or external CDN dependencies.
- Keep all score weights, caps, and thresholds in `config.py`; JSON knowledge files remain the data source of truth.
- Never invent data sources. Use `Project assumption - needs verification` for unsupported record bases or thresholds and list them in `DATA_REVIEW.md`.
- Never compare per-serving values directly with per-100-g/ml thresholds. Salt is not sodium; a conversion must be labelled as an estimate.
- Keep allergen alerts separate from scoring and visible regardless of score. Show the informational disclaimer on every result.
- Run `pytest` before declaring a phase done. Update `TASKS.md` and `docs/MEMORY.md` after every phase.
- Append to `docs/DECISIONS.md`; do not rewrite existing entries.

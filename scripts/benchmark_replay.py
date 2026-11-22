"""Replay an explicit local-image manifest without modifying scan history.

Verified counts mean parser-admitted fields, not independently measured accuracy.
Run before editing the pipeline, then repeat with --compare pointing to baseline.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from nutrition import comparable_nutrients
from ocr import recognize_text
from preprocess import preprocess_image
from storage import load_knowledge


def comparison_rows(before, after):
    """Join identical source bytes; changed or unmatched images are not compared."""
    previous = {row["sha256"]: row for row in before["images"]}
    rows = []
    for row in after["images"]:
        old = previous.get(row["sha256"])
        rows.append({
            "name": row["name"], "kind": row.get("kind", "unspecified"),
            "before": old.get("verified_core_count") if old else None,
            "after": row.get("verified_core_count"),
            "delta": (row["verified_core_count"] - old["verified_core_count"]
                      if old and old.get("verified_core_count") is not None
                      and row.get("verified_core_count") is not None else None),
            "before_fields": old.get("verified_core_fields", []) if old else [],
            "after_fields": row.get("verified_core_fields", []),
        })
    return rows


def run(manifest, output, compare=None):
    records = json.loads(manifest.read_text(encoding="utf-8"))
    results = []
    # Importing Flask initializes its storage. Isolate that startup too.
    with tempfile.TemporaryDirectory(prefix="nutriscan-benchmark-") as temporary:
        config.UPLOAD_DIR = Path(temporary) / "uploads"
        config.PROCESSED_DIR = config.UPLOAD_DIR / "processed"
        config.HISTORY_PATH = Path(temporary) / "history.json"
        from app import _analyze_label

        knowledge = load_knowledge()
        seen = set()
        for record in records:
            path = ROOT / record["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            row = {**record, "sha256": digest}
            started = time.perf_counter()
            try:
                prepared = preprocess_image(path)
                ocr = recognize_text(prepared["processed"], prepared["original_gray"])
                analysis = _analyze_label(ocr["text"], [], knowledge, ocr)
                usable = comparable_nutrients(analysis["nutrients"])
                core = set(usable).intersection(config.SCORE_CORE_NUTRIENTS)
                if "salt" in usable:
                    core.add("sodium")
                row.update(
                    verified_core_count=len(core), verified_core_fields=sorted(core),
                    verified_fields=sorted({n["name"] for n in analysis["nutrients"] if n.get("verified")}),
                    score=analysis["health_score"], status=analysis["score_status"],
                    nutrients=analysis["nutrients"], ocr_attempts=ocr["attempts"],
                    mean_confidence=ocr["mean_confidence"],
                    first_median_word_height=ocr.get("first_median_word_height"),
                    retry_scale=ocr.get("retry_scale"),
                    preprocessing=prepared["diagnostics"],
                )
                if analysis["health_score"] is not None:
                    assert sum(n["points"] for n in analysis["score_breakdown"]) == analysis["health_score"]
            except Exception as exc:
                row.update(verified_core_count=None, error=f"{type(exc).__name__}: {exc}")
            row["seconds"] = round(time.perf_counter() - started, 3)
            results.append(row)
            print(f"{row['name']}: {row['verified_core_count']}/5; {row['seconds']}s", flush=True)
    report = {
        "analysis_version": config.ANALYSIS_VERSION,
        "count_definition": "Distinct comparable core nutrient fields admitted by the parser; not independently checked accuracy.",
        "manifest": manifest.name, "images": results,
    }
    if compare:
        report["comparison"] = comparison_rows(json.loads(compare.read_text(encoding="utf-8")), report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if compare:
        lines = ["# OCR before/after benchmark", "", report["count_definition"], "",
                 "| Image | Kind | Before /5 | After /5 | Change |", "|---|---|---:|---:|---:|"]
        for row in report["comparison"]:
            lines.append(f"| {row['name']} | {row['kind']} | {row['before']} | {row['after']} | {row['delta']} |")
        output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    run(args.manifest, args.output, args.compare)


if __name__ == "__main__":
    main()

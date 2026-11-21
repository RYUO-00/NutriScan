"""Download pinned official English Tesseract packs without changing system data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config


def install(name, directory=None):
    manifest = json.loads((config.BASE_DIR / "data/ocr/models.json").read_text(encoding="utf-8"))
    record = manifest[name]
    target = Path(directory or config.OCR_MODELS_DIR) / name / "eng.traineddata"
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == record["sha256"]:
        return target
    url = f"https://raw.githubusercontent.com/tesseract-ocr/{name}/{record['commit']}/eng.traineddata"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(record["bytes"] + 1)
    if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"The {name} download did not match the pinned file checksum.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".eng-", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", choices=["tessdata_best", "tessdata_fast", "tessdata"], default=["tessdata_best", "tessdata_fast"])
    args = parser.parse_args(argv)
    try:
        for name in args.models:
            print(install(name))
    except (OSError, ValueError) as exc:
        print(f"Model installation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""JSON persistence boundary for knowledge, scan history, and saved results."""

import json
import os
import tempfile
import threading
from pathlib import Path

import config
from scripts.validate_data import DataValidationError, read_records, validate_data


class StorageError(RuntimeError):
    """Persistence or knowledge-base failure with a user-safe message."""


HISTORY_LOCK = threading.Lock()
KNOWLEDGE_FILES = {
    "additives": "additives.json",
    "allergens": "allergens.json",
    "ingredient_flags": "ingredient_flags.json",
    "nutrition_limits": "nutrition_limits.json",
}


def load_knowledge():
    """Load and validate all knowledge arrays; fail clearly on bad startup data."""
    try:
        validate_data()
        knowledge = {key: read_records(filename) for key, filename in KNOWLEDGE_FILES.items()}
    except DataValidationError as exc:
        raise StorageError(f"NutriScan cannot start because its knowledge data is invalid: {exc}") from exc
    return knowledge


def initialize_history():
    """Create an empty local history array without resetting an existing file."""
    path = Path(config.HISTORY_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_LOCK:
            if path.exists():
                return
            try:
                with path.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write("[]\n")
            except FileExistsError:
                return
    except OSError as exc:
        raise StorageError(f"Scan history could not be initialized: {path}.") from exc


def _read_history_unlocked():
    path = Path(config.HISTORY_PATH)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            history = json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise StorageError(f"Scan history is malformed: {path}. Keep a backup and repair the JSON file.") from exc
    except OSError as exc:
        raise StorageError(f"Scan history could not be read: {path}.") from exc
    if not isinstance(history, list):
        raise StorageError(f"Scan history is malformed: {path} must contain a JSON array.")
    if any(not isinstance(item, dict) or not isinstance(item.get("scan_id"), str) for item in history):
        raise StorageError(f"Scan history is malformed: {path} must contain scan objects with string scan_id values.")
    return history


def get_history():
    with HISTORY_LOCK:
        return _read_history_unlocked()


def add_scan(scan):
    """Atomically append one scan under a process lock."""
    if not isinstance(scan, dict) or not isinstance(scan.get("scan_id"), str) or not scan["scan_id"]:
        raise StorageError("The scan could not be saved because its result identifier is missing.")
    path = Path(config.HISTORY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    with HISTORY_LOCK:
        history = _read_history_unlocked()
        history.append(scan)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(history, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
        except OSError as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise StorageError("The scan was processed but its history entry could not be saved. Check the local data folder permissions.") from exc
    return scan


def get_scan_by_id(scan_id):
    with HISTORY_LOCK:
        for scan in _read_history_unlocked():
            if scan.get("scan_id") == scan_id:
                return scan
    return None

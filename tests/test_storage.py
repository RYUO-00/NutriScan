import json

import pytest

import config
import storage
from storage import StorageError, add_scan, get_history, get_scan_by_id, initialize_history, load_knowledge


def test_load_knowledge_returns_all_four_json_datasets():
    knowledge = load_knowledge()
    assert set(knowledge) == {"additives", "allergens", "ingredient_flags", "nutrition_limits"}
    assert len(knowledge["additives"]) == 180


def test_missing_or_malformed_knowledge_stops_startup_with_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path)
    with pytest.raises(StorageError, match="additives.json"):
        load_knowledge()
    (tmp_path / "additives.json").write_text("{", encoding="utf-8")
    with pytest.raises(StorageError, match="additives.json"):
        load_knowledge()


def test_history_atomic_write_and_lookup(tmp_path, monkeypatch):
    history_path = tmp_path / "scan_history.json"
    monkeypatch.setattr(config, "HISTORY_PATH", history_path)
    replace_calls = []
    real_replace = storage.os.replace

    def record_replace(source, target):
        replace_calls.append((source, target))
        assert source.parent == target.parent
        return real_replace(source, target)

    monkeypatch.setattr(storage.os, "replace", record_replace)
    saved = add_scan({"scan_id": "scan-test-1", "health_score": 88})
    assert replace_calls and history_path.is_file()
    assert get_history() == [saved]
    assert get_scan_by_id("scan-test-1") == saved
    assert get_scan_by_id("missing") is None
    assert json.loads(history_path.read_text(encoding="utf-8")) == [saved]


def test_initialize_history_creates_empty_array_and_preserves_existing_file(tmp_path, monkeypatch):
    history_path = tmp_path / "data" / "scan_history.json"
    monkeypatch.setattr(config, "HISTORY_PATH", history_path)
    initialize_history()
    assert history_path.read_text(encoding="utf-8") == "[]\n"
    history_path.write_text("[{\"scan_id\":\"saved\"}]", encoding="utf-8")
    initialize_history()
    assert json.loads(history_path.read_text(encoding="utf-8")) == [{"scan_id": "saved"}]


def test_malformed_history_is_not_silently_reset(tmp_path, monkeypatch):
    history_path = tmp_path / "scan_history.json"
    history_path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(config, "HISTORY_PATH", history_path)
    with pytest.raises(StorageError, match="Scan history is malformed"):
        get_history()

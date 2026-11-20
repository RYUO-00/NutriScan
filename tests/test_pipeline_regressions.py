"""Known OCR transcripts exercise the real upload → analysis → saved report path."""

from io import BytesIO
import json

import pytest

import app as app_module
import config
from storage import add_scan


def panel(**overrides):
    rows = {"Total Fat": "1 g", "Saturated Fat": "0.1 g", "Trans Fat": "0 g", "Total Sugars": "1 g", "Sodium": "10 mg"}
    rows.update(overrides)
    return "Nutrition Information per 100 g\n" + "\n".join(f"{name} {value}" for name, value in rows.items())


CASES = [
    pytest.param(panel(**{"Total Sugars": "35 g"}), 85, "sufficient", {"sugar"}, id="01-high-sugar"),
    pytest.param(panel(**{"Saturated Fat": "8 g"}), 85, "sufficient", {"saturated_fat"}, id="02-high-saturated-fat"),
    pytest.param(panel(Sodium="900 mg"), 85, "sufficient", {"sodium"}, id="03-high-sodium"),
    pytest.param(panel(**{"Trans Fat": "3 g"}), 85, "sufficient", {"trans_fat"}, id="04-trans-fat"),
    pytest.param(panel(**{"Total Sugars": "35 g", "Saturated Fat": "8 g", "Trans Fat": "3 g", "Sodium": "900 mg"}), 40, "sufficient", {"sugar", "saturated_fat", "trans_fat", "sodium"}, id="05-multiple-concerns"),
    pytest.param("Nutrition Facts\nAll values unreadable\nTake another photo", None, "insufficient", set(), id="06-no-readable-nutrition"),
    pytest.param("Per 100 g\nTotal Sugars 35 g\nSodium ???\nTotal Fat 11q", 85, "provisional", {"sugar"}, id="07-incomplete-ocr"),
    pytest.param(panel(**{"Total Fat": "12 g", "Saturated Fat": "4 g", "Total Sugars": "8 g", "Sodium": "800 mg"}), 64, "sufficient", {"total_fat", "saturated_fat", "sugar", "sodium"}, id="08-nutrients-without-additives"),
    pytest.param("Ingredients: hazelnuts, skim milk\nContains: tree nuts", None, "insufficient", set(), id="09-hazelnuts-skim-milk-allergens"),
    pytest.param(panel() + "\nPotassium 170mg", 100, "sufficient", set(), id="10-potassium-is-not-additive"),
]


@pytest.fixture
def scan_client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(config, "PROCESSED_DIR", tmp_path / "uploads" / "processed")
    monkeypatch.setattr(config, "HISTORY_PATH", tmp_path / "data" / "history.json")
    return app_module.create_app({"TESTING": True}).test_client()


def upload_text(client, monkeypatch, text, *, confidence=94, selected=("Tree nut",)):
    monkeypatch.setattr(app_module, "recognize_text", lambda *_args: {
        "text": text, "mean_confidence": confidence, "retried": False,
        "attempt_count": 1, "psm": 6, "used_original": False, "attempts": [],
    })
    return client.post("/scan", data={
        "image": (BytesIO((config.SAMPLE_LABEL_DIR / "clear_flat.png").read_bytes()), "regression.png", "image/png"),
        "user_allergens": list(selected),
    }, content_type="multipart/form-data", headers={"Accept": "application/json"})


@pytest.mark.parametrize("text,expected_score,status,deducted", CASES)
def test_ten_label_pipeline_cases(scan_client, monkeypatch, text, expected_score, status, deducted):
    response = upload_text(scan_client, monkeypatch, text)
    assert response.status_code == 200
    result = response.get_json()
    assert result["raw_text"] == text
    assert result["health_score"] == expected_score
    assert result["score_status"] == status
    actual_deductions = {item["item"] for item in result["score_breakdown"] if item["category"] == "nutrient"}
    assert actual_deductions == deducted
    if expected_score is not None:
        assert sum(item["points"] for item in result["score_breakdown"]) == result["health_score"]
        assert result["score_totals"]["nutrient_deduction"] == sum(
            config.HIGH_NUTRIENT_DEDUCTION if item["status"] == "High" else config.MEDIUM_NUTRIENT_DEDUCTION
            for item in result["score_breakdown"] if item["category"] == "nutrient"
        )
    else:
        assert result["score_band"] is None
    if "hazelnuts" in text:
        alerts = {item["allergen_group"]: item for item in result["allergen_alerts"]}
        assert alerts["Tree nut"]["selected"] is True
        assert "hazelnut" in alerts["Tree nut"]["matched_keywords"]
        assert "tree nuts" in alerts["Tree nut"]["matched_keywords"]
        assert alerts["Milk"]["selected"] is False
    if "Potassium" in text:
        assert result["additives"] == []
        assert result["unknown_additive_codes"] == []
        assert next(item for item in result["nutrients"] if item["name"] == "sodium")["value"] == 10
    assert result["additives"] == []
    stored = scan_client.get(f"/api/history/{result['scan_id']}")
    assert stored.status_code == 200 and stored.get_json() == result
    reopened = scan_client.get(f"/history?scan_id={result['scan_id']}")
    assert reopened.status_code == 200
    html = reopened.get_data(as_text=True)
    assert "Data status: " + status.title() in html
    if expected_score is None:
        assert "Insufficient data" in html and 'aria-valuenow="100"' not in html
        assert "None / 100" not in html and "Good band" not in html
    else:
        assert f'class="score-value">{expected_score}</span>' in html
    assert "Informational screening only" in html
    for path in (result["image_path"], result["processed_image_path"]):
        assert scan_client.get("/" + path).status_code == 200
    summaries = scan_client.get("/api/history").get_json()
    assert summaries[0]["score_status"] == status
    assert summaries[0]["health_score"] == expected_score
    assert scan_client.get("/history").status_code == 200


def test_unknown_serving_basis_and_low_confidence_do_not_score(scan_client, monkeypatch):
    for text, confidence in (("Nutrition Facts per serving\nSugar 30 g", 94), (panel(**{"Total Sugars": "35 g"}), 12)):
        result = upload_text(scan_client, monkeypatch, text, confidence=confidence).get_json()
        assert result["health_score"] is None
        assert result["score_status"] == "insufficient"
        assert result["score_breakdown"] == []


def test_allergen_matching_survives_missing_section_headings(scan_client, monkeypatch):
    result = upload_text(scan_client, monkeypatch, "HAZELNUTS, SKIM MILK, TREE NUTS\nUnreadable nutrition").get_json()
    assert result["health_score"] is None
    assert {item["allergen_group"] for item in result["allergen_alerts"]} == {"Tree nut", "Milk"}
    html = scan_client.get(f"/history?scan_id={result['scan_id']}").get_data(as_text=True)
    assert "Selected allergen alerts" in html and "Also contains" in html


def test_selected_allergens_do_not_change_a_numeric_score(scan_client, monkeypatch):
    text = "Ingredients: hazelnuts, skim milk\n" + panel(**{"Total Sugars": "35 g"})
    selected = upload_text(scan_client, monkeypatch, text).get_json()
    unselected = upload_text(scan_client, monkeypatch, text, selected=()).get_json()
    assert selected["health_score"] == unselected["health_score"]
    assert selected["score_breakdown"] == unselected["score_breakdown"]
    assert any(item["selected"] for item in selected["allergen_alerts"])
    assert all(not item["selected"] for item in unselected["allergen_alerts"])


def test_explicit_tree_nut_group_works_without_an_individual_nut_name(scan_client, monkeypatch):
    result = upload_text(scan_client, monkeypatch, "Contains: tree nuts and milk").get_json()
    assert {item["allergen_group"] for item in result["allergen_alerts"]} == {"Tree nut", "Milk"}
    assert result["health_score"] is None


def test_legacy_history_is_reviewed_without_overwriting_original_data(scan_client):
    legacy = {
        "scan_id": "old-perfect", "health_score": 100, "score_band": "Good",
        "raw_text": "HAZELNUTS, SKIM MILK\nNutrition Facts\nTotal Fat 11g\nPotassium 170mg",
        "scanned_at": "2026-11-01T12:00:00+05:30", "image_name": "old.png",
        "image_path": "uploads/old.png", "processed_image_path": "uploads/processed/old.png",
        "user_allergens": ["Tree nut"], "score_breakdown": [{"category": "starting score", "points": 100}],
    }
    add_scan(legacy)
    before = config.HISTORY_PATH.read_bytes()
    result = scan_client.get("/api/history/old-perfect").get_json()
    assert result["health_score"] is None and result["score_status"] == "insufficient"
    assert result["previous_scoring"]["health_score"] == 100
    assert result["allergen_alerts"]
    assert result["unknown_additive_codes"] == []
    assert "stored label text" in result["score_review_note"]
    html = scan_client.get("/history?scan_id=old-perfect")
    assert html.status_code == 200 and b"Insufficient data" in html.data
    archive = scan_client.get("/history")
    assert archive.status_code == 200 and b"Insufficient data" in archive.data
    assert b"None" not in archive.data
    assert scan_client.get("/api/history").get_json()[0]["health_score"] is None
    assert config.HISTORY_PATH.read_bytes() == before
    assert json.loads(before)[0] == legacy

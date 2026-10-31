from io import BytesIO
from pathlib import Path

import pytest

import app as app_module
import config
from ocr import OCRNoTextError, OCRSetupError
from storage import StorageError


SAMPLE_TEXT = """Ingredients: whole wheat flour, rice flour, sugar, palm oil, salt, spices, soy lecithin (322), sodium benzoate (E 211)
Contains: Peanut, Milk
Nutrition Information per 100 g
Energy 425 kcal
Total fat 17 g
Saturated fat 5 g
Trans fat 0.1 g
Total sugars 12 g
Sodium 580 mg
Protein 7 g
Dietary fibre 4 g"""


@pytest.fixture
def client(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(config, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(config, "PROCESSED_DIR", upload_dir / "processed")
    monkeypatch.setattr(config, "HISTORY_PATH", tmp_path / "data" / "scan_history.json")
    monkeypatch.setattr(app_module, "recognize_text", lambda *_args: {
        "text": SAMPLE_TEXT, "mean_confidence": 91.5, "word_confidences": [91.5],
        "retried": False, "attempt_count": 1, "psm": 6, "used_original": False, "attempts": [],
    })
    return app_module.create_app({"TESTING": True}).test_client()


def _sample_bytes():
    return Path(config.SAMPLE_LABEL_DIR / "clear_flat.png").read_bytes()


def test_human_datetime_format_keeps_iso_fallback():
    assert app_module._human_datetime("2026-10-31T20:11:00+05:30") == "31 Oct 2026, 8:11 PM"
    assert app_module._human_datetime("unknown timestamp") == "unknown timestamp"


def test_scan_history_api_saved_result_and_result_page(client):
    assert client.get("/").status_code == 200
    assert b"Try a sample label" in client.get("/").data
    assert Path(config.HISTORY_PATH).read_text(encoding="utf-8") == "[]\n"
    assert client.get("/history").status_code == 200
    assert client.get("/api/history").get_json() == []

    response = client.post(
        "/scan",
        data={
            "image": (BytesIO(_sample_bytes()), "../../my snack label.png", "image/png"),
            "user_allergens": ["Peanut"],
        },
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    result = response.get_json()
    assert result["image_name"] == "my_snack_label.png"
    assert result["image_path"].startswith("uploads/scan_")
    assert result["processed_image_path"].startswith("uploads/processed/scan_")
    assert result["health_score"] < 100
    assert result["score_band"] in {"Good", "Moderate", "Poor"}
    additive_categories = {item["ins_code"]: item["category"] for item in result["additives"]}
    assert additive_categories["211"] == "Preservative"
    assert additive_categories["322"] == "Emulsifier"
    assert "sodium benzoate (E 211)" not in result["unrecognised_tokens"]
    assert any(item["allergen_group"] == "Peanut" and item["severity"] == "critical" for item in result["allergen_alerts"])
    assert any(item["name"] == "sodium" for item in result["nutrients"])
    assert result["starting_score"] == 100
    assert result["health_score"] == 68
    assert result["score_totals"] == {
        "additive_deduction": 6,
        "harmful_flag_deduction": 0,
        "nutrient_deduction": 28,
        "beneficial_credit": 2,
    }
    nutrient_status = {item["name"]: item["status"] for item in result["nutrients"]}
    assert nutrient_status["energy"] == "Informational"
    assert nutrient_status["protein"] == "Informational"
    assert nutrient_status["fibre"] == "Informational"
    assert not [
        item for item in result["score_breakdown"]
        if item["category"] == "nutrient" and item["item"] in {"energy", "protein", "fibre"}
    ]
    assert "not medical advice" in result["disclaimer"].lower()

    history = client.get("/api/history").get_json()
    assert len(history) == 1
    assert history[0]["scan_id"] == result["scan_id"]
    assert history[0]["scanned_at"] == result["scanned_at"]
    reopened = client.get(f"/api/history/{result['scan_id']}")
    assert reopened.status_code == 200
    assert reopened.get_json() == result
    page = client.get(f"/history?scan_id={result['scan_id']}")
    assert page.status_code == 200
    assert app_module._human_datetime(result["scanned_at"]).encode() in page.data
    assert b"Health Score" in page.data
    assert b"Sodium benzoate" in page.data
    assert b"Informational screening only" in page.data
    assert b'aria-label="Score before and after screening"' in page.data
    assert b"<dt>Before</dt>" in page.data
    assert b"<dt>After</dt>" in page.data
    assert b"How this was calculated and sources" in page.data
    assert page.data.count(b"Codex Alimentarius CXG 36-1989, functional class column.") == 1
    assert page.data.count(b"numeric values are defined only in config.py") == 1
    assert b"class=\"source-note\"" not in page.data
    page_html = page.get_data(as_text=True)
    comparison = page_html[page_html.index('<div class="comparison"'):page_html.index('Image comparison position')]
    labels_start = comparison.index('<div class="comparison-labels"')
    labels_end = comparison.index("</div>", labels_start) + len("</div>")
    viewport_start = comparison.index('<div class="comparison-viewport">')
    assert labels_end < viewport_start
    assert comparison.count('class="compare-caption ') == 2
    assert comparison.count('class="comparison-image') == 2
    assert 'id="comparison-slider"' in page_html
    critical_section = page_html.split('<section class="alert-section"', 1)[1].split("</section>", 1)[0]
    assert "Peanut" in critical_section
    assert "Milk" not in critical_section
    also_contains = page_html.split('<section class="also-contains-section"', 1)[1].split("</section>", 1)[0]
    assert "Milk" in also_contains
    assert "Wheat or Gluten" in also_contains


def test_unselected_detected_allergens_do_not_create_red_alert_section(client):
    response = client.post(
        "/scan",
        data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'class="alert-section"' not in page
    assert "Selected allergen alerts" not in page
    assert 'class="also-contains-section"' in page
    assert 'class="allergen-alert critical"' not in page
    assert "No allergen keywords detected" not in page


def test_no_allergen_matches_state_keeps_alerts_separate_from_score(client, monkeypatch):
    response = client.post(
        "/scan",
        data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    result = response.get_json()
    result["allergen_alerts"] = []
    monkeypatch.setattr(app_module, "get_scan_by_id", lambda _scan_id: result)

    page = client.get(f"/history?scan_id={result['scan_id']}").get_data(as_text=True)

    assert 'class="no-allergen-matches"' in page
    assert 'id="allergen-heading"' in page
    assert "No allergen keywords detected" in page
    assert 'class="alert-section"' not in page
    assert 'class="also-contains-section"' not in page


def test_current_pages_have_brand_metadata_and_keep_script_ids(client):
    scan_page = client.get("/").get_data(as_text=True)
    assert "<title>Read a food label | NutriScan</title>" in scan_page
    assert 'name="description" content="Upload a food-label photo' in scan_page
    assert 'property="og:title" content="Read a food label | NutriScan"' in scan_page
    assert 'property="og:description"' in scan_page
    assert 'alt="NutriScan label reader"' in scan_page
    assert "images/favicon.svg" in scan_page
    for element_id in ("main", "scan-form", "label-image", "preview-wrap", "preview", "preview-name", "allergen-chips", "sample-button", "scan-status", "scan-progress"):
        assert f'id="{element_id}"' in scan_page

    history_page = client.get("/history").get_data(as_text=True)
    assert "<title>Label history | NutriScan</title>" in history_page
    assert 'id="history-list"' in history_page

    result = client.post(
        "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png"), "user_allergens": ["Peanut"]},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    for element_id in ("allergen-heading", "also-contains-heading", "score-heading", "nutrient-heading", "additive-heading", "flags-heading", "raw-ocr", "comparison-heading", "comparison-slider", "comparison-help", "detected-findings"):
        assert f'id="{element_id}"' in result
    assert "<title>Scan result | NutriScan</title>" in result
    assert 'property="og:description"' in result


def test_scan_progress_reports_real_pipeline_stages(client, monkeypatch):
    progress_id = "12345678123456781234567812345678"
    stages = []
    original_record = app_module._record_scan_progress

    def record(progress_key, stage):
        if progress_key == progress_id:
            stages.append(stage)
        original_record(progress_key, stage)

    monkeypatch.setattr(app_module, "_record_scan_progress", record)
    response = client.post(
        "/scan",
        data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png"), "progress_id": progress_id},
        content_type="multipart/form-data",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )
    assert response.status_code == 200
    assert stages == ["uploading", "preprocessing", "reading_text", "decoding", "nutrition", "scoring", "saving", "complete"]
    assert client.get(f"/api/scan-progress/{progress_id}").get_json() == {"stage": "complete"}
    assert client.get("/api/scan-progress/not-a-uuid").status_code == 404
    javascript = client.get("/static/js/app.js").get_data(as_text=True)
    assert "/api/scan-progress/" in javascript
    assert "setInterval" not in javascript


def test_fresh_result_html_keeps_developer_sources_in_collapsible_section(client):
    response = client.post(
        "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    source_start = page.index('<details class="source-details">')
    source_end = page.index("</details>", source_start) + len("</details>")
    sources = page[source_start:source_end]
    outside_sources = page[:source_start] + page[source_end:]

    assert "How this was calculated and sources" in sources
    assert "Project assumption" in sources
    assert "numeric values are defined only in config.py" in sources
    assert "Project assumption" not in outside_sources
    assert "config.py" not in outside_sources
    assert "configured" not in outside_sources.casefold()
    assert page.count('<span class="informational-text">Informational</span>') == 3
    assert 'class="status status-informational"' not in page
    assert '<ul class="finding-list compact-list">' not in page
    assert page.count('<ul class="finding-list">') >= 2


def test_comparison_layout_has_a_sized_shared_frame_and_mobile_stack(client):
    response = client.get("/static/css/style.css?v=20261031-2")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    assert ".comparison { --split: 50%; position: relative;" in css
    assert "aspect-ratio: 1.58; max-height: 620px; min-height: 340px; overflow: clip;" in css
    assert ".comparison-viewport { position: relative; width: 100%; height: 100%;" in css
    assert ".comparison { height: 480px; min-height: 0; aspect-ratio: auto;" in css
    assert "grid-template-rows: var(--split) calc(100% - var(--split));" in css
    assert ".original-image { grid-row: 1; }" in css
    assert ".processed-image { grid-row: 2; clip-path: none; }" in css


@pytest.mark.parametrize(
    "data,status,message",
    [
        ({}, 400, "Choose a JPG or PNG"),
        ({"image": (BytesIO(b"gif"), "label.gif", "image/gif")}, 400, "Unsupported file type"),
        ({"image": (BytesIO(b""), "empty.png", "image/png")}, 400, "image is empty"),
        ({"image": (BytesIO(b"not an image"), "fake.png", "image/png")}, 400, "could not be decoded"),
        ({"image": (BytesIO(b"\x89PNG\r\n\x1a\n"), "wrong.jpg", "image/png")}, 400, "extension and image MIME type do not match"),
        ({"image": (BytesIO(b"x" * (config.MAX_CONTENT_LENGTH + 1)), "large.png", "image/png")}, 413, "larger than the 5 MB"),
    ],
)
def test_upload_validation_failures_are_specific(client, data, status, message):
    response = client.post("/scan", data=data, content_type="multipart/form-data", headers={"Accept": "application/json"})
    assert response.status_code == status
    assert message.lower() in response.get_json()["error"].lower()


def test_tesseract_and_unreadable_text_failures_are_friendly(client, monkeypatch):
    for error, status in ((OCRSetupError("Install Tesseract 5 with English data."), 503), (OCRNoTextError("No readable label text was found."), 422)):
        monkeypatch.setattr(app_module, "recognize_text", lambda *_args, exc=error: (_ for _ in ()).throw(exc))
        response = client.post(
            "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
            content_type="multipart/form-data", headers={"Accept": "application/json"},
        )
        assert response.status_code == status
        assert response.get_json()["error"] == str(error)


def test_failed_history_write_cleans_saved_images(client, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "add_scan", lambda _scan: (_ for _ in ()).throw(StorageError("History write failed clearly.")))
    response = client.post(
        "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data", headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.get_json()["error"] == "History write failed clearly."
    assert list((tmp_path / "uploads").rglob("scan_*")) == []


def test_unexpected_scan_failure_is_friendly_and_cleans_images(client, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "_run_pipeline", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal detail")))
    response = client.post(
        "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data", headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert "could not complete this scan" in response.get_json()["error"].lower()
    assert "internal detail" not in response.get_data(as_text=True)
    assert list((tmp_path / "uploads").rglob("scan_*")) == []


def test_malformed_history_and_all_404_routes_are_friendly(client, tmp_path, monkeypatch):
    history_path = config.HISTORY_PATH
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text("{bad", encoding="utf-8")
    response = client.get("/api/history")
    assert response.status_code == 500
    assert "history is malformed" in response.get_json()["error"].lower()
    history_path.write_text("[]", encoding="utf-8")
    assert client.get("/api/history/missing").status_code == 404
    assert client.get("/missing").status_code == 404


def test_sample_image_is_served_locally_without_cdn(client):
    response = client.get("/static/images/sample_label.png")
    assert response.status_code == 200
    assert response.mimetype == "image/png"


def test_unselected_detected_allergens_never_create_red_banner(client):
    response = client.post(
        "/scan", data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<section class="alert-section"' not in page
    assert 'class="allergen-alert critical"' not in page
    assert '<section class="also-contains-section"' in page
    assert "Also contains" in page

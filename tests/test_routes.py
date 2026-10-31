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
    assert b"Before screening:" in page.data
    assert b"After screening:" in page.data
    assert b"How this was calculated and sources" in page.data
    assert page.data.count(b"Codex Alimentarius CXG 36-1989, functional class column.") == 1
    assert page.data.count(b"numeric values are defined only in config.py") == 1
    assert b"class=\"source-note\"" not in page.data
    page_html = page.get_data(as_text=True)
    assert "<title>Your scan result · NutriScan</title>" in page_html
    assert 'property="og:title" content="Your scan result · NutriScan"' in page_html
    for hook in ("allergen-heading", "also-contains-heading", "nutrient-heading", "additive-heading", "flags-heading", "score-heading", "comparison-heading", "comparison-slider", "comparison-help", "raw-ocr", "detected-findings"):
        assert f'id="{hook}"' in page_html
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


def test_scan_progress_endpoint_tracks_actual_processing_stages(client):
    progress_id = "sample-progress-run"
    response = client.post(
        "/scan",
        data={"image": (BytesIO(_sample_bytes()), "label.png", "image/png"), "progress_id": progress_id},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    progress = client.get(f"/api/scan-progress/{progress_id}")
    assert progress.status_code == 200
    assert progress.get_json()["stages"] == [
        "uploading", "preprocessing", "reading_text", "decoding", "nutrition", "scoring", "saving", "complete"
    ]


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
    assert "*[hidden] { display: none !important; }" in css
    assert ".raw-text .section-main { margin: 13px 0 3px 168px; }" in css
    assert ".comparison { --split: 50%; position: relative;" in css
    assert "aspect-ratio: 1.58; max-height: 600px; min-height: 300px;" in css
    assert ".comparison-viewport { position: relative; width: 100%; min-width: 0; min-height: 0;" in css
    assert ".comparison { height: 465px; min-height: 0; aspect-ratio: auto; grid-template-rows: 34px minmax(0,1fr); }" in css
    assert "grid-template-rows: var(--split) calc(100% - var(--split));" in css
    assert ".original-image { grid-row: 1; }" in css
    assert ".processed-image { grid-row: 2; clip-path: none; border-top: 1px solid var(--rule-heavy); }" in css


def test_page_metadata_logo_and_existing_ui_hooks(client):
    scan_page = client.get("/").get_data(as_text=True)
    history_page = client.get("/history").get_data(as_text=True)
    error_page = client.get("/missing").get_data(as_text=True)
    assert "<title>Scan a food label · NutriScan</title>" in scan_page
    assert "<title>Scan history · NutriScan</title>" in history_page
    assert "<title>Scan unavailable · NutriScan</title>" in error_page
    assert 'property="og:title" content="Scan a food label · NutriScan"' in scan_page
    assert 'property="og:title" content="Scan history · NutriScan"' in history_page
    assert 'property="og:title" content="Scan unavailable · NutriScan"' in error_page
    assert 'property="og:description"' in scan_page
    assert 'property="og:image"' in scan_page
    assert 'src="/static/images/logo.svg"' in scan_page
    assert 'href="/static/images/favicon.svg"' in scan_page
    assert 'href="/static/images/favicon.png"' in scan_page
    assert client.get("/static/images/logo.svg").status_code == 200
    assert client.get("/static/images/favicon.svg").status_code == 200
    assert client.get("/static/images/favicon.png").mimetype == "image/png"
    assert client.get("/static/images/nutriscan-social.png").mimetype == "image/png"
    for hook in ("scan-form", "label-image", "preview-wrap", "preview", "preview-name", "allergen-chips", "sample-button", "scan-status", "scan-progress"):
        assert f'id="{hook}"' in scan_page
    assert 'id="history-list"' in history_page
    script = client.get("/static/js/app.js?v=20261031-impeccable").get_data(as_text=True)
    assert "/api/scan-progress/" in script
    assert "setInterval(updateStage" not in script
    assert "mark.tabIndex = 0" in script


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
    monkeypatch.setattr(app_module, "_run_pipeline", lambda *_args: (_ for _ in ()).throw(RuntimeError("internal detail")))
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

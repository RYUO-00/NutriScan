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
    scan_page = client.get("/")
    assert scan_page.status_code == 200
    assert b"Try a sample label" in scan_page.data
    assert b"Find the detail that matters." in scan_page.data
    for element_id in ("main", "scan-form", "label-image", "preview-wrap", "preview", "preview-name", "allergen-chips", "sample-button", "scan-status", "scan-progress"):
        assert f'id="{element_id}"'.encode() in scan_page.data
    assert b"capture=\"environment\"" in scan_page.data
    assert scan_page.data.count(b"data-stage=") == len(app_module.SCAN_PROGRESS_STAGES)
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
    original_image = client.get(f"/uploads/{result['image_path'][8:]}")
    processed_image = client.get(f"/uploads/{result['processed_image_path'][8:]}")
    assert original_image.status_code == 200
    assert original_image.mimetype == "image/png"
    assert original_image.get_data() == _sample_bytes()
    assert processed_image.status_code == 200
    assert processed_image.mimetype == "image/png"
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
    score_summary = app_module._score_summary(result)
    assert score_summary == {
        "starting_score": result["starting_score"],
        "deductions": 34,
        "credits": 2,
        "adjustment": 0,
        "final_score": result["health_score"],
    }
    assert score_summary["starting_score"] - score_summary["deductions"] + score_summary["credits"] + score_summary["adjustment"] == score_summary["final_score"]
    assert app_module._score_waterfall(score_summary) == [
        {"label": "Starting score", "points": 100, "kind": "total", "start": 0, "width": 100},
        {"label": "Total deductions", "points": -34, "kind": "down", "start": 66, "width": 34},
        {"label": "Total credits", "points": 2, "kind": "up", "start": 66, "width": 2},
        {"label": "Final score", "points": 68, "kind": "total", "start": 0, "width": 68},
    ]
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
    assert b"Your label analysis" in page.data
    assert b'class="result-file">my_snack_label.png</p>' in page.data
    assert b'class="score-value">68</span><span class="score-total">/ 100</span>' in page.data
    assert f'<span>Starting score:</span><strong>{result["starting_score"]}</strong>'.encode() in page.data
    assert f'<span>Final score:</span><strong>{result["health_score"]}</strong>'.encode() in page.data
    assert f'class="score-band">{result["score_band"]}</span>'.encode() in page.data
    assert "Poor</strong><small>0–49".encode() in page.data
    assert "Moderate</strong><small>50–79".encode() in page.data
    assert "Good</strong><small>80–100".encode() in page.data
    assert "Total deductions</span><strong>−34".encode() in page.data
    assert "Total credits</span><strong>+2".encode() in page.data
    assert "Final score</span><strong>68 / 100".encode() in page.data
    assert b'class="score-waterfall"' in page.data
    assert b'class="score-waterfall-row" data-kind="down"' in page.data
    assert b"--bar-start: 66%; --bar-width: 34%" in page.data
    assert b"Individual contributions, reasons, and running balances:" in page.data
    assert b"Sodium benzoate" in page.data
    assert b"Informational screening only" in page.data
    assert b"Starting" in page.data
    assert b"Final" in page.data
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
    for element_id in ("allergen-heading", "also-contains-heading", "nutrient-heading", "additive-heading", "flags-heading", "score-heading", "comparison-heading", "comparison-slider", "comparison-help", "raw-ocr", "detected-findings"):
        assert f'id="{element_id}"' in page_html
    assert "data-image-fallback" in page_html
    assert "Balance<strong>68</strong>" in page_html
    critical_section = page_html.split('<section class="alert-section"', 1)[1].split("</section>", 1)[0]
    assert "Peanut" in critical_section
    assert "Milk" not in critical_section
    also_contains = page_html.split('<section class="also-contains-section"', 1)[1].split("</section>", 1)[0]
    assert "Milk" in also_contains
    assert "Wheat or Gluten" in also_contains


def test_scan_progress_api_reports_the_backend_stages_and_completion(client):
    progress_id = "8c965746168d4b7fb4cd53a113f873c5"
    response = client.post(
        "/scan",
        data={
            "image": (BytesIO(_sample_bytes()), "label.png", "image/png"),
            "progress_id": progress_id,
        },
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200

    progress_response = client.get(f"/api/scan-progress/{progress_id}")
    assert progress_response.status_code == 200
    progress = progress_response.get_json()
    assert progress["state"] == "complete"
    assert progress["active_stage"] is None
    assert progress["completed_stages"] == list(app_module.SCAN_PROGRESS_STAGES)
    assert progress["error"] is None


def test_scan_progress_api_rejects_invalid_and_unknown_ids(client):
    assert client.get("/api/scan-progress/not-a-uuid").status_code == 400
    unknown_progress_id = app_module.uuid.uuid4().hex
    assert client.get(f"/api/scan-progress/{unknown_progress_id}").status_code == 404


def test_history_archive_reopens_scans_and_distinguishes_selected_allergens(client):
    responses = []
    for selected in ([], ["Peanut"]):
        form = {"image": (BytesIO(_sample_bytes()), "label.png", "image/png")}
        if selected:
            form["user_allergens"] = selected
        responses.append(client.post(
            "/scan", data=form, content_type="multipart/form-data", headers={"Accept": "application/json"},
        ))
    assert all(response.status_code == 200 for response in responses)

    history = client.get("/history")
    assert history.status_code == 200
    html = history.get_data(as_text=True)
    assert 'id="history-list"' in html
    assert html.count('class="history-row"') == 2
    assert "Open saved result" in html
    assert "detected" in html
    assert "selected allergen alert" in html
    assert 'class="archive-alert selected"' in html
    assert 'class="archive-alert other"' in html
    assert 'class="archive-thumb-image"' in html
    for response in responses:
        assert f"/history?scan_id={response.get_json()['scan_id']}" in html

    # The selected scan's saved report is reopened directly, without rerunning OCR.
    saved = client.get("/api/history").get_json()
    for item in saved:
        reopened = client.get(f"/history?scan_id={item['scan_id']}")
        assert reopened.status_code == 200
        assert app_module._human_datetime(item["scanned_at"]).encode() in reopened.data


def test_history_empty_state_explains_how_to_start(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Your scan archive starts here." in response.data
    assert b"Scan a label" in response.data


def test_history_mobile_grid_keeps_product_clear_of_score(client):
    css = client.get("/static/css/style.css?v=20261101-9").get_data(as_text=True)
    assert ".archive-date { color: var(--muted); font: .75rem/1.35 var(--mono); white-space: nowrap; }" in css
    assert ".archive-score { grid-column: 2; grid-row: 1; align-self: center; }" in css


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
    assert page.count('class="nutrient-state informational-text">Context only</span>') == 3
    assert 'class="status status-informational"' not in page
    assert '<ul class="finding-list compact-list">' not in page
    assert page.count('<ul class="finding-list finding-grid">') == 2
    assert "Protein" in page and "Fibre" in page and "Energy" in page
    assert "Status: Medium" not in page
    assert 'class="nutrient-name">Fibre' in page and 'class="nutrient-name">Protein' in page
    assert "Score breakdown" in page and "running total" in page.casefold()
    assert 'class="allergen-alert critical"' not in page


def test_comparison_layout_has_a_sized_shared_frame_and_mobile_stack(client):
    response = client.get("/static/css/style.css?v=20261101-8")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    assert ".comparison { --split: 50%; position: relative; display: grid; grid-template-rows: 42px auto;" in css
    assert ".comparison-viewport { width: 100%; height: min(725px, calc((100vw - 48px) * 0.625)); min-width: 0; min-height: 0; position: relative; aspect-ratio: 16 / 10;" in css
    assert ".comparison-labels { display: flex; align-items: center; justify-content: space-between;" in css
    assert ".comparison-panel { position: absolute; inset: 0; display: grid; width: 100%; height: 100%; place-items: center;" in css
    assert ".comparison .comparison-viewport { height: 510px; aspect-ratio: auto; display: grid;" in css
    assert "grid-template-rows: var(--split) calc(100% - var(--split));" in css
    assert ".comparison .original-panel { grid-row: 1; }" in css
    assert ".comparison .processed-panel { grid-row: 2; clip-path: none;" in css


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


def test_frontend_routes_are_generated_without_host_specific_urls(client):
    scan_page = client.get("/").get_data(as_text=True)
    assert 'class="brand" href="/"' in scan_page
    assert 'href="/history"' in scan_page
    assert 'action="/scan"' in scan_page
    assert 'data-progress-url="/api/scan-progress/__progress_id__"' in scan_page
    assert 'data-result-url="/history?scan_id=__scan_id__"' in scan_page
    assert 'data-sample-url="/static/images/sample_label.png"' in scan_page

    frontend_sources = [
        *Path(app_module.__file__).with_name("templates").glob("*.html"),
        Path(app_module.__file__).with_name("static") / "js" / "app.js",
        Path(app_module.__file__).with_name("static") / "css" / "style.css",
    ]
    forbidden_host_literals = ("127.0.0.1", "localhost", "0.0.0.0")
    for source_path in frontend_sources:
        source = source_path.read_text(encoding="utf-8").casefold()
        assert not any(host_literal in source for host_literal in forbidden_host_literals), source_path


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

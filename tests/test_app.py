
from app import create_app
import app as app_module
import config
import pytest
from scoring import calculate_health_score
from nutrition import parse_nutrition
from storage import load_knowledge


def test_scan_page_and_history_page_render():
    client = create_app({"TESTING": True}).test_client()
    assert client.get("/").status_code == 200
    assert client.get("/history").status_code == 200


def test_unknown_page_is_friendly_404():
    response = create_app({"TESTING": True}).test_client().get("/not-a-page")
    assert response.status_code == 404
    assert b"not found" in response.data.lower()


@pytest.mark.parametrize(
    ("arguments", "expected_host", "shows_warning"),
    [([], "127.0.0.1", False), (["--lan"], "0.0.0.0", True)],
)
def test_startup_modes_keep_port_and_debug_settings(monkeypatch, capsys, arguments, expected_host, shows_warning):
    calls = []
    monkeypatch.setattr(app_module.app, "run", lambda **kwargs: calls.append(kwargs))

    app_module.main(arguments)

    assert calls == [{
        "host": expected_host,
        "port": 5000,
        "debug": False,
        "use_reloader": False,
    }]
    terminal = capsys.readouterr()
    if shows_warning:
        assert "WARNING" in terminal.err
        assert "other devices" in terminal.err
        assert "trusted private network" in terminal.err
    else:
        assert terminal.err == ""


def test_score_summary_reconciles_engine_range_clamp():
    engine_result = calculate_health_score(
        additives=[{"ins_code": str(index), "risk_level": "high"} for index in range(10)],
        ingredient_flags=[{"keyword": f"harmful-{index}", "flag_type": "harmful"} for index in range(8)],
        nutrients=parse_nutrition("Per 100 g\nTotal Fat 25 g\nSaturated Fat 8 g\nTrans Fat 3 g\nSugar 30 g\nSodium 900 mg"),
    )
    summary = app_module._score_summary({
        "starting_score": config.STARTING_SCORE,
        "health_score": engine_result["health_score"],
        "score_breakdown": engine_result["score_breakdown"],
    })

    assert summary["deductions"] == 165
    assert summary["credits"] == 0
    assert summary["adjustment"] == 65
    assert summary["starting_score"] - summary["deductions"] + summary["credits"] + summary["adjustment"] == summary["final_score"] == 0
    waterfall = app_module._score_waterfall(summary)
    assert waterfall[-2]["kind"] == "cap"
    assert waterfall[-2]["points"] == 65
    assert waterfall[-1]["label"] == "Final score"
    assert waterfall[-1]["points"] == 0


def test_score_ranges_follow_configured_score_bands():
    assert app_module._score_ranges() == [
        {"label": "Poor", "lower": 0, "upper": 49, "width": 50},
        {"label": "Moderate", "lower": 50, "upper": 79, "width": 30},
        {"label": "Good", "lower": 80, "upper": 100, "width": 20},
    ]


def test_panel_retry_preserves_whole_page_allergens_and_score_ledger():
    raw = "Ingredients: wheat flour, peanut\nContains: peanut\nNutrition Facts\nSugar unreadable"
    panel = "Nutrition per 100g\nTotal Fat 1g\nSaturated Fat 0.2g\nSugar 35g\nSodium 10mg"
    result = app_module._analyze_label(raw, ["Peanut"], load_knowledge(), {
        "mean_confidence": 90,
        "nutrition_ocr": {"text": panel, "mean_confidence": 95, "lines": []},
    })
    assert result["health_score"] == 87  # Sugar deduction and existing wheat-flour credit.
    assert sum(item["points"] for item in result["score_breakdown"]) == result["health_score"]
    assert any(alert["allergen_group"] == "Peanut" and alert["selected"] for alert in result["allergen_alerts"])
    assert result["raw_text"] == raw and "Sugar 35g" in result["nutrition_text"]
    assert result["data_completeness"]["ocr_mean_confidence"] == 95


@pytest.mark.parametrize("raw, warning", [
    ("Nutrition per 100g\n30g serving with\n200 ml COW'S MILK\nSugar unreadable", False),
    ("Nutrition per 100g\nSugar unreadable", True),
])
def test_panel_cannot_erase_whole_page_preparation_warning(raw, warning):
    result = app_module._analyze_label(raw, [], load_knowledge(), {
        "mean_confidence": 95, "prepared_columns": warning,
        "nutrition_ocr": {"text": "Nutrition per 100g\nTotal Fat 93g", "mean_confidence": 95},
    })
    assert result["health_score"] is None
    assert result["score_status"] == "insufficient"
    assert all(not row["verified"] for row in result["nutrients"])
    assert "prepared-food column" in result["nutrients"][0]["reason"]

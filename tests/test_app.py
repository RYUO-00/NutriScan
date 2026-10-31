from app import create_app


def test_scan_page_and_history_page_render():
    client = create_app({"TESTING": True}).test_client()
    assert client.get("/").status_code == 200
    assert client.get("/history").status_code == 200


def test_unknown_page_is_friendly_404():
    response = create_app({"TESTING": True}).test_client().get("/not-a-page")
    assert response.status_code == 404
    assert b"not found" in response.data.lower()

from scripts.benchmark_ocr import comparison_rows


def test_benchmark_compares_identical_image_bytes_and_does_not_hide_errors():
    before = {"images": [{"sha256": "same", "verified_core_count": 1, "verified_core_fields": ["sugar"]},
                         {"sha256": "old", "verified_core_count": 5}]}
    after = {"images": [{"sha256": "same", "name": "photo", "verified_core_count": 3,
                         "verified_core_fields": ["sugar", "sodium", "total_fat"]},
                        {"sha256": "new", "name": "changed photo", "verified_core_count": 5},
                        {"sha256": "error", "name": "failed photo", "verified_core_count": None}]}
    rows = comparison_rows(before, after)
    assert rows[0]["before"] == 1 and rows[0]["after"] == 3 and rows[0]["delta"] == 2
    assert rows[1]["before"] is None and rows[1]["delta"] is None
    assert rows[2]["after"] is None and rows[2]["delta"] is None

from pathlib import Path

from scripts.validate_data import EXPECTED_COUNTS, read_records, validate_data


def test_knowledge_files_meet_target_counts_and_review_queue():
    assert validate_data() == EXPECTED_COUNTS


def test_additive_functional_classes_are_specific_or_queued_for_review():
    records = read_records("additives.json")
    by_code = {item["ins_code"]: item for item in records}
    assert by_code["211"]["category"] == "Preservative"
    assert by_code["322"]["category"] == "Emulsifier"
    for item in records:
        assert item["category_source"]
        if item["category_review_reason"]:
            assert item["category"] == "Class under review"
        else:
            assert " or " not in item["category"].casefold()

    review_text = Path("DATA_REVIEW.md").read_text(encoding="utf-8")
    unresolved = [item for item in records if item["category_review_reason"]]
    assert len(unresolved) == 12
    for item in unresolved:
        assert f"INS {item['ins_code']} {item['name']}" in review_text


def test_caution_flags_have_distinct_label_specific_reasons():
    flags = [item for item in read_records("ingredient_flags.json") if item["flag_type"] == "caution"]
    reasons = [item["reason"] for item in flags]
    assert len(flags) == 40
    assert len(reasons) == len(set(reasons))
    assert all(reason.endswith(".") and len(reason.split()) >= 8 for reason in reasons)
    by_keyword = {item["keyword"]: item["reason"] for item in flags}
    assert "ingredient list" in by_keyword["sugar"].lower()
    assert "specific oil" in by_keyword["edible vegetable oil"].lower()
    assert "sodium" not in by_keyword["salt"].lower()

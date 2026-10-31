import config
from matcher import decode_additives, match_allergens, match_ingredient_tokens, normalize_additive_code
from storage import load_knowledge


def test_additive_code_formats_subcodes_unknowns_and_contextual_bare_number():
    knowledge = load_knowledge()
    text = "E211, E 211, E-211, INS211, INS 211, E160a(i), 150d, Preservative (211), E999, and package 211 g"
    decoded, unknown = decode_additives(text, knowledge["additives"])
    codes = {item["ins_code"] for item in decoded}
    assert {"211", "160ai", "150d"}.issubset(codes)
    assert next(item for item in decoded if item["ins_code"] == "211")["source_spans"]
    assert normalize_additive_code("E 160a(i)") == "160ai"
    assert normalize_additive_code("INS-211") == "211"
    assert [item["code"] for item in unknown] == ["999"]
    # Bare 211 inside a recognized additive-class bracket is accepted; the trailing mass is not.
    assert len(next(item for item in decoded if item["ins_code"] == "211")["source_spans"]) == 6


def test_exact_synonym_then_fuzzy_and_threshold():
    additives = [{"id": 1, "ins_code": "211", "name": "Sodium Benzoate", "synonyms": ["benzoate of soda"]}]
    flags = [{"id": 1, "keyword": "whole wheat flour", "flag_type": "beneficial"}]
    matched_additives, matched_flags, unknown = match_ingredient_tokens(
        ["whole wheat flour", "benzoate of soda", "sodum benzoate", "unknown flour"], additives, flags
    )
    assert [item["match_type"] for item in matched_additives] == ["synonym", "fuzzy"]
    assert [item["match_type"] for item in matched_flags] == ["exact"]
    assert unknown == ["unknown flour"]
    _additives, _flags, strict_unknown = match_ingredient_tokens(
        ["sodum benzoate"], additives, flags, fuzzy_threshold=100
    )
    assert strict_unknown == ["sodum benzoate"]


def test_known_additive_name_matches_when_code_is_parenthetical():
    additives = [{"id": 1, "ins_code": "322", "name": "Lecithins", "synonyms": ["soy lecithin"]}]
    matched, flags, unknown = match_ingredient_tokens(["soy lecithin (322)"], additives, [])
    assert flags == []
    assert unknown == []
    assert matched[0]["ins_code"] == "322"
    assert matched[0]["matched_token"] == "soy lecithin (322)"


def test_allergen_groups_selected_alerts_and_context_dependent_lecithin():
    knowledge = load_knowledge()
    alerts = match_allergens(
        "wheat flour, soy lecithin, cashew, cocoa butter, lecithin",
        "Contains peanut and milk",
        knowledge["allergens"],
        ["Milk", "Peanut"],
    )
    by_group = {item["allergen_group"]: item for item in alerts}
    assert set(by_group) == {"Wheat or Gluten", "Soy", "Tree nut", "Peanut", "Milk"}
    assert by_group["Milk"]["severity"] == "critical"
    assert by_group["Peanut"]["severity"] == "critical"
    assert by_group["Soy"]["selected"] is False
    assert "soy lecithin" in by_group["Soy"]["matched_keywords"]


def test_unqualified_lecithin_is_not_an_allergen_match():
    knowledge = load_knowledge()
    assert match_allergens("lecithin", "", knowledge["allergens"]) == []

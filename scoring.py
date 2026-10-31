"""Configured, explainable Health Score heuristic."""

import config


def _unique(items, key_names):
    seen = set()
    result = []
    for item in items:
        identity = next((item.get(key) for key in key_names if item.get(key) is not None), None)
        identity = identity if identity is not None else item.get("name", item.get("keyword"))
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
    return result


def _band(score):
    for lower_bound, label in config.SCORE_BANDS:
        if score >= lower_bound:
            return label
    return "Poor"


def calculate_health_score(additives=None, ingredient_flags=None, nutrients=None):
    """Return score, band, totals, and a reason for every applied contribution."""
    additives = _unique(additives or [], ("ins_code", "id"))
    ingredient_flags = _unique(ingredient_flags or [], ("id", "keyword"))
    nutrients = nutrients or []
    breakdown = [{"category": "starting score", "item": "Starting value", "points": config.STARTING_SCORE, "reason": "The score begins at the configured project value."}]
    additive_used = 0
    harmful_used = 0
    benefit_used = 0
    nutrient_seen = set()

    for additive in additives:
        risk = str(additive.get("risk_level", "low")).casefold()
        raw = config.ADDITIVE_DEDUCTIONS.get(risk, config.ADDITIVE_DEDUCTIONS["low"])
        applied = min(raw, max(0, config.ADDITIVE_DEDUCTION_CAP - additive_used))
        additive_used += applied
        breakdown.append({
            "category": "additive",
            "item": additive.get("name", additive.get("ins_code", "Recognized additive")),
            "points": -applied,
            "reason": additive.get("reason", "Screening deduction from the configured additive category."),
            "risk_level": risk,
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The configured total additive deduction cap was reached."

    for flag in ingredient_flags:
        if flag.get("flag_type") != "harmful":
            continue
        raw = config.HARMFUL_FLAG_DEDUCTION
        applied = min(raw, max(0, config.HARMFUL_FLAG_DEDUCTION_CAP - harmful_used))
        harmful_used += applied
        breakdown.append({
            "category": "ingredient flag",
            "item": flag.get("keyword", "Flagged ingredient"),
            "points": -applied,
            "reason": flag.get("reason", "Configured harmful-flag deduction."),
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The configured harmful-flag deduction cap was reached."

    for nutrient in nutrients:
        key = nutrient.get("name")
        if key in config.INFORMATIONAL_NUTRIENTS:
            continue
        if key in nutrient_seen or nutrient.get("status") not in {"High", "Medium"}:
            continue
        nutrient_seen.add(key)
        if nutrient.get("status") == "High":
            points = config.HIGH_NUTRIENT_DEDUCTION
        else:
            points = config.MEDIUM_NUTRIENT_DEDUCTION
        breakdown.append({
            "category": "nutrient",
            "item": key,
            "points": -points,
            "reason": nutrient.get("reason", f"{nutrient.get('status')} screening status on a comparable value."),
            "status": nutrient["status"],
        })

    for flag in ingredient_flags:
        if flag.get("flag_type") != "beneficial":
            continue
        raw = config.BENEFICIAL_FLAG_BONUS
        applied = min(raw, max(0, config.BENEFICIAL_FLAG_BONUS_CAP - benefit_used))
        benefit_used += applied
        breakdown.append({
            "category": "ingredient flag",
            "item": flag.get("keyword", "Beneficial ingredient"),
            "points": applied,
            "reason": flag.get("reason", "Configured beneficial-ingredient credit."),
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The configured beneficial credit cap was reached."

    raw_score = sum(item["points"] for item in breakdown)
    score = max(0, min(100, raw_score))
    if score != raw_score:
        breakdown.append({
            "category": "clamp",
            "item": "Score range",
            "points": score - raw_score,
            "reason": "The score is clamped to the configured 0 to 100 range.",
        })
    return {
        "health_score": score,
        "score_band": _band(score),
        "score_breakdown": breakdown,
        "totals": {
            "additive_deduction": additive_used,
            "harmful_flag_deduction": harmful_used,
            "nutrient_deduction": sum(-item["points"] for item in breakdown if item["category"] == "nutrient"),
            "beneficial_credit": benefit_used,
        },
    }

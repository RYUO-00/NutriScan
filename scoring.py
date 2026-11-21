"""Configured, explainable Health Score heuristic."""

import config
from nutrition import comparable_nutrients, _threshold_status


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


def _data_completeness(nutrients, usable):
    present = {item.get("name") for item in nutrients}
    missing, unverified = [], []
    for key in config.SCORE_CORE_NUTRIENTS:
        alternatives = config.SCORE_NUTRIENT_ALTERNATIVES.get(key, (key,))
        if any(candidate in usable for candidate in alternatives):
            continue
        (unverified if any(candidate in present for candidate in alternatives) else missing).append(key)
    covered = len(config.SCORE_CORE_NUTRIENTS) - len(missing) - len(unverified)
    adverse = any(_threshold_status(key, item["value"], item["basis"], item["unit"], {}, item.get("serving_size"))[0] in {"Medium", "High"} for key, item in usable.items())
    enough = covered >= config.SCORE_MIN_CORE_FIELDS or adverse
    status = "insufficient" if not enough else ("provisional" if missing or unverified else "sufficient")
    messages = []
    if missing:
        messages.append("Not read: " + ", ".join(key.replace("_", " ") for key in missing) + ".")
    if unverified:
        messages.append("Could not verify a comparable value for: " + ", ".join(key.replace("_", " ") for key in unverified) + ".")
    if status == "insufficient":
        messages.insert(0, "A screening score needs either the majority of core fields or a verified nutritional concern. The available comparable readings do not meet that minimum.")
    elif status == "provisional":
        messages.insert(0, "This result covers only the verified readings. Missing information could change the score.")
    return {
        "status": status,
        "recognized_nutrients": sorted(present - {None}),
        "comparable_nutrients": sorted(usable),
        "missing_nutrients": missing,
        "unverified_nutrients": unverified,
        "verified_core_count": covered,
        "required_core_count": len(config.SCORE_CORE_NUTRIENTS),
        "coverage_percent": round(covered * 100 / len(config.SCORE_CORE_NUTRIENTS)),
        "confidence": "unavailable" if status == "insufficient" else ("limited" if missing or unverified else "supported"),
        "messages": messages,
    }


def calculate_health_score(additives=None, ingredient_flags=None, nutrients=None):
    """Return score, band, totals, and a reason for every applied contribution."""
    additives = _unique(additives or [], ("ins_code", "id"))
    ingredient_flags = _unique(ingredient_flags or [], ("id", "keyword"))
    nutrients = nutrients or []
    usable = comparable_nutrients(nutrients)
    completeness = _data_completeness(nutrients, usable)
    if completeness["status"] == "insufficient":
        return {
            "health_score": None, "score_band": None, "score_status": "insufficient",
            "data_completeness": completeness, "score_breakdown": [],
            "totals": {"additive_deduction": 0, "harmful_flag_deduction": 0, "nutrient_deduction": 0, "beneficial_credit": 0},
        }
    breakdown = [{"category": "starting score", "item": "Starting value", "points": config.STARTING_SCORE, "reason": f"The score starts at {config.STARTING_SCORE} points."}]
    additive_used = 0
    harmful_used = 0
    benefit_used = 0

    for additive in additives:
        risk = str(additive.get("risk_level", "low")).casefold()
        raw = config.ADDITIVE_DEDUCTIONS.get(risk, config.ADDITIVE_DEDUCTIONS["low"])
        applied = min(raw, max(0, config.ADDITIVE_DEDUCTION_CAP - additive_used))
        additive_used += applied
        breakdown.append({
            "category": "additive",
            "item": additive.get("name", additive.get("ins_code", "Recognized additive")),
            "points": -applied,
            "reason": additive.get("reason", "Screening deduction for this additive."),
            "risk_level": risk,
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The total additive deduction limit was reached."

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
            "reason": flag.get("reason", "Screening deduction for this ingredient flag."),
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The total ingredient deduction limit was reached."

    evaluations = {key: _threshold_status(key, item["value"], item["basis"], item["unit"], {}, item.get("serving_size")) for key, item in usable.items()}
    grouped_with = {}
    for group in config.SCORE_NON_ADDITIVE_GROUPS:
        matches = [key for key in group if key in evaluations and evaluations[key][0] in {"High", "Medium"}]
        if len(matches) > 1:
            primary = max(matches, key=lambda key: config.HIGH_NUTRIENT_DEDUCTION if evaluations[key][0] == "High" else config.MEDIUM_NUTRIENT_DEDUCTION)
            grouped_with.update({key: primary for key in matches if key != primary})
    for key, nutrient in usable.items():
        if key == "salt" and "sodium" in usable:
            continue
        status, reason, _threshold = evaluations[key]
        if status not in {"High", "Medium"}:
            continue
        if status == "High":
            points = config.HIGH_NUTRIENT_DEDUCTION
        else:
            points = config.MEDIUM_NUTRIENT_DEDUCTION
        grouped_reason = ""
        if key in grouped_with:
            points = 0
            grouped_reason = f" Included in the {grouped_with[key].replace('_', ' ')} deduction; the same nutrient group is not counted twice."
        breakdown.append({
            "category": "nutrient",
            "item": key,
            "points": -points,
            "reason": f"{key.replace('_', ' ').title()}: {nutrient['value']:g} {nutrient['unit']} per {nutrient['basis']}; {status.lower()} screening range. " + nutrient.get("reason", reason) + grouped_reason,
            "status": status,
            "threshold_source": _threshold.get("source"),
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
            "reason": flag.get("reason", "Screening credit for this ingredient."),
        })
        if applied < raw:
            breakdown[-1]["cap_note"] = "The total ingredient credit limit was reached."

    raw_score = sum(item["points"] for item in breakdown)
    score = max(0, min(100, raw_score))
    if score != raw_score:
        breakdown.append({
            "category": "clamp",
            "item": "Score range",
            "points": score - raw_score,
            "reason": "The score is limited to the 0 to 100 range.",
        })
    return {
        "health_score": score,
        "score_band": _band(score),
        "score_status": completeness["status"],
        "data_completeness": completeness,
        "score_breakdown": breakdown,
        "totals": {
            "additive_deduction": additive_used,
            "harmful_flag_deduction": harmful_used,
            "nutrient_deduction": sum(-item["points"] for item in breakdown if item["category"] == "nutrient"),
            "beneficial_credit": benefit_used,
        },
    }

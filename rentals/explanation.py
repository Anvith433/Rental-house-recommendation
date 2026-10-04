"""Deterministic, data-grounded explanations for recommendation scores.

Every sentence is derived from the property's actual attributes and the
user's preferences – no templates are filled with invented facts and no
language model is involved.
"""

from .recommendations import must_have_failures_for


def _rupees(amount) -> str:
    return f"₹{float(amount):,.0f}"


def _explain_location(preferences, matched, unmatched, strengths, weaknesses, house):
    location = preferences.get("location")
    if "location" in matched:
        strengths.append(f"Matches your preferred location: {location}")
    elif "location" in unmatched:
        weaknesses.append(f"Does not match your preferred location: {location}")


def _explain_budget(preferences, matched, unmatched, strengths, weaknesses, house):
    max_rent = preferences.get("max_rent")
    if "budget" in matched and max_rent is not None:
        savings = float(max_rent) - float(house.rent)
        if savings > 0:
            strengths.append(
                f"Within your maximum budget of {_rupees(max_rent)}, saving {_rupees(savings)}"
            )
        else:
            strengths.append(f"Matches your maximum budget of {_rupees(max_rent)}")
    elif "budget" in unmatched:
        weaknesses.append(f"Exceeds your maximum budget of {_rupees(max_rent)}")

    min_rent = preferences.get("min_rent")
    if "minimum_budget" in matched:
        strengths.append(f"Meets your minimum budget of {_rupees(min_rent)}")
    elif "minimum_budget" in unmatched:
        weaknesses.append(f"Below your minimum budget of {_rupees(min_rent)}")


def _explain_bedrooms(preferences, matched, unmatched, strengths, weaknesses, house):
    bedrooms = preferences.get("bedrooms")
    minimum_mode = preferences.get("bedroom_mode", "exact") == "minimum"
    if "bedrooms" in matched:
        if minimum_mode:
            strengths.append(
                f"Has {house.bedrooms} bedrooms, meeting your minimum requirement of {bedrooms}"
            )
        else:
            strengths.append(f"Matches your {bedrooms}-bedroom requirement")
    elif "bedrooms" in unmatched:
        if minimum_mode:
            weaknesses.append(
                f"Has only {house.bedrooms} bedrooms; you requested at least {bedrooms}"
            )
        else:
            weaknesses.append(
                f"Has {house.bedrooms} bedrooms instead of your requested {bedrooms}"
            )


def _explain_furnished(preferences, matched, unmatched, strengths, weaknesses, house):
    furnished = preferences.get("furnished")
    if furnished is None:
        return
    if "furnished" in matched:
        strengths.append("Furnished as requested" if furnished else "Unfurnished as requested")
    elif "furnished" in unmatched:
        weaknesses.append(
            "The house is not furnished as requested"
            if furnished
            else "The house is furnished, but you requested an unfurnished property"
        )


def _explain_parking(preferences, matched, unmatched, strengths, weaknesses, house):
    parking = preferences.get("parking")
    if parking is None:
        return
    if "parking" in matched:
        strengths.append(
            "Parking is available as requested" if parking else "No parking, matching your preference"
        )
    elif "parking" in unmatched:
        weaknesses.append(
            "Parking was requested but is unavailable"
            if parking
            else "Parking is available, although you preferred no parking"
        )


_EXPLAINERS = (
    _explain_location,
    _explain_budget,
    _explain_bedrooms,
    _explain_furnished,
    _explain_parking,
)


def _summarise(matched, unmatched, must_have_failures) -> str:
    if must_have_failures:
        return (
            "This house matches several of your preferences, but does not satisfy "
            f"your must-have preference(s): {', '.join(must_have_failures)}."
        )
    if matched and not unmatched:
        return "Excellent match. This house satisfies all of your specified preferences."
    if len(matched) >= 3:
        return "Good overall match with several of your preferences satisfied."
    if matched:
        return "Partial match. Some of your preferences are satisfied."
    return "Limited match. This house does not satisfy most of your specified preferences."


def generate_house_explanation(house, preferences, score_result, budget_context=None):
    """Explain why ``house`` received ``score_result``.

    ``budget_context`` (optional) carries ``original_max_rent`` when the
    engine had to relax the budget, so the explanation can state plainly that
    a property costs more than the user originally asked for.
    """
    matched = score_result.get("matched_preferences", [])
    unmatched = score_result.get("unmatched_preferences", [])
    priority = preferences.get("priority") or {}

    strengths: list[str] = []
    weaknesses: list[str] = []
    for explain in _EXPLAINERS:
        explain(preferences, matched, unmatched, strengths, weaknesses, house)

    original_max_rent = (budget_context or {}).get("original_max_rent")
    if original_max_rent is not None and house.rent > float(original_max_rent):
        weaknesses.append(
            f"Rent is {_rupees(house.rent - float(original_max_rent))} above your original "
            f"budget of {_rupees(original_max_rent)} (shown because the budget was relaxed)"
        )

    return {
        "summary": _summarise(matched, unmatched, must_have_failures_for(unmatched, priority)),
        "strengths": strengths,
        "weaknesses": weaknesses,
    }

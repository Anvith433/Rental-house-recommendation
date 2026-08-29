def generate_house_explanation(
    house,
    preferences,
    score_result
):
    """
    Generate a human-readable explanation
    for why a house received its recommendation score.
    """

    matched_preferences = score_result.get(
        "matched_preferences",
        []
    )

    unmatched_preferences = score_result.get(
        "unmatched_preferences",
        []
    )

    priority = preferences.get(
        "priority",
        {}
    )

    strengths = []
    weaknesses = []

    # -------------------------
    # LOCATION EXPLANATION
    # -------------------------
    location = preferences.get("location")

    if "location" in matched_preferences:

        strengths.append(
            f"Matches your preferred location: "
            f"{location}"
        )

    elif "location" in unmatched_preferences:

        weaknesses.append(
            f"Does not match your preferred "
            f"location: {location}"
        )

    # -------------------------
    # BUDGET EXPLANATION
    # -------------------------
    max_rent = preferences.get("max_rent")

    if "budget" in matched_preferences:

        if max_rent is not None:

            savings = (
                float(max_rent)
                - float(house.rent)
            )

            if savings > 0:

                strengths.append(
                    f"Within your maximum budget of "
                    f"₹{float(max_rent):,.0f}, "
                    f"saving ₹{savings:,.0f}"
                )

            else:

                strengths.append(
                    f"Matches your maximum budget "
                    f"of ₹{float(max_rent):,.0f}"
                )

    elif "budget" in unmatched_preferences:

        weaknesses.append(
            f"Exceeds your maximum budget of "
            f"₹{float(max_rent):,.0f}"
        )

    # -------------------------
    # MINIMUM RENT EXPLANATION
    # -------------------------
    min_rent = preferences.get("min_rent")

    if "minimum_budget" in matched_preferences:

        strengths.append(
            f"Meets your minimum budget of "
            f"₹{float(min_rent):,.0f}"
        )

    elif "minimum_budget" in unmatched_preferences:

        weaknesses.append(
            f"Below your minimum budget of "
            f"₹{float(min_rent):,.0f}"
        )

    # -------------------------
    # BEDROOM EXPLANATION
    # -------------------------
    bedrooms = preferences.get("bedrooms")

    bedroom_mode = preferences.get(
        "bedroom_mode",
        "exact"
    )

    if "bedrooms" in matched_preferences:

        if bedroom_mode == "minimum":

            strengths.append(
                f"Has {house.bedrooms} bedrooms, "
                f"meeting your minimum requirement "
                f"of {bedrooms}"
            )

        else:

            strengths.append(
                f"Matches your {bedrooms}-bedroom "
                f"requirement"
            )

    elif "bedrooms" in unmatched_preferences:

        if bedroom_mode == "minimum":

            weaknesses.append(
                f"Has only {house.bedrooms} bedrooms; "
                f"you requested at least {bedrooms}"
            )

        else:

            weaknesses.append(
                f"Has {house.bedrooms} bedrooms instead "
                f"of your requested {bedrooms}"
            )

    # -------------------------
    # FURNISHED EXPLANATION
    # -------------------------
    furnished = preferences.get("furnished")

    if furnished is not None:

        if "furnished" in matched_preferences:

            if furnished:

                strengths.append(
                    "Furnished as requested"
                )

            else:

                strengths.append(
                    "Unfurnished as requested"
                )

        elif "furnished" in unmatched_preferences:

            if furnished:

                weaknesses.append(
                    "The house is not furnished "
                    "as requested"
                )

            else:

                weaknesses.append(
                    "The house is furnished, "
                    "but you requested an "
                    "unfurnished property"
                )

    # -------------------------
    # PARKING EXPLANATION
    # -------------------------
    parking = preferences.get("parking")

    if parking is not None:

        if "parking" in matched_preferences:

            if parking:

                strengths.append(
                    "Parking is available "
                    "as requested"
                )

            else:

                strengths.append(
                    "No parking, matching "
                    "your preference"
                )

        elif "parking" in unmatched_preferences:

            if parking:

                weaknesses.append(
                    "Parking was requested "
                    "but is unavailable"
                )

            else:

                weaknesses.append(
                    "Parking is available, "
                    "although you preferred "
                    "no parking"
                )

    # -------------------------
    # PRIORITY INFORMATION
    # -------------------------
    must_have_failures = []

    for preference_name in unmatched_preferences:

        priority_name = preference_name

        if preference_name == "minimum_budget":

            priority_name = "budget"

        if (
            priority.get(priority_name)
            == "must_have"
        ):

            must_have_failures.append(
                priority_name
            )

    # -------------------------
    # SUMMARY
    # -------------------------
    if must_have_failures:

        formatted_preferences = ", ".join(
            must_have_failures
        )

        summary = (
            "This house matches several of your "
            "preferences, but does not satisfy "
            f"your must-have preference(s): "
            f"{formatted_preferences}."
        )

    elif (
        len(matched_preferences) > 0
        and len(unmatched_preferences) == 0
    ):

        summary = (
            "Excellent match. This house "
            "satisfies all of your specified "
            "preferences."
        )

    elif len(matched_preferences) >= 3:

        summary = (
            "Good overall match with several "
            "of your preferences satisfied."
        )

    elif len(matched_preferences) > 0:

        summary = (
            "Partial match. Some of your "
            "preferences are satisfied."
        )

    else:

        summary = (
            "Limited match. This house does "
            "not satisfy most of your "
            "specified preferences."
        )

    # -------------------------
    # RETURN EXPLANATION
    # -------------------------
    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses
    }
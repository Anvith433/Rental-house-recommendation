def calculate_house_score(house, preferences):

    score = 0

    matched_preferences = []
    unmatched_preferences = []

    # -------------------------
    # PRIORITY CONFIGURATION
    # -------------------------
    priority = preferences.get(
        "priority",
        {}
    )

    priority_weights = {
        "must_have": 1.50,
        "important": 1.25,
        "preferred": 1.00,
        "optional": 0.50
    }

    def get_priority_weight(preference_name):

        preference_priority = priority.get(
            preference_name,
            "preferred"
        )

        return priority_weights.get(
            preference_priority,
            1.00
        )

    # -------------------------
    # Location: 30 points
    # -------------------------
    location = preferences.get("location")

    if location:

        location_weight = (
            get_priority_weight("location")
        )

        location_score = 30 * location_weight

        if location.lower() in house.location.lower():

            score += location_score

            matched_preferences.append(
                "location"
            )

        else:

            unmatched_preferences.append(
                "location"
            )

    # -------------------------
    # Budget: 25 points
    # -------------------------
    max_rent = preferences.get("max_rent")

    if max_rent is not None:

        max_rent = float(max_rent)

        if house.rent <= max_rent:

            # Calculate how much of the user's
            # budget is being saved.
            savings_ratio = (
                max_rent - house.rent
            ) / max_rent

            base_budget_score = (
                15 + (10 * savings_ratio)
            )

            budget_weight = (
                get_priority_weight("budget")
            )

            budget_score = (
                base_budget_score
                * budget_weight
            )

            score += budget_score

            matched_preferences.append(
                "budget"
            )

        else:

            unmatched_preferences.append(
                "budget"
            )

    # -------------------------
    # Minimum Rent
    # -------------------------
    min_rent = preferences.get("min_rent")

    if min_rent is not None:

        min_rent = float(min_rent)

        if house.rent >= min_rent:

            matched_preferences.append(
                "minimum_budget"
            )

        else:

            unmatched_preferences.append(
                "minimum_budget"
            )

    # -------------------------
    # Bedrooms: 20 points
    # -------------------------
    bedrooms = preferences.get("bedrooms")

    if bedrooms is not None:

        bedrooms = int(bedrooms)

        bedroom_mode = preferences.get(
            "bedroom_mode",
            "exact"
        )

        bedroom_weight = (
            get_priority_weight("bedrooms")
        )

        # -------------------------
        # Minimum bedroom mode
        # -------------------------
        if bedroom_mode == "minimum":

            if house.bedrooms >= bedrooms:

                if house.bedrooms == bedrooms:

                    bedroom_score = 20

                else:

                    extra_bedrooms = (
                        house.bedrooms - bedrooms
                    )

                    bedroom_score = max(
                        10,
                        20 - (
                            extra_bedrooms * 5
                        )
                    )

                bedroom_score = (
                    bedroom_score
                    * bedroom_weight
                )

                score += bedroom_score

                matched_preferences.append(
                    "bedrooms"
                )

            else:

                unmatched_preferences.append(
                    "bedrooms"
                )

        # -------------------------
        # Exact bedroom mode
        # -------------------------
        else:

            if house.bedrooms == bedrooms:

                bedroom_score = (
                    20 * bedroom_weight
                )

                score += bedroom_score

                matched_preferences.append(
                    "bedrooms"
                )

            else:

                unmatched_preferences.append(
                    "bedrooms"
                )

    # -------------------------
    # Furnished: 15 points
    # -------------------------
    furnished = preferences.get(
        "furnished"
    )

    if furnished is not None:

        furnished_weight = (
            get_priority_weight("furnished")
        )

        furnished_score = (
            15 * furnished_weight
        )

        if house.furnished == furnished:

            score += furnished_score

            matched_preferences.append(
                "furnished"
            )

        else:

            unmatched_preferences.append(
                "furnished"
            )

    # -------------------------
    # Parking: 10 points
    # -------------------------
    parking = preferences.get(
        "parking"
    )

    if parking is not None:

        parking_weight = (
            get_priority_weight("parking")
        )

        parking_score = (
            10 * parking_weight
        )

        if house.parking == parking:

            score += parking_score

            matched_preferences.append(
                "parking"
            )

        else:

            unmatched_preferences.append(
                "parking"
            )

    # -------------------------
    # MUST-HAVE PENALTY
    # -------------------------
    #
    # A must-have preference that is not
    # satisfied should have a significant
    # negative effect on the recommendation.
    #
    # Hard filters such as required_parking
    # are still handled by views.py.
    #
    must_have_penalty = 20

    for preference_name in unmatched_preferences:

        if preference_name == "minimum_budget":

            priority_name = "budget"

        else:

            priority_name = preference_name

        if (
            priority.get(priority_name)
            == "must_have"
        ):

            score -= must_have_penalty

    # -------------------------
    # FINAL SCORE
    # -------------------------
    score = max(
        0,
        min(score, 100)
    )

    return {
        "score": round(
            score,
            2
        ),

        "matched_preferences": (
            matched_preferences
        ),

        "unmatched_preferences": (
            unmatched_preferences
        )
    }
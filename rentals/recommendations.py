def calculate_house_score(house, preferences):

    score = 0

    matched_preferences = []
    unmatched_preferences = []

    # -------------------------
    # Location: 30 points
    # -------------------------
    location = preferences.get("location")

    if location:

        if location.lower() in house.location.lower():

            score += 30
            matched_preferences.append("location")

        else:

            unmatched_preferences.append("location")

    # -------------------------
    # Budget: 25 points
    # -------------------------
    max_rent = preferences.get("max_rent")

    if max_rent:

        max_rent = float(max_rent)

        if house.rent <= max_rent:

            budget_ratio = house.rent / max_rent

            budget_score = 25 * budget_ratio

            score += budget_score

            matched_preferences.append("budget")

        else:

            unmatched_preferences.append("budget")

    # -------------------------
    # Bedrooms: 20 points
    # -------------------------
    bedrooms = preferences.get("bedrooms")

    if bedrooms:

        bedrooms = int(bedrooms)

        bedroom_mode = preferences.get(
            "bedroom_mode",
            "exact"
        )

        if bedroom_mode == "minimum":

            if house.bedrooms >= bedrooms:

                if house.bedrooms == bedrooms:

                    score += 20

                else:

                    extra_bedrooms = (
                        house.bedrooms - bedrooms
                    )

                    bedroom_score = max(
                        10,
                        20 - (extra_bedrooms * 5)
                    )

                    score += bedroom_score

                matched_preferences.append(
                    "bedrooms"
                )

            else:

                unmatched_preferences.append(
                    "bedrooms"
                )

        else:

            if house.bedrooms == bedrooms:

                score += 20

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
    furnished = preferences.get("furnished")

    if furnished is not None:

        if house.furnished == furnished:

            score += 15

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
    parking = preferences.get("parking")

    if parking is not None:

        if house.parking == parking:

            score += 10

            matched_preferences.append(
                "parking"
            )

        else:

            unmatched_preferences.append(
                "parking"
            )

    # -------------------------
    # Final result
    # -------------------------
    return {
        "score": round(score, 2),
        "matched_preferences": matched_preferences,
        "unmatched_preferences": unmatched_preferences
    }
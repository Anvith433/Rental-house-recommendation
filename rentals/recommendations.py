def calculate_house_score(house, preferences):
    """
    Calculate how well a house matches the user's preferences.

    Maximum score = 100
    """

    score = 0

    # Location match - 30 points
    if preferences.get("location"):
        if preferences["location"].lower() in house.location.lower():
            score += 30

    # Budget match - 30 points
    if preferences.get("max_rent"):
        if house.rent <= preferences["max_rent"]:
            score += 30

    # Bedroom match - 20 points
    if preferences.get("bedrooms"):
        if house.bedrooms == preferences["bedrooms"]:
            score += 20

    # Furnished match - 10 points
    if preferences.get("furnished") is not None:
        if house.furnished == preferences["furnished"]:
            score += 10

    # Parking match - 10 points
    if preferences.get("parking") is not None:
        if house.parking == preferences["parking"]:
            score += 10

    return score
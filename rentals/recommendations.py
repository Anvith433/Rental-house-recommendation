"""Weighted, priority-aware scoring of a single property against preferences.

``calculate_house_score`` is pure (no database access) so it can score tens of
thousands of candidates per request. Each criterion is evaluated by its own
small function returning ``(matched, points)`` where ``matched`` is ``None``
when the user expressed no preference for that criterion.
"""

from .recommendation_config import (
    BEDROOM_EXTRA_ROOM_PENALTY,
    BEDROOM_MINIMUM_POINTS,
    BUDGET_BASE_POINTS,
    BUDGET_SAVINGS_POINTS,
    DEFAULT_PRIORITY,
    MAX_SCORE,
    MIN_SCORE,
    MUST_HAVE_PENALTY,
    PRIORITY_MULTIPLIERS,
    SCORING_WEIGHTS,
)

# Unmatched preference name -> the priority key that governs it.
PRIORITY_KEY_FOR_PREFERENCE = {"minimum_budget": "budget"}


def priority_multiplier(priority: dict, criterion: str) -> float:
    level = priority.get(criterion, DEFAULT_PRIORITY)
    return PRIORITY_MULTIPLIERS.get(level, PRIORITY_MULTIPLIERS[DEFAULT_PRIORITY])


def _score_location(house, location):
    if not location:
        return None, 0.0
    if location.lower() in house.location.lower():
        return True, float(SCORING_WEIGHTS["location"])
    return False, 0.0


def _score_budget(house, max_rent):
    if max_rent is None:
        return None, 0.0
    max_rent = float(max_rent)
    if house.rent > max_rent:
        return False, 0.0
    savings_ratio = (max_rent - house.rent) / max_rent if max_rent else 0.0
    return True, BUDGET_BASE_POINTS + BUDGET_SAVINGS_POINTS * savings_ratio


def _check_minimum_rent(house, min_rent):
    """Minimum rent is a match/mismatch signal only; it earns no points."""
    if min_rent is None:
        return None, 0.0
    return house.rent >= float(min_rent), 0.0


def _score_bedrooms(house, bedrooms, bedroom_mode):
    if bedrooms is None:
        return None, 0.0
    bedrooms = int(bedrooms)
    full_points = SCORING_WEIGHTS["bedrooms"]

    if bedroom_mode == "minimum":
        if house.bedrooms < bedrooms:
            return False, 0.0
        extra_rooms = house.bedrooms - bedrooms
        if extra_rooms == 0:
            return True, float(full_points)
        return True, float(
            max(BEDROOM_MINIMUM_POINTS, full_points - extra_rooms * BEDROOM_EXTRA_ROOM_PENALTY)
        )

    if house.bedrooms == bedrooms:
        return True, float(full_points)
    return False, 0.0


def _score_boolean_feature(actual: bool, wanted, criterion: str):
    if wanted is None:
        return None, 0.0
    if actual == wanted:
        return True, float(SCORING_WEIGHTS[criterion])
    return False, 0.0


def calculate_house_score(house, preferences: dict) -> dict:
    """Score ``house`` against ``preferences``.

    Returns ``score`` (0–100, 2 d.p.), the ordered ``matched_preferences`` and
    ``unmatched_preferences`` lists, and a per-criterion ``breakdown`` of the
    (priority-weighted) points awarded.
    """
    priority = preferences.get("priority") or {}

    evaluations = [
        ("location", "location", _score_location(house, preferences.get("location"))),
        ("budget", "budget", _score_budget(house, preferences.get("max_rent"))),
        ("minimum_budget", None, _check_minimum_rent(house, preferences.get("min_rent"))),
        (
            "bedrooms",
            "bedrooms",
            _score_bedrooms(
                house, preferences.get("bedrooms"), preferences.get("bedroom_mode", "exact")
            ),
        ),
        (
            "furnished",
            "furnished",
            _score_boolean_feature(house.furnished, preferences.get("furnished"), "furnished"),
        ),
        (
            "parking",
            "parking",
            _score_boolean_feature(house.parking, preferences.get("parking"), "parking"),
        ),
    ]

    score = 0.0
    matched_preferences: list[str] = []
    unmatched_preferences: list[str] = []
    breakdown: dict[str, float] = {}

    for name, criterion, (matched, points) in evaluations:
        if matched is None:
            continue
        if matched:
            matched_preferences.append(name)
        else:
            unmatched_preferences.append(name)
        if criterion is not None:
            weighted = points * priority_multiplier(priority, criterion)
            breakdown[criterion] = round(weighted, 2)
            score += weighted

    must_have_failures = must_have_failures_for(unmatched_preferences, priority)
    score -= MUST_HAVE_PENALTY * len(must_have_failures)

    score = max(MIN_SCORE, min(score, MAX_SCORE))

    return {
        "score": round(score, 2),
        "matched_preferences": matched_preferences,
        "unmatched_preferences": unmatched_preferences,
        "breakdown": breakdown,
    }


def must_have_failures_for(unmatched_preferences: list[str], priority: dict) -> list[str]:
    """Priority keys of unmatched preferences the user marked as must-have."""
    failures = []
    for name in unmatched_preferences:
        key = PRIORITY_KEY_FOR_PREFERENCE.get(name, name)
        if priority.get(key) == "must_have":
            failures.append(key)
    return failures

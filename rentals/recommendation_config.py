"""Single source of truth for the recommendation engine's tunable numbers.

Base weights sum to 100. Each criterion's points are multiplied by the user's
priority for that criterion; unmet must-have criteria incur a fixed penalty;
the final score is clamped to [0, 100].
"""

from django.conf import settings

SCORING_WEIGHTS: dict[str, int] = {
    "location": 30,
    "budget": 25,
    "bedrooms": 20,
    "furnished": 15,
    "parking": 10,
}

# Budget: a within-budget property earns the base points, plus up to the
# savings points in proportion to how far below the maximum rent it is.
BUDGET_BASE_POINTS = 15
BUDGET_SAVINGS_POINTS = SCORING_WEIGHTS["budget"] - BUDGET_BASE_POINTS

# Minimum-bedroom mode: each bedroom above the requested count costs points,
# down to a floor, so an exact fit ranks above an oversized home.
BEDROOM_EXTRA_ROOM_PENALTY = 5
BEDROOM_MINIMUM_POINTS = 10

PRIORITY_MULTIPLIERS: dict[str, float] = {
    "must_have": 1.50,
    "important": 1.25,
    "preferred": 1.00,
    "optional": 0.50,
}
DEFAULT_PRIORITY = "preferred"

MUST_HAVE_PENALTY = 20

MIN_SCORE = 0
MAX_SCORE = 100

DEFAULT_TOP_N = 5
MAX_TOP_N = 100


def budget_relaxation_steps() -> tuple[int, ...]:
    """Percentages by which max_rent is progressively raised when a strict
    search finds nothing. Override with RECOMMENDATION_BUDGET_RELAXATION_STEPS."""
    return tuple(getattr(settings, "RECOMMENDATION_BUDGET_RELAXATION_STEPS", (10, 20, 30)))

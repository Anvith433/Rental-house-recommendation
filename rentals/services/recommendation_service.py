"""The recommendation pipeline.

    validated preferences
        → hard constraints (database query)          candidate_queryset()
        → budget relaxation if nothing matched       _find_candidates()
        → weighted, priority-aware scoring           score_candidates()
        → deterministic ranking                      rank()
        → Top-N selection
        → serialization + explanation of Top-N only  _build_recommendations()

Only the Top-N survivors are serialized and explained, so the cost of the
expensive stages is independent of the candidate count.

Database access is two queries on the strict path: candidates are loaded with
only the columns scoring needs (instantiating full rows dominated latency at
50K candidates), then the Top-N are fetched in full with their primary image.
"""

import json
import logging
import time
from dataclasses import dataclass, field

from django.db.models import QuerySet

from core.metrics import recommendation_metrics

from ..choices import ListingStatus
from ..explanation import generate_house_explanation
from ..models import House, RecommendationHistory
from ..recommendation_config import DEFAULT_TOP_N, budget_relaxation_steps
from ..recommendations import calculate_house_score
from ..serializers.properties import PropertyListSerializer

logger = logging.getLogger("rentwise.recommendations")

# Columns read by scoring and ranking; everything else is loaded for Top-N only.
SCORING_FIELDS = ("id", "location", "rent", "bedrooms", "furnished", "parking", "area_sqft")


@dataclass
class ScoredHouse:
    house: House
    score: float
    matched_preferences: list[str]
    unmatched_preferences: list[str]
    breakdown: dict[str, float]

    @property
    def score_result(self) -> dict:
        return {
            "score": self.score,
            "matched_preferences": self.matched_preferences,
            "unmatched_preferences": self.unmatched_preferences,
        }


@dataclass
class BudgetRelaxation:
    original_max_rent: float
    relaxed_max_rent: float
    percentage: int


@dataclass
class RecommendationResult:
    recommendations: list[dict]
    total_matches: int
    requested_top_n: int
    filters_applied: dict
    relaxation: BudgetRelaxation | None = None
    latency_ms: float = 0.0
    property_ids: list[int] = field(default_factory=list)

    def to_response(self) -> dict:
        data = {
            "recommendations": self.recommendations,
            "total_matches": self.total_matches,
            "requested_top_n": self.requested_top_n,
            "returned_count": len(self.recommendations),
            "filters_applied": self.filters_applied,
            "budget_relaxed": self.relaxation is not None,
        }
        if self.relaxation is not None:
            data["message"] = (
                "No houses matched your original budget. Showing recommendations "
                "with a slightly higher budget."
            )
            data["original_max_rent"] = self.relaxation.original_max_rent
            data["relaxed_max_rent"] = self.relaxation.relaxed_max_rent
            data["relaxation_percentage"] = self.relaxation.percentage
        elif not self.recommendations:
            data["message"] = "No houses matched your requirements."
        return data


class RecommendationService:
    """Rule-based, explainable property recommender."""

    def __init__(self, relaxation_steps: tuple[int, ...] | None = None):
        self.relaxation_steps = (
            relaxation_steps if relaxation_steps is not None else budget_relaxation_steps()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def recommend(self, preferences: dict, user=None) -> RecommendationResult:
        """Run the full pipeline for validated ``preferences``.

        When ``user`` is authenticated the request is recorded in their
        recommendation history.
        """
        started = time.perf_counter()
        top_n = preferences.get("top_n", DEFAULT_TOP_N)

        candidates, effective_preferences, relaxation = self._find_candidates(preferences)
        ranked = self.rank(self.score_candidates(candidates, effective_preferences))
        top = ranked[:top_n]

        budget_context = (
            {"original_max_rent": relaxation.original_max_rent} if relaxation else None
        )
        recommendations = self._build_recommendations(top, effective_preferences, budget_context)

        result = RecommendationResult(
            recommendations=recommendations,
            total_matches=len(candidates),
            requested_top_n=top_n,
            filters_applied=preferences,
            relaxation=relaxation,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            property_ids=[item.house.id for item in top],
        )
        self._record(result, user)
        return result

    def evaluate(self, house: House, preferences: dict) -> dict:
        """Score and explain one property against ``preferences`` (used for
        property details and comparisons). No hard filtering is applied."""
        scored = self._score(house, preferences)
        return {
            "score": scored.score,
            "matched_preferences": scored.matched_preferences,
            "unmatched_preferences": scored.unmatched_preferences,
            "score_breakdown": scored.breakdown,
            "explanation": generate_house_explanation(house, preferences, scored.score_result),
        }

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------
    @staticmethod
    def candidate_queryset(preferences: dict) -> QuerySet:
        """Apply the hard constraints in the database. Only active listings
        are ever recommended."""
        houses = House.objects.filter(status=ListingStatus.ACTIVE)

        max_rent = preferences.get("max_rent")
        if max_rent is not None:
            houses = houses.filter(rent__lte=max_rent)

        min_rent = preferences.get("min_rent")
        if min_rent is not None:
            houses = houses.filter(rent__gte=min_rent)

        bedrooms = preferences.get("bedrooms")
        if bedrooms is not None:
            if preferences.get("bedroom_mode", "exact") == "minimum":
                houses = houses.filter(bedrooms__gte=bedrooms)
            else:
                houses = houses.filter(bedrooms=bedrooms)

        location = preferences.get("location")
        if location:
            houses = houses.filter(location__icontains=location)

        if preferences.get("required_parking"):
            houses = houses.filter(parking=True)

        return houses

    def score_candidates(self, houses: list[House], preferences: dict) -> list[ScoredHouse]:
        return [self._score(house, preferences) for house in houses]

    @staticmethod
    def rank(scored: list[ScoredHouse]) -> list[ScoredHouse]:
        """Deterministic order: score DESC, rent ASC, area DESC, id ASC."""
        return sorted(
            scored,
            key=lambda item: (-item.score, item.house.rent, -item.house.area_sqft, item.house.id),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _score(house: House, preferences: dict) -> ScoredHouse:
        result = calculate_house_score(house, preferences)
        return ScoredHouse(
            house=house,
            score=result["score"],
            matched_preferences=result["matched_preferences"],
            unmatched_preferences=result["unmatched_preferences"],
            breakdown=result["breakdown"],
        )

    def _can_relax_budget(self, preferences: dict) -> bool:
        priority = preferences.get("priority") or {}
        return (
            preferences.get("max_rent") is not None
            and preferences.get("allow_budget_relaxation", True)
            # An explicit must-have budget is a hard requirement: never relax it.
            and priority.get("budget") != "must_have"
        )

    def _find_candidates(self, preferences: dict):
        """Strict search first; if empty, raise max_rent step by step. Every
        other constraint is preserved, and the relaxation is reported."""
        candidates = list(self.candidate_queryset(preferences).only(*SCORING_FIELDS))
        if candidates or not self._can_relax_budget(preferences):
            return candidates, preferences, None

        original_max_rent = float(preferences["max_rent"])
        for percentage in self.relaxation_steps:
            relaxed_max_rent = original_max_rent * (1 + percentage / 100)
            relaxed_preferences = {**preferences, "max_rent": relaxed_max_rent}
            candidates = list(
                self.candidate_queryset(relaxed_preferences).only(*SCORING_FIELDS)
            )
            if candidates:
                relaxation = BudgetRelaxation(original_max_rent, relaxed_max_rent, percentage)
                return candidates, relaxed_preferences, relaxation

        return [], preferences, None

    @staticmethod
    def _build_recommendations(top: list[ScoredHouse], preferences: dict, budget_context):
        if not top:
            return []
        full_houses = House.objects.with_primary_image().in_bulk([item.house.id for item in top])

        recommendations = []
        for item in top:
            house = full_houses.get(item.house.id)
            if house is None:  # Deleted between the two queries.
                continue
            serialized = PropertyListSerializer(house).data
            recommendations.append(
                {
                    "rank": len(recommendations) + 1,
                    "property": serialized,
                    # Deprecated alias of "property", kept for existing clients.
                    "house": serialized,
                    "score": item.score,
                    "matched_preferences": item.matched_preferences,
                    "unmatched_preferences": item.unmatched_preferences,
                    "score_breakdown": item.breakdown,
                    "explanation": generate_house_explanation(
                        house, preferences, item.score_result, budget_context
                    ),
                }
            )
        return recommendations

    @staticmethod
    def _record(result: RecommendationResult, user) -> None:
        relaxed = result.relaxation is not None
        recommendation_metrics.record(
            latency_ms=result.latency_ms,
            candidates=result.total_matches,
            results=len(result.recommendations),
            relaxed=relaxed,
        )
        logger.info(
            "recommendation served",
            extra={
                "candidates": result.total_matches,
                "returned": len(result.recommendations),
                "budget_relaxed": relaxed,
                "latency_ms": result.latency_ms,
            },
        )
        if user is not None and user.is_authenticated:
            RecommendationHistory.objects.create(
                user=user,
                # Round-trip through JSON to store plain, serializable values.
                request_preferences=json.loads(json.dumps(result.filters_applied, default=str)),
                result_property_ids=result.property_ids,
                top_score=result.recommendations[0]["score"] if result.recommendations else None,
                total_matches=result.total_matches,
                budget_relaxed=relaxed,
                latency_ms=result.latency_ms,
            )

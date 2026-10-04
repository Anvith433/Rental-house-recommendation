from django.test import TestCase, override_settings

from core.metrics import recommendation_metrics
from rentals.explanation import generate_house_explanation
from rentals.recommendation_config import (
    MUST_HAVE_PENALTY,
    PRIORITY_MULTIPLIERS,
    SCORING_WEIGHTS,
)
from rentals.recommendations import calculate_house_score
from rentals.services.recommendation_service import RecommendationService

from .factories import make_house

BASE = {"bedroom_mode": "exact", "top_n": 5}


def prefs(**values):
    return {**BASE, **values}


class ScoringConfigurationTests(TestCase):
    def test_base_weights_sum_to_100(self):
        self.assertEqual(sum(SCORING_WEIGHTS.values()), 100)
        self.assertEqual(
            SCORING_WEIGHTS,
            {"location": 30, "budget": 25, "bedrooms": 20, "furnished": 15, "parking": 10},
        )

    def test_priority_multipliers_are_ordered(self):
        order = ["must_have", "important", "preferred", "optional"]
        values = [PRIORITY_MULTIPLIERS[level] for level in order]
        self.assertEqual(values, sorted(values, reverse=True))


class ScoringUnitTests(TestCase):
    def setUp(self):
        self.house = make_house()  # HSR, ₹23,000, 2 bed, furnished, no parking

    def test_breakdown_sums_to_score_without_penalties(self):
        result = calculate_house_score(
            self.house,
            prefs(location="HSR", max_rent=25000, bedrooms=2, furnished=True, parking=False),
        )
        self.assertAlmostEqual(sum(result["breakdown"].values()), result["score"], places=1)
        self.assertEqual(result["breakdown"]["location"], 30)

    def test_priority_multiplier_scales_criterion_points(self):
        important = calculate_house_score(
            self.house, prefs(location="HSR", priority={"location": "important"})
        )
        optional = calculate_house_score(
            self.house, prefs(location="HSR", priority={"location": "optional"})
        )
        self.assertEqual(important["breakdown"]["location"], 37.5)
        self.assertEqual(optional["breakdown"]["location"], 15)

    def test_each_failed_must_have_applies_penalty(self):
        result = calculate_house_score(
            self.house,
            prefs(
                location="Whitefield",
                parking=True,
                furnished=True,
                priority={"location": "must_have", "parking": "must_have"},
            ),
        )
        expected = max(0, 15 - 2 * MUST_HAVE_PENALTY)
        self.assertEqual(result["score"], expected)

    def test_budget_score_rewards_savings(self):
        tight = calculate_house_score(self.house, prefs(max_rent=23000))["score"]
        roomy = calculate_house_score(self.house, prefs(max_rent=46000))["score"]
        self.assertEqual(tight, 15)
        self.assertEqual(roomy, 20)

    def test_equal_min_and_max_rent(self):
        result = calculate_house_score(self.house, prefs(min_rent=23000, max_rent=23000))
        self.assertIn("budget", result["matched_preferences"])
        self.assertIn("minimum_budget", result["matched_preferences"])

    def test_zero_budget_does_not_crash(self):
        free = make_house(rent=0)
        self.assertEqual(calculate_house_score(free, prefs(max_rent=0))["score"], 15)

    def test_minimum_bedroom_mode_penalises_extra_rooms(self):
        big = make_house(bedrooms=5)
        result = calculate_house_score(big, prefs(bedrooms=2, bedroom_mode="minimum"))
        self.assertEqual(result["breakdown"]["bedrooms"], 10)  # floor applies

    def test_score_is_clamped(self):
        result = calculate_house_score(
            self.house,
            prefs(
                location="HSR",
                max_rent=100000,
                bedrooms=2,
                furnished=True,
                parking=False,
                priority={k: "must_have" for k in SCORING_WEIGHTS},
            ),
        )
        self.assertEqual(result["score"], 100)


class RecommendationServiceTests(TestCase):
    def setUp(self):
        self.service = RecommendationService()
        recommendation_metrics.reset()

    def test_empty_database(self):
        result = self.service.recommend(prefs(location="HSR", max_rent=30000))
        self.assertEqual(result.recommendations, [])
        self.assertEqual(result.total_matches, 0)
        self.assertIsNone(result.relaxation)

    def test_inactive_and_flagged_listings_are_never_recommended(self):
        active = make_house()
        make_house(status="inactive")
        make_house(status="flagged")
        result = self.service.recommend(prefs(location="HSR"))
        self.assertEqual(result.property_ids, [active.id])

    def test_ties_break_by_rent_then_area_then_id(self):
        expensive = make_house(rent=25000, area_sqft=1500)
        cheap_small = make_house(rent=22000, area_sqft=900)
        cheap_large = make_house(rent=22000, area_sqft=1200)
        cheap_large_twin = make_house(rent=22000, area_sqft=1200)
        result = self.service.recommend(prefs(location="HSR"))  # identical scores
        self.assertEqual(
            result.property_ids,
            [cheap_large.id, cheap_large_twin.id, cheap_small.id, expensive.id],
        )

    def test_ranking_is_stable_across_runs(self):
        for index in range(20):
            make_house(rent=20000 + (index % 4) * 1000, area_sqft=900 + (index % 3) * 100)
        first = self.service.recommend(prefs(location="HSR", max_rent=30000, top_n=20))
        second = self.service.recommend(prefs(location="HSR", max_rent=30000, top_n=20))
        self.assertEqual(first.property_ids, second.property_ids)

    def test_budget_relaxation_reports_original_and_relaxed_budget(self):
        make_house(rent=21000)
        result = self.service.recommend(prefs(location="HSR", max_rent=18000)).to_response()
        self.assertTrue(result["budget_relaxed"])
        self.assertEqual(result["original_max_rent"], 18000.0)
        self.assertAlmostEqual(result["relaxed_max_rent"], 21600.0)
        self.assertEqual(result["relaxation_percentage"], 20)
        self.assertEqual(result["filters_applied"]["max_rent"], 18000)

    def test_relaxation_preserves_other_hard_constraints(self):
        make_house(rent=19000, parking=False)
        result = self.service.recommend(
            prefs(location="HSR", max_rent=18000, required_parking=True)
        )
        self.assertEqual(result.recommendations, [])
        self.assertIsNone(result.relaxation)

    def test_relaxation_stops_after_last_step(self):
        make_house(rent=30000)
        result = self.service.recommend(prefs(location="HSR", max_rent=18000))
        self.assertEqual(result.recommendations, [])

    def test_must_have_budget_is_never_relaxed(self):
        make_house(rent=19000)
        result = self.service.recommend(
            prefs(location="HSR", max_rent=18000, priority={"budget": "must_have"})
        )
        self.assertEqual(result.recommendations, [])
        self.assertIsNone(result.relaxation)

    def test_client_can_disable_relaxation(self):
        make_house(rent=19000)
        result = self.service.recommend(
            prefs(location="HSR", max_rent=18000, allow_budget_relaxation=False)
        )
        self.assertIsNone(result.relaxation)

    @override_settings(RECOMMENDATION_BUDGET_RELAXATION_STEPS=(50,))
    def test_relaxation_steps_are_configurable(self):
        make_house(rent=26000)
        result = RecommendationService().recommend(prefs(location="HSR", max_rent=18000))
        self.assertEqual(result.relaxation.percentage, 50)

    def test_relaxed_explanation_is_honest_about_original_budget(self):
        make_house(rent=21000)
        recommendation = self.service.recommend(
            prefs(location="HSR", max_rent=18000)
        ).recommendations[0]
        explanation = recommendation["explanation"]
        self.assertTrue(
            any("Exceeds your maximum budget of ₹18,000 by ₹3,000" in w for w in explanation["weaknesses"])
        )
        self.assertFalse(any("budget" in s.lower() for s in explanation["strengths"]))
        self.assertNotIn("Excellent", explanation["summary"])

    def test_only_top_n_are_serialized(self):
        for index in range(30):
            make_house(rent=20000 + index)
        result = self.service.recommend(prefs(location="HSR", top_n=3))
        self.assertEqual(result.total_matches, 30)
        self.assertEqual(len(result.recommendations), 3)
        self.assertEqual([r["rank"] for r in result.recommendations], [1, 2, 3])

    def test_response_keeps_backward_compatible_house_key(self):
        make_house()
        item = self.service.recommend(prefs(location="HSR")).recommendations[0]
        self.assertEqual(item["house"], item["property"])
        for key in ("score", "matched_preferences", "unmatched_preferences", "explanation"):
            self.assertIn(key, item)

    def test_metrics_are_recorded(self):
        make_house()
        self.service.recommend(prefs(location="HSR"))
        self.service.recommend(prefs(location="Nowhere"))
        snapshot = recommendation_metrics.snapshot()
        self.assertEqual(snapshot["requests"], 2)
        self.assertEqual(snapshot["empty_result_rate"], 0.5)
        self.assertIsNotNone(snapshot["average_latency_ms"])

    def test_evaluate_scores_single_property(self):
        house = make_house()
        evaluation = self.service.evaluate(house, prefs(location="HSR", max_rent=25000))
        self.assertIn("score_breakdown", evaluation)
        self.assertEqual(evaluation["matched_preferences"], ["location", "budget"])

    def test_explanation_without_budget_context_is_unchanged(self):
        house = make_house()
        preferences = prefs(location="HSR", max_rent=25000)
        score = calculate_house_score(house, preferences)
        self.assertEqual(
            generate_house_explanation(house, preferences, score),
            generate_house_explanation(house, preferences, score, budget_context=None),
        )

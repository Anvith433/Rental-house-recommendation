from django.test import TestCase

from rentals.models import House
from rentals.recommendations import calculate_house_score


class HouseRecommendationScoreTests(TestCase):

    def setUp(self):

        self.house = House.objects.create(
            title="2BHK HSR Apartment",
            location="HSR Layout",
            rent=23000,
            bedrooms=2,
            bathrooms=2,
            furnished=True,
            parking=False,
            area_sqft=1100
        )

    # -------------------------
    # PERFECT MATCH
    # -------------------------
    def test_perfect_match(self):

        preferences = {
            "location": "HSR",
            "max_rent": 25000,
            "min_rent": 20000,
            "bedrooms": 2,
            "bedroom_mode": "exact",
            "furnished": True,
            "parking": False
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertEqual(
            result["score"],
            90.8
        )

        self.assertEqual(
            result["matched_preferences"],
            [
                "location",
                "budget",
                "minimum_budget",
                "bedrooms",
                "furnished",
                "parking"
            ]
        )

        self.assertEqual(
            result["unmatched_preferences"],
            []
        )

    # -------------------------
    # LOCATION MATCH
    # -------------------------
    def test_location_match(self):

        preferences = {
            "location": "HSR"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "location",
            result["matched_preferences"]
        )

    # -------------------------
    # LOCATION MISMATCH
    # -------------------------
    def test_location_mismatch(self):

        preferences = {
            "location": "Koramangala"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "location",
            result["unmatched_preferences"]
        )

    # -------------------------
    # BUDGET MATCH
    # -------------------------
    def test_budget_match(self):

        preferences = {
            "max_rent": 30000
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "budget",
            result["matched_preferences"]
        )

    # -------------------------
    # BUDGET MISMATCH
    # -------------------------
    def test_budget_mismatch(self):

        preferences = {
            "max_rent": 20000
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "budget",
            result["unmatched_preferences"]
        )

    # -------------------------
    # MINIMUM BUDGET MATCH
    # -------------------------
    def test_minimum_budget_match(self):

        preferences = {
            "min_rent": 20000
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "minimum_budget",
            result["matched_preferences"]
        )

    # -------------------------
    # MINIMUM BUDGET MISMATCH
    # -------------------------
    def test_minimum_budget_mismatch(self):

        preferences = {
            "min_rent": 25000
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "minimum_budget",
            result["unmatched_preferences"]
        )

    # -------------------------
    # EXACT BEDROOM MATCH
    # -------------------------
    def test_exact_bedroom_match(self):

        preferences = {
            "bedrooms": 2,
            "bedroom_mode": "exact"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "bedrooms",
            result["matched_preferences"]
        )

    # -------------------------
    # EXACT BEDROOM MISMATCH
    # -------------------------
    def test_exact_bedroom_mismatch(self):

        preferences = {
            "bedrooms": 3,
            "bedroom_mode": "exact"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "bedrooms",
            result["unmatched_preferences"]
        )

    # -------------------------
    # MINIMUM BEDROOM MATCH
    # -------------------------
    def test_minimum_bedroom_match(self):

        preferences = {
            "bedrooms": 1,
            "bedroom_mode": "minimum"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "bedrooms",
            result["matched_preferences"]
        )

    # -------------------------
    # MINIMUM BEDROOM MISMATCH
    # -------------------------
    def test_minimum_bedroom_mismatch(self):

        preferences = {
            "bedrooms": 3,
            "bedroom_mode": "minimum"
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "bedrooms",
            result["unmatched_preferences"]
        )

    # -------------------------
    # FURNISHED MATCH
    # -------------------------
    def test_furnished_match(self):

        preferences = {
            "furnished": True
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "furnished",
            result["matched_preferences"]
        )

    # -------------------------
    # FURNISHED MISMATCH
    # -------------------------
    def test_furnished_mismatch(self):

        preferences = {
            "furnished": False
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "furnished",
            result["unmatched_preferences"]
        )

    # -------------------------
    # PARKING MATCH
    # -------------------------
    def test_parking_match(self):

        preferences = {
            "parking": False
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "parking",
            result["matched_preferences"]
        )

    # -------------------------
    # PARKING MISMATCH
    # -------------------------
    def test_parking_mismatch(self):

        preferences = {
            "parking": True
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertIn(
            "parking",
            result["unmatched_preferences"]
        )

    # -------------------------
    # SCORE RANGE
    # -------------------------
    def test_score_is_between_zero_and_hundred(self):

        preferences = {
            "location": "HSR",
            "max_rent": 25000,
            "min_rent": 20000,
            "bedrooms": 2,
            "bedroom_mode": "exact",
            "furnished": True,
            "parking": False,
            "priority": {
                "location": "must_have",
                "budget": "must_have",
                "bedrooms": "must_have",
                "furnished": "must_have",
                "parking": "must_have"
            }
        }

        result = calculate_house_score(
            self.house,
            preferences
        )

        self.assertGreaterEqual(
            result["score"],
            0
        )

        self.assertLessEqual(
            result["score"],
            100
        )
from django.test import TestCase

from rentals.models import House
from rentals.recommendations import calculate_house_score
from rentals.explanation import generate_house_explanation


class HouseExplanationTests(TestCase):

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
    # HELPER
    # -------------------------
    def generate_explanation(self, preferences):

        score_result = calculate_house_score(
            self.house,
            preferences
        )

        return generate_house_explanation(
            self.house,
            preferences,
            score_result
        )

    # -------------------------
    # ALL PREFERENCES MATCH
    # -------------------------
    def test_all_preferences_match(self):

        preferences = {
            "location": "HSR",
            "max_rent": 25000,
            "min_rent": 20000,
            "bedrooms": 2,
            "bedroom_mode": "exact",
            "furnished": True,
            "parking": False
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertIn(
            "Excellent match",
            explanation["summary"]
        )

        self.assertEqual(
            explanation["weaknesses"],
            []
        )

        self.assertGreater(
            len(explanation["strengths"]),
            0
        )

    # -------------------------
    # LOCATION EXPLANATION
    # -------------------------
    def test_location_match_explanation(self):

        preferences = {
            "location": "HSR"
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "location" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # LOCATION MISMATCH
    # -------------------------
    def test_location_mismatch_explanation(self):

        preferences = {
            "location": "Koramangala"
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "location" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

    # -------------------------
    # BUDGET EXPLANATION
    # -------------------------
    def test_budget_match_explanation(self):

        preferences = {
            "max_rent": 25000
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "budget" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # BUDGET MISMATCH
    # -------------------------
    def test_budget_mismatch_explanation(self):

        preferences = {
            "max_rent": 20000
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "budget" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

    # -------------------------
    # MINIMUM BUDGET
    # -------------------------
    def test_minimum_budget_explanation(self):

        preferences = {
            "min_rent": 20000
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "minimum budget" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # BEDROOM MATCH
    # -------------------------
    def test_bedroom_match_explanation(self):

        preferences = {
            "bedrooms": 2,
            "bedroom_mode": "exact"
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "bedroom" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # BEDROOM MISMATCH
    # -------------------------
    def test_bedroom_mismatch_explanation(self):

        preferences = {
            "bedrooms": 3,
            "bedroom_mode": "exact"
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "bedroom" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

    # -------------------------
    # MINIMUM BEDROOM MODE
    # -------------------------
    def test_minimum_bedroom_explanation(self):

        preferences = {
            "bedrooms": 1,
            "bedroom_mode": "minimum"
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "bedroom" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # FURNISHED MATCH
    # -------------------------
    def test_furnished_match_explanation(self):

        preferences = {
            "furnished": True
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "furnished" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # FURNISHED MISMATCH
    # -------------------------
    def test_furnished_mismatch_explanation(self):

        preferences = {
            "furnished": False
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "furnished" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

    # -------------------------
    # PARKING MATCH
    # -------------------------
    def test_parking_match_explanation(self):

        preferences = {
            "parking": False
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "parking" in strength.lower()
                for strength in explanation["strengths"]
            )
        )

    # -------------------------
    # PARKING MISMATCH
    # -------------------------
    def test_parking_mismatch_explanation(self):

        preferences = {
            "parking": True
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "parking" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

    # -------------------------
    # EXPLANATION STRUCTURE
    # -------------------------
    def test_explanation_has_required_structure(self):

        preferences = {
            "location": "HSR",
            "max_rent": 25000,
            "bedrooms": 2
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertIn(
            "summary",
            explanation
        )

        self.assertIn(
            "strengths",
            explanation
        )

        self.assertIn(
            "weaknesses",
            explanation
        )

        self.assertIsInstance(
            explanation["summary"],
            str
        )

        self.assertIsInstance(
            explanation["strengths"],
            list
        )

        self.assertIsInstance(
            explanation["weaknesses"],
            list
        )

    # -------------------------
    # MUST-HAVE FAILURE
    # -------------------------
    def test_must_have_failure_is_reflected(self):

        preferences = {
            "parking": True,
            "priority": {
                "parking": "must_have"
            }
        }

        explanation = self.generate_explanation(
            preferences
        )

        self.assertTrue(
            any(
                "parking" in weakness.lower()
                for weakness in explanation["weaknesses"]
            )
        )

        self.assertIn(
            "must-have",
            explanation["summary"].lower()
        )
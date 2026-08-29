from django.test import TestCase
from rest_framework.test import APIClient

from rentals.models import House


class RecommendationEdgeCaseTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        House.objects.create(
            title="2BHK HSR Apartment",
            location="HSR Layout",
            rent=23000,
            bedrooms=2,
            bathrooms=2,
            furnished=True,
            parking=False,
            area_sqft=1100
        )

        House.objects.create(
            title="3BHK HSR Premium Apartment",
            location="HSR Layout",
            rent=35000,
            bedrooms=3,
            bathrooms=3,
            furnished=True,
            parking=True,
            area_sqft=1600
        )

        House.objects.create(
            title="1BHK Koramangala Apartment",
            location="Koramangala",
            rent=18000,
            bedrooms=1,
            bathrooms=1,
            furnished=False,
            parking=False,
            area_sqft=700
        )

    # -------------------------
    # TOP N = 1
    # -------------------------
    def test_top_n_one(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "top_n": 1
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["returned_count"],
            1
        )

    # -------------------------
    # TOP N = 100
    # -------------------------
    def test_top_n_maximum(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "top_n": 100
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertLessEqual(
            response.data["returned_count"],
            100
        )

    # -------------------------
    # ZERO TOP N
    # -------------------------
    def test_top_n_zero_is_rejected(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "top_n": 0
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

    # -------------------------
    # ZERO MAX RENT
    # -------------------------
    def test_zero_max_rent(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "max_rent": 0
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["recommendations"],
            []
        )

    # -------------------------
    # ZERO MIN RENT
    # -------------------------
    def test_zero_min_rent(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "min_rent": 0
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertGreater(
            response.data["total_matches"],
            0
        )

    # -------------------------
    # EQUAL MIN/MAX RENT
    # -------------------------
    def test_equal_min_and_max_rent(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "min_rent": 23000,
                "max_rent": 23000
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        for recommendation in response.data[
            "recommendations"
        ]:

            self.assertEqual(
                recommendation["house"]["rent"],
                23000
            )

    # -------------------------
    # VERY LARGE BUDGET
    # -------------------------
    def test_very_large_max_rent(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "max_rent": 100000000,
                "top_n": 100
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertGreater(
            response.data["total_matches"],
            0
        )

    # -------------------------
    # LARGE BEDROOM REQUEST
    # -------------------------
    def test_no_match_for_unrealistic_bedrooms(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "bedrooms": 100,
                "bedroom_mode": "exact"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["recommendations"],
            []
        )

    # -------------------------
    # EMPTY PREFERENCES
    # -------------------------
    def test_empty_preferences(self):

        response = self.client.post(
            "/api/recommendations/",
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertGreater(
            response.data["total_matches"],
            0
        )

    # -------------------------
    # MINIMUM BEDROOM + EXTRA
    # -------------------------
    def test_minimum_bedroom_allows_extra_bedrooms(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "bedrooms": 2,
                "bedroom_mode": "minimum",
                "top_n": 100
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        for recommendation in response.data[
            "recommendations"
        ]:

            self.assertGreaterEqual(
                recommendation["house"]["bedrooms"],
                2
            )

    # -------------------------
    # OPTIONAL PARKING
    # -------------------------
    def test_optional_parking_does_not_filter(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "parking": True,
                "required_parking": False,
                "top_n": 100
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        # Houses without parking are still allowed
        # because parking is only a scoring preference.
        self.assertGreater(
            response.data["total_matches"],
            0
        )

    # -------------------------
    # REQUIRED PARKING
    # -------------------------
    def test_required_parking_filters_non_parking_houses(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "required_parking": True,
                "top_n": 100
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        for recommendation in response.data[
            "recommendations"
        ]:

            self.assertTrue(
                recommendation["house"]["parking"]
            )

    # -------------------------
    # PRIORITY VALID COMBINATION
    # -------------------------
    def test_multiple_priority_levels(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "bedrooms": 2,
                "priority": {
                    "location": "must_have",
                    "budget": "important",
                    "bedrooms": "important",
                    "furnished": "preferred",
                    "parking": "optional"
                },
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertGreater(
            response.data["returned_count"],
            0
        )

    # -------------------------
    # BUDGET FALLBACK BOUNDARY
    # -------------------------
    def test_budget_fallback_does_not_exceed_30_percent(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 18000,
                "bedrooms": 2,
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        if response.data["budget_relaxed"]:

            self.assertLessEqual(
                response.data["relaxed_max_rent"],
                18000 * 1.30
            )

    # -------------------------
    # FALLBACK PRESERVES BEDROOM
    # -------------------------
    def test_budget_fallback_preserves_bedroom_filter(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 18000,
                "bedrooms": 2,
                "bedroom_mode": "exact",
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        for recommendation in response.data[
            "recommendations"
        ]:

            self.assertEqual(
                recommendation["house"]["bedrooms"],
                2
            )

    # -------------------------
    # FALLBACK PRESERVES LOCATION
    # -------------------------
    def test_budget_fallback_preserves_location(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 18000,
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        for recommendation in response.data[
            "recommendations"
        ]:

            self.assertIn(
                "HSR",
                recommendation["house"]["location"]
            )
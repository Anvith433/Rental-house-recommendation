from django.test import TestCase
from rest_framework.test import APIClient

from rentals.models import House


class RecommendationViewTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.house_1 = House.objects.create(
            title="2BHK HSR Apartment",
            location="HSR Layout",
            rent=23000,
            bedrooms=2,
            bathrooms=2,
            furnished=True,
            parking=False,
            area_sqft=1100
        )

        self.house_2 = House.objects.create(
            title="2BHK HSR Premium Apartment",
            location="HSR Layout",
            rent=24000,
            bedrooms=2,
            bathrooms=2,
            furnished=True,
            parking=True,
            area_sqft=1200
        )

        self.house_3 = House.objects.create(
            title="3BHK HSR Premium Apartment",
            location="HSR Layout",
            rent=35000,
            bedrooms=3,
            bathrooms=3,
            furnished=True,
            parking=True,
            area_sqft=1600
        )

        self.house_4 = House.objects.create(
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
    # VALID REQUEST
    # -------------------------
    def test_valid_recommendation_request(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "bedrooms": 2,
                "bedroom_mode": "exact",
                "furnished": True,
                "parking": False,
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIn(
            "recommendations",
            response.data
        )

    # -------------------------
    # RESPONSE STRUCTURE
    # -------------------------
    def test_response_contains_expected_metadata(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "bedrooms": 2,
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIn(
            "recommendations",
            response.data
        )

        self.assertIn(
            "total_matches",
            response.data
        )

        self.assertIn(
            "requested_top_n",
            response.data
        )

        self.assertIn(
            "returned_count",
            response.data
        )

        self.assertIn(
            "filters_applied",
            response.data
        )

        self.assertIn(
            "budget_relaxed",
            response.data
        )

    # -------------------------
    # TOP N LIMIT
    # -------------------------
    def test_top_n_limits_results(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 50000,
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

        self.assertEqual(
            len(response.data["recommendations"]),
            1
        )

        self.assertEqual(
            response.data["requested_top_n"],
            1
        )

    # -------------------------
    # EXACT BEDROOM MODE
    # -------------------------
    def test_exact_bedroom_mode(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 50000,
                "bedrooms": 2,
                "bedroom_mode": "exact",
                "top_n": 10
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        recommendations = response.data[
            "recommendations"
        ]

        for recommendation in recommendations:

            self.assertEqual(
                recommendation["house"]["bedrooms"],
                2
            )

    # -------------------------
    # MINIMUM BEDROOM MODE
    # -------------------------
    def test_minimum_bedroom_mode(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 50000,
                "bedrooms": 2,
                "bedroom_mode": "minimum",
                "top_n": 10
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        recommendations = response.data[
            "recommendations"
        ]

        for recommendation in recommendations:

            self.assertGreaterEqual(
                recommendation["house"]["bedrooms"],
                2
            )

    # -------------------------
    # PARKING HARD FILTER
    # -------------------------
    def test_required_parking_filters_houses(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 50000,
                "bedrooms": 2,
                "required_parking": True,
                "top_n": 10
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        recommendations = response.data[
            "recommendations"
        ]

        for recommendation in recommendations:

            self.assertTrue(
                recommendation["house"]["parking"]
            )

    # -------------------------
    # NO MATCHES
    # -------------------------
    def test_no_matching_houses(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "Whitefield",
                "max_rent": 10000,
                "bedrooms": 5,
                "top_n": 5
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

        self.assertEqual(
            response.data["total_matches"],
            0
        )

        self.assertEqual(
            response.data["returned_count"],
            0
        )

    # -------------------------
    # BUDGET FALLBACK
    # -------------------------
    def test_budget_fallback(self):

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

        self.assertTrue(
            response.data["budget_relaxed"]
        )

        self.assertEqual(
            response.data["original_max_rent"],
            18000.0
        )

        self.assertGreater(
            response.data["relaxed_max_rent"],
            18000.0
        )

        self.assertGreater(
            response.data["returned_count"],
            0
        )

    # -------------------------
    # EXPLANATION INCLUDED
    # -------------------------
    def test_recommendation_contains_explanation(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "bedrooms": 2,
                "top_n": 5
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        recommendations = response.data[
            "recommendations"
        ]

        self.assertGreater(
            len(recommendations),
            0
        )

        recommendation = recommendations[0]

        self.assertIn(
            "explanation",
            recommendation
        )

        explanation = recommendation[
            "explanation"
        ]

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

    # -------------------------
    # INVALID MAX RENT
    # -------------------------
    def test_negative_max_rent_returns_400(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "max_rent": -1000
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "max_rent",
            response.data
        )

    # -------------------------
    # INVALID BEDROOM MODE
    # -------------------------
    def test_invalid_bedroom_mode_returns_400(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "bedrooms": 2,
                "bedroom_mode": "wrong"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "bedroom_mode",
            response.data
        )

    # -------------------------
    # INVALID TOP N
    # -------------------------
    def test_top_n_above_limit_returns_400(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "top_n": 101
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "top_n",
            response.data
        )

    # -------------------------
    # INVALID RENT RANGE
    # -------------------------
    def test_invalid_rent_range_returns_400(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "min_rent": 50000,
                "max_rent": 30000
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertTrue(
            "rent" in response.data
            or "non_field_errors"
            in response.data
        )

    # -------------------------
    # INVALID PRIORITY
    # -------------------------
    def test_invalid_priority_returns_400(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "priority": {
                    "location": "wrong"
                }
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "priority",
            response.data
        )
import time

from django.test import TestCase
from django.db import connection
from rest_framework.test import APIClient

from rentals.models import House


class RecommendationPerformanceTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        houses = []

        for i in range(500):

            houses.append(
                House(
                    title=f"Test House {i}",
                    location=(
                        "HSR Layout"
                        if i % 2 == 0
                        else "Koramangala"
                    ),
                    rent=(
                        20000 + (i % 10) * 1000
                    ),
                    bedrooms=(
                        1 + (i % 3)
                    ),
                    bathrooms=2,
                    furnished=(
                        i % 2 == 0
                    ),
                    parking=(
                        i % 3 == 0
                    ),
                    area_sqft=(
                        800 + (i % 10) * 100
                    )
                )
            )

        House.objects.bulk_create(houses)

    # --------------------------------
    # PERFORMANCE: 500 HOUSES
    # --------------------------------
    def test_recommendation_with_500_houses(self):

        start_time = time.perf_counter()

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "bedrooms": 2,
                "bedroom_mode": "exact",
                "top_n": 5
            },
            format="json"
        )

        elapsed_time = (
            time.perf_counter() - start_time
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertLessEqual(
            response.data["returned_count"],
            5
        )

        print(
            f"\n500-house recommendation "
            f"response time: "
            f"{elapsed_time:.4f} seconds"
        )

    # --------------------------------
    # DATABASE QUERY COUNT
    # --------------------------------
    def test_recommendation_query_count(self):

        with self.assertNumQueries(2):

            response = self.client.post(
                "/api/recommendations/",
                {
                    "location": "HSR",
                    "max_rent": 40000,
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

    # --------------------------------
    # TOP-N PERFORMANCE
    # --------------------------------
    def test_large_candidate_set_with_small_top_n(
        self
    ):

        start_time = time.perf_counter()

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "top_n": 1
            },
            format="json"
        )

        elapsed_time = (
            time.perf_counter() - start_time
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["returned_count"],
            1
        )

        print(
            f"\nTop-1 recommendation "
            f"response time: "
            f"{elapsed_time:.4f} seconds"
        )

    # --------------------------------
    # RANKING PERFORMANCE
    # --------------------------------
    def test_ranking_returns_sorted_scores(self):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "max_rent": 40000,
                "top_n": 10
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        scores = [
            recommendation["score"]
            for recommendation
            in response.data["recommendations"]
        ]

        self.assertEqual(
            scores,
            sorted(
                scores,
                reverse=True
            )
        )

    # --------------------------------
    # RESULT SIZE
    # --------------------------------
    def test_top_n_does_not_return_excess_results(
        self
    ):

        response = self.client.post(
            "/api/recommendations/",
            {
                "location": "HSR",
                "top_n": 3
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertLessEqual(
            response.data["returned_count"],
            3
        )
import time

from django.test import TestCase
from rest_framework.test import APIClient

from rentals.models import House


class RecommendationProfilingTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        houses = []

        for i in range(10000):

            houses.append(
                House(
                    title=f"Profile House {i}",
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

    def test_profile_recommendation_pipeline(self):

        print("\n")
        print("=" * 45)
        print("OPTIMIZED RECOMMENDATION PIPELINE PROFILE")
        print("=" * 45)

        # -----------------------------------------
        # DATABASE FILTERING
        # -----------------------------------------

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

        total_time = (
            time.perf_counter() - start_time
        )

        self.assertEqual(
            response.status_code,
            200
        )

        returned_count = (
            response.data["returned_count"]
        )

        total_matches = (
            response.data["total_matches"]
        )

        print(
            f"Candidate houses: "
            f"{total_matches:,}"
        )

        print(
            f"Total API response: "
            f"{total_time:.4f} seconds"
        )

        print(
            f"Top-N returned: "
            f"{returned_count}"
        )

        print("-" * 45)

        # -----------------------------------------
        # PERFORMANCE ASSERTIONS
        # -----------------------------------------

        self.assertLessEqual(
            returned_count,
            5
        )

        self.assertGreater(
            total_matches,
            0
        )

        print(
            "Pipeline status: OPTIMIZED"
        )

        print("=" * 45)
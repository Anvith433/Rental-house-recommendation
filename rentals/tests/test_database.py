from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIClient

from rentals.models import House


class RecommendationDatabaseTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        houses = []

        for i in range(100):

            houses.append(
                House(
                    title=f"Database Test House {i}",
                    location="HSR Layout",
                    rent=20000 + (i % 5) * 1000,
                    bedrooms=2,
                    bathrooms=2,
                    furnished=True,
                    parking=(i % 2 == 0),
                    area_sqft=1000 + i
                )
            )

        House.objects.bulk_create(houses)

    def test_recommendation_query_count(self):

        with CaptureQueriesContext(connection) as context:

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

        print(
            f"\nRecommendation DB queries: "
            f"{len(context.captured_queries)}"
        )

        for index, query in enumerate(
            context.captured_queries,
            start=1
        ):

            print(
                f"\nQUERY {index}:\n"
                f"{query['sql']}"
            )
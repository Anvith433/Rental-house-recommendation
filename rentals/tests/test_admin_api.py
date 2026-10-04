from django.test import TestCase

from rentals.models import Favorite, Inquiry, PropertyInteraction, RecommendationHistory

from .factories import auth_client, make_house, make_user


class AdminAnalyticsTests(TestCase):
    def setUp(self):
        self.admin = make_user(admin=True)
        self.client = auth_client(self.admin)
        self.user = make_user()
        self.house = make_house(title="Most loved home")
        make_house(title="Hidden listing", status="inactive")
        make_house(title="Suspicious listing", status="flagged")
        Favorite.objects.create(user=self.user, property=self.house)
        PropertyInteraction.objects.create(user=self.user, property=self.house, interaction_type="VIEW")
        RecommendationHistory.objects.create(
            user=self.user, request_preferences={}, total_matches=4, latency_ms=12.5, budget_relaxed=True
        )
        RecommendationHistory.objects.create(
            user=self.user, request_preferences={}, total_matches=2, latency_ms=7.5
        )

    def test_analytics_totals(self):
        response = self.client.get("/api/admin/analytics/")
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["users"]["total"], 2)
        self.assertEqual(data["properties"]["total"], 3)
        self.assertEqual(data["properties"]["active"], 1)
        self.assertEqual(data["properties"]["flagged"], 1)
        self.assertEqual(data["favorites"]["total"], 1)
        self.assertEqual(data["recommendations"]["total"], 2)
        self.assertEqual(data["recommendations"]["average_latency_ms"], 10.0)
        self.assertEqual(data["recommendations"]["average_candidates"], 3.0)
        self.assertEqual(data["recommendations"]["budget_relaxation_rate"], 0.5)
        self.assertEqual(len(data["recommendation_trend"]), 14)
        self.assertEqual(data["recommendation_trend"][-1]["count"], 2)
        self.assertEqual(data["most_favorited"][0]["id"], self.house.id)
        self.assertEqual(data["most_viewed"][0]["views_total"], 1)
        self.assertIn("engine_metrics", data)

    def test_admin_property_list_includes_all_statuses_and_counts(self):
        response = self.client.get("/api/admin/properties/")
        self.assertEqual(response.data["count"], 3)
        loved = next(p for p in response.data["results"] if p["id"] == self.house.id)
        self.assertEqual(loved["favorites_count"], 1)
        self.assertEqual(loved["views_count"], 1)

    def test_admin_property_list_filters_by_status(self):
        response = self.client.get("/api/admin/properties/", {"status": "flagged"})
        self.assertEqual([p["title"] for p in response.data["results"]], ["Suspicious listing"])

    def test_admin_manages_inquiries(self):
        inquiry = Inquiry.objects.create(user=self.user, property=self.house, message="Still available?")
        listed = self.client.get("/api/admin/inquiries/")
        self.assertEqual(listed.data["results"][0]["user_email"], self.user.email)
        response = self.client.patch(f"/api/admin/inquiries/{inquiry.id}/", {"status": "responded", "message": "edited"})
        self.assertEqual(response.status_code, 200)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, "responded")
        self.assertEqual(inquiry.message, "Still available?")

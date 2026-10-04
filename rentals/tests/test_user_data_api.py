from django.test import TestCase
from rest_framework.test import APIClient

from rentals.models import Favorite, PropertyInteraction, RecommendationHistory, UserPreference

from .factories import auth_client, make_house, make_user


class FavoriteTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other = make_user()
        self.client = auth_client(self.user)
        self.house = make_house(image_url="/fav.svg")

    def url(self, pk):
        return f"/api/favorites/{pk}/"

    def test_favorites_require_authentication(self):
        anon = APIClient()
        self.assertEqual(anon.get("/api/favorites/").status_code, 401)
        self.assertEqual(anon.post(self.url(self.house.id)).status_code, 401)
        self.assertEqual(anon.delete(self.url(self.house.id)).status_code, 401)

    def test_add_favorite_is_idempotent(self):
        self.assertEqual(self.client.post(self.url(self.house.id)).status_code, 201)
        self.assertEqual(self.client.post(self.url(self.house.id)).status_code, 200)
        self.assertEqual(Favorite.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            PropertyInteraction.objects.filter(user=self.user, interaction_type="FAVORITE").count(), 1
        )

    def test_list_contains_only_own_favorites_with_property_summary(self):
        self.client.post(self.url(self.house.id))
        other_house = make_house(title="Someone else's favourite")
        auth_client(self.other).post(self.url(other_house.id))

        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        favorite = response.data["results"][0]
        self.assertEqual(favorite["property"]["id"], self.house.id)
        self.assertEqual(favorite["property"]["primary_image"], "/fav.svg")
        self.assertEqual(self.client.get("/api/favorites/ids/").data["ids"], [self.house.id])

    def test_remove_favorite(self):
        self.client.post(self.url(self.house.id))
        self.assertEqual(self.client.delete(self.url(self.house.id)).status_code, 204)
        self.assertFalse(Favorite.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.delete(self.url(self.house.id)).status_code, 404)

    def test_user_cannot_remove_another_users_favorite(self):
        auth_client(self.other).post(self.url(self.house.id))
        self.assertEqual(self.client.delete(self.url(self.house.id)).status_code, 404)
        self.assertTrue(Favorite.objects.filter(user=self.other, property=self.house).exists())

    def test_cannot_favorite_missing_or_inactive_property(self):
        inactive = make_house(status="inactive")
        self.assertEqual(self.client.post(self.url(999999)).status_code, 404)
        self.assertEqual(self.client.post(self.url(inactive.id)).status_code, 404)

    def test_favorites_list_query_count_is_constant(self):
        for index in range(10):
            house = make_house(title=f"Saved home {index}", image_url=f"/{index}.svg")
            Favorite.objects.create(user=self.user, property=house)
        # auth user lookup + count + favorites page + properties (with image subquery)
        with self.assertNumQueries(4):
            self.client.get("/api/favorites/")


class PreferenceTests(TestCase):
    URL = "/api/preferences/"

    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_get_returns_defaults_before_saving(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["updated_at"])
        self.assertEqual(response.data["bedroom_mode"], "exact")

    def test_put_creates_then_replaces(self):
        payload = {
            "location": "HSR Layout",
            "min_rent": 15000,
            "max_rent": 30000,
            "bedrooms": 2,
            "bedroom_mode": "minimum",
            "furnished": True,
            "parking": None,
            "required_parking": False,
            "priority": {"location": "must_have", "budget": "important"},
        }
        response = self.client.put(self.URL, payload)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["priority"], {"location": "must_have", "budget": "important"})

        response = self.client.put(self.URL, {"location": "Whitefield"})
        self.assertEqual(response.status_code, 200)
        preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(preference.location, "Whitefield")
        self.assertIsNone(preference.max_rent)  # PUT resets unspecified fields

    def test_patch_updates_single_field(self):
        self.client.put(self.URL, {"location": "HSR", "max_rent": 30000})
        self.client.patch(self.URL, {"max_rent": 35000})
        preference = UserPreference.objects.get(user=self.user)
        self.assertEqual((preference.location, preference.max_rent), ("HSR", 35000))

    def test_validation(self):
        for payload, field in (
            ({"min_rent": 40000, "max_rent": 30000}, "rent"),
            ({"max_rent": -1}, "max_rent"),
            ({"bedrooms": 0}, "bedrooms"),
            ({"bedroom_mode": "approximately"}, "bedroom_mode"),
            ({"priority": {"location": "critical"}}, "priority"),
        ):
            with self.subTest(payload=payload):
                response = self.client.put(self.URL, payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["error"]["details"])

    def test_preferences_are_private(self):
        self.client.put(self.URL, {"location": "Secret Street"})
        other = auth_client(make_user())
        self.assertEqual(other.get(self.URL).data["location"], "")
        self.assertEqual(APIClient().get(self.URL).status_code, 401)


class RecommendationHistoryTests(TestCase):
    URL = "/api/recommendations/history/"

    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)
        self.house = make_house()

    def recommend(self, client, **payload):
        return client.post("/api/recommendations/", {"location": "HSR", "top_n": 3, **payload})

    def test_signed_in_requests_are_recorded(self):
        self.recommend(self.client, max_rent=30000)
        entry = RecommendationHistory.objects.get(user=self.user)
        self.assertEqual(entry.result_property_ids, [self.house.id])
        self.assertEqual(entry.request_preferences["max_rent"], 30000.0)
        self.assertEqual(entry.total_matches, 1)
        self.assertGreater(entry.top_score, 0)

    def test_anonymous_requests_are_not_recorded(self):
        self.recommend(APIClient())
        self.assertEqual(RecommendationHistory.objects.count(), 0)

    def test_history_lists_own_entries_with_result_summaries(self):
        self.recommend(self.client)
        self.recommend(auth_client(make_user()))
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["results"][0]["id"], self.house.id)

    def test_history_requires_authentication(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_clear_history_only_affects_own_entries(self):
        self.recommend(self.client)
        other = make_user()
        self.recommend(auth_client(other))
        self.assertEqual(self.client.delete(self.URL).status_code, 204)
        self.assertFalse(RecommendationHistory.objects.filter(user=self.user).exists())
        self.assertTrue(RecommendationHistory.objects.filter(user=other).exists())

    def test_signed_in_recommendation_adds_exactly_one_write(self):
        # 1 auth lookup + 2 pipeline queries + 1 history insert
        with self.assertNumQueries(4):
            self.recommend(self.client, max_rent=30000)

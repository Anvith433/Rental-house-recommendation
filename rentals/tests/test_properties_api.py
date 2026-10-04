from django.test import TestCase
from rest_framework.test import APIClient

from rentals.models import House, PropertyInteraction, UserPreference

from .factories import auth_client, make_house, make_user, property_payload

LIST_URL = "/api/properties/"


def detail_url(pk):
    return f"{LIST_URL}{pk}/"


class PropertySearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hsr = make_house(
            title="2BHK HSR Apartment", location="HSR Layout", rent=23000, image_url="/a.svg"
        )
        self.kora = make_house(
            title="1BHK Koramangala Studio",
            location="Koramangala",
            rent=18000,
            bedrooms=1,
            bathrooms=1,
            furnished=False,
            area_sqft=600,
            property_type="studio",
        )
        self.villa = make_house(
            title="4BHK Whitefield Villa",
            location="Whitefield",
            rent=90000,
            bedrooms=4,
            bathrooms=4,
            parking=True,
            area_sqft=3200,
            property_type="villa",
        )
        self.inactive = make_house(title="Old listing", status="inactive")

    def ids(self, response):
        return [item["id"] for item in response.data["results"]]

    def test_list_is_public_paginated_and_hides_inactive(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertNotIn(self.inactive.id, self.ids(response))
        self.assertIn("next", response.data)

    def test_list_returns_primary_image_without_full_image_set(self):
        response = self.client.get(LIST_URL, {"location": "HSR"})
        item = response.data["results"][0]
        self.assertEqual(item["primary_image"], "/a.svg")
        self.assertNotIn("images", item)
        self.assertNotIn("description", item)

    def test_list_uses_constant_number_of_queries(self):
        for index in range(15):
            make_house(title=f"Extra listing {index}", image_url=f"/{index}.svg")
        with self.assertNumQueries(2):  # count + page (images via subquery)
            self.client.get(LIST_URL, {"page_size": 20})

    def test_filter_by_location_rent_and_bedrooms(self):
        response = self.client.get(LIST_URL, {"location": "HSR", "max_rent": 30000, "bedrooms": 2})
        self.assertEqual(self.ids(response), [self.hsr.id])

    def test_location_filter_matches_city(self):
        response = self.client.get(LIST_URL, {"location": "bangalore"})
        self.assertEqual(response.data["count"], 3)

    def test_rent_range_filters(self):
        response = self.client.get(LIST_URL, {"min_rent": 20000, "max_rent": 50000})
        self.assertEqual(self.ids(response), [self.hsr.id])

    def test_boolean_type_and_area_filters(self):
        self.assertEqual(self.ids(self.client.get(LIST_URL, {"parking": "true"})), [self.villa.id])
        self.assertEqual(self.ids(self.client.get(LIST_URL, {"furnished": "false"})), [self.kora.id])
        self.assertEqual(
            self.ids(self.client.get(LIST_URL, {"property_type": "villa"})), [self.villa.id]
        )
        self.assertEqual(
            sorted(self.ids(self.client.get(LIST_URL, {"min_area": 1000}))),
            sorted([self.hsr.id, self.villa.id]),
        )
        self.assertEqual(self.ids(self.client.get(LIST_URL, {"bathrooms": 3})), [self.villa.id])

    def test_search_matches_title(self):
        response = self.client.get(LIST_URL, {"search": "villa"})
        self.assertEqual(self.ids(response), [self.villa.id])

    def test_ordering_by_rent(self):
        ascending = self.ids(self.client.get(LIST_URL, {"ordering": "rent"}))
        self.assertEqual(ascending, [self.kora.id, self.hsr.id, self.villa.id])
        descending = self.ids(self.client.get(LIST_URL, {"ordering": "-rent"}))
        self.assertEqual(descending, list(reversed(ascending)))

    def test_invalid_filters_return_400(self):
        for params in (
            {"max_rent": -5},
            {"max_rent": "cheap"},
            {"bedrooms": 99},
            {"property_type": "castle"},
            {"furnished": "maybe"},
            {"available_by": "not-a-date"},
        ):
            with self.subTest(params=params):
                response = self.client.get(LIST_URL, params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["error"]["code"], "INVALID_REQUEST")

    def test_page_size_is_capped(self):
        for index in range(60):
            make_house(title=f"Bulk listing number {index}")
        response = self.client.get(LIST_URL, {"page_size": 1000})
        self.assertEqual(len(response.data["results"]), 50)

    def test_out_of_range_page_returns_404(self):
        response = self.client.get(LIST_URL, {"page": 999})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "NOT_FOUND")

    def test_inactive_detail_is_hidden_from_users(self):
        self.assertEqual(self.client.get(detail_url(self.inactive.id)).status_code, 404)

    def test_admin_sees_inactive_with_status_filter(self):
        admin = auth_client(make_user(admin=True))
        response = admin.get(LIST_URL, {"status": "inactive"})
        self.assertEqual(self.ids(response), [self.inactive.id])
        self.assertEqual(admin.get(detail_url(self.inactive.id)).status_code, 200)

    def test_status_filter_does_not_reveal_inactive_to_users(self):
        response = self.client.get(LIST_URL, {"status": "inactive"})
        self.assertEqual(response.data["count"], 0)

    def test_locations_endpoint_counts_active_listings(self):
        response = self.client.get(f"{LIST_URL}locations/")
        self.assertEqual(response.status_code, 200)
        locations = {row["location"]: row["count"] for row in response.data}
        self.assertEqual(locations["HSR Layout"], 2 - 1)  # inactive listing excluded
        self.assertEqual(set(locations), {"HSR Layout", "Koramangala", "Whitefield"})

    def test_legacy_houses_endpoint_still_works(self):
        response = self.client.get("/api/houses/", {"location": "HSR"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ids(response), [self.hsr.id])


class PropertyDetailTests(TestCase):
    def setUp(self):
        self.house = make_house(title="2BHK HSR Apartment", image_url="/primary.svg")
        self.user = make_user()

    def test_detail_includes_images_and_full_fields(self):
        response = APIClient().get(detail_url(self.house.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["images"][0]["image_url"], "/primary.svg")
        self.assertIn("description", response.data)
        self.assertNotIn("owner", response.data)
        self.assertNotIn("match", response.data)

    def test_detail_records_view_for_signed_in_user(self):
        auth_client(self.user).get(detail_url(self.house.id))
        self.assertTrue(
            PropertyInteraction.objects.filter(
                user=self.user, property=self.house, interaction_type="VIEW"
            ).exists()
        )

    def test_detail_includes_match_against_saved_preferences(self):
        UserPreference.objects.create(
            user=self.user, location="HSR", max_rent=25000, bedrooms=2, furnished=True
        )
        response = auth_client(self.user).get(detail_url(self.house.id))
        match = response.data["match"]
        self.assertGreater(match["score"], 0)
        self.assertIn("location", match["matched_preferences"])
        self.assertIn("summary", match["explanation"])

    def test_invalid_id_returns_404(self):
        self.assertEqual(APIClient().get(detail_url("abc")).status_code, 404)
        self.assertEqual(APIClient().get(detail_url(999999)).status_code, 404)


class PropertyManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user(admin=True)
        self.admin_client = auth_client(self.admin)
        self.user_client = auth_client(make_user())

    def test_admin_creates_property_with_images(self):
        response = self.admin_client.post(LIST_URL, property_payload())
        self.assertEqual(response.status_code, 201, response.data)
        house = House.objects.get(pk=response.data["id"])
        self.assertEqual(house.owner, self.admin)
        self.assertEqual(house.images.count(), 2)
        self.assertEqual(response.data["primary_image"], "/images/properties/apartment-1.svg")
        self.assertEqual(response.data["amenities"], ["gym", "lift"])

    def test_normal_user_cannot_create_update_or_delete(self):
        house = make_house()
        self.assertEqual(self.user_client.post(LIST_URL, property_payload()).status_code, 403)
        self.assertEqual(
            self.user_client.patch(detail_url(house.id), {"rent": 1}).status_code, 403
        )
        self.assertEqual(self.user_client.delete(detail_url(house.id)).status_code, 403)
        self.assertTrue(House.objects.filter(pk=house.pk, rent=23000).exists())

    def test_anonymous_cannot_write(self):
        self.assertEqual(APIClient().post(LIST_URL, property_payload()).status_code, 401)

    def test_admin_updates_and_replaces_images(self):
        house = self.admin_client.post(LIST_URL, property_payload()).data
        response = self.admin_client.patch(
            detail_url(house["id"]),
            {"rent": 30000, "images": [{"image_url": "/new.svg", "caption": "New"}]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rent"], 30000)
        self.assertEqual([img["image_url"] for img in response.data["images"]], ["/new.svg"])
        self.assertTrue(response.data["images"][0]["is_primary"])

    def test_admin_deactivates_property(self):
        house = make_house()
        response = self.admin_client.patch(detail_url(house.id), {"status": "inactive"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(APIClient().get(detail_url(house.id)).status_code, 404)

    def test_admin_deletes_property(self):
        house = make_house()
        self.assertEqual(self.admin_client.delete(detail_url(house.id)).status_code, 204)
        self.assertFalse(House.objects.filter(pk=house.pk).exists())

    def test_validation_rejects_bad_values(self):
        cases = {
            "rent": {"rent": -100},
            "bedrooms": {"bedrooms": 50},
            "latitude": {"latitude": "123.0"},
            "longitude": {"longitude": "-200"},
            "property_type": {"property_type": "castle"},
            "amenities": {"amenities": ["helipad"]},
            "floor": {"floor": 10, "total_floors": 4},
            "area_sqft": {"area_sqft": 0},
            "status": {"status": "sold"},
            "title": {"title": ""},
        }
        for field, override in cases.items():
            with self.subTest(field=field):
                response = self.admin_client.post(LIST_URL, property_payload(**override))
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["error"]["details"])

    def test_unsafe_image_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "data:text/html;base64,xx", "//evil.com/x.png", "a b"):
            with self.subTest(url=url):
                response = self.admin_client.post(
                    LIST_URL, property_payload(images=[{"image_url": url}])
                )
                self.assertEqual(response.status_code, 400)

    def test_only_one_primary_image_allowed(self):
        response = self.admin_client.post(
            LIST_URL,
            property_payload(
                images=[
                    {"image_url": "/a.svg", "is_primary": True},
                    {"image_url": "/b.svg", "is_primary": True},
                ]
            ),
        )
        self.assertEqual(response.status_code, 400)


class CompareTests(TestCase):
    def setUp(self):
        self.houses = [make_house(title=f"Comparable home {i}", rent=20000 + i) for i in range(5)]
        self.url = f"{LIST_URL}compare/"

    def test_compare_returns_properties_in_requested_order(self):
        ids = [self.houses[2].id, self.houses[0].id]
        response = APIClient().get(self.url, {"ids": ",".join(map(str, ids))})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["id"] for p in response.data["properties"]], ids)
        self.assertFalse(response.data["has_saved_preferences"])

    def test_compare_requires_two_to_four_ids(self):
        self.assertEqual(APIClient().get(self.url, {"ids": str(self.houses[0].id)}).status_code, 400)
        five = ",".join(str(h.id) for h in self.houses)
        self.assertEqual(APIClient().get(self.url, {"ids": five}).status_code, 400)
        self.assertEqual(APIClient().get(self.url).status_code, 400)

    def test_compare_rejects_malformed_ids(self):
        self.assertEqual(APIClient().get(self.url, {"ids": "1,abc"}).status_code, 400)

    def test_compare_includes_match_scores_for_saved_preferences(self):
        user = make_user()
        UserPreference.objects.create(user=user, location="HSR", max_rent=30000)
        ids = f"{self.houses[0].id},{self.houses[1].id}"
        response = auth_client(user).get(self.url, {"ids": ids})
        self.assertTrue(response.data["has_saved_preferences"])
        self.assertEqual(set(response.data["matches"]), {str(self.houses[0].id), str(self.houses[1].id)})


class InquiryTests(TestCase):
    def setUp(self):
        self.house = make_house()
        self.user = make_user()
        self.url = f"{detail_url(self.house.id)}inquiries/"

    def test_inquiry_requires_authentication(self):
        response = APIClient().post(self.url, {"message": "Is this still available?"})
        self.assertEqual(response.status_code, 401)

    def test_user_creates_inquiry_and_contact_interaction(self):
        response = auth_client(self.user).post(
            self.url, {"message": "Is this still available next month?", "phone": "+91 98450 12345"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "new")
        self.assertTrue(
            PropertyInteraction.objects.filter(user=self.user, interaction_type="CONTACT").exists()
        )

    def test_inquiry_validation(self):
        client = auth_client(self.user)
        self.assertEqual(client.post(self.url, {"message": "hi"}).status_code, 400)
        self.assertEqual(
            client.post(self.url, {"message": "x" * 2001}).status_code, 400
        )
        self.assertEqual(
            client.post(self.url, {"message": "Long enough message", "phone": "abc"}).status_code,
            400,
        )

from django.test import TestCase
from rest_framework.test import APIClient

from rentals.tests.factories import auth_client, make_user

USERS_URL = "/api/admin/users/"


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user(email="admin@example.com", admin=True)
        self.user = make_user(email="user@example.com")
        self.admin_client = auth_client(self.admin)

    def test_normal_user_cannot_list_users(self):
        response = auth_client(self.user).get(USERS_URL)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"]["code"], "PERMISSION_DENIED")

    def test_anonymous_cannot_list_users(self):
        self.assertEqual(APIClient().get(USERS_URL).status_code, 401)

    def test_admin_lists_users_with_usage_counts(self):
        response = self.admin_client.get(USERS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertIn("favorites_count", response.data["results"][0])
        self.assertNotIn("password", response.data["results"][0])

    def test_admin_can_search_and_filter(self):
        response = self.admin_client.get(USERS_URL, {"search": "user@", "role": "USER"})
        self.assertEqual([u["email"] for u in response.data["results"]], ["user@example.com"])

    def test_admin_can_deactivate_user(self):
        response = self.admin_client.patch(f"{USERS_URL}{self.user.id}/", {"is_active": False})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_admin_can_promote_user(self):
        self.admin_client.patch(f"{USERS_URL}{self.user.id}/", {"role": "ADMIN"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "ADMIN")
        self.assertTrue(self.user.is_staff)
        self.assertEqual(auth_client(self.user).get(USERS_URL).status_code, 200)

    def test_admin_cannot_lock_themselves_out(self):
        url = f"{USERS_URL}{self.admin.id}/"
        self.assertEqual(self.admin_client.patch(url, {"is_active": False}).status_code, 400)
        self.assertEqual(self.admin_client.patch(url, {"role": "USER"}).status_code, 400)

    def test_admin_cannot_edit_user_profile_fields(self):
        self.admin_client.patch(f"{USERS_URL}{self.user.id}/", {"email": "changed@example.com"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "user@example.com")

    def test_users_cannot_be_deleted_via_api(self):
        response = self.admin_client.delete(f"{USERS_URL}{self.user.id}/")
        self.assertEqual(response.status_code, 405)

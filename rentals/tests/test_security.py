import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import path
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from rentals.models import Favorite, RecommendationHistory

from .factories import auth_client, make_house, make_user

BASE_DIR = Path(__file__).resolve().parents[2]


class ExplodingView(APIView):
    permission_classes: list = []

    def get(self, request):
        raise RuntimeError("database password is hunter2 at /srv/secret/path")


class ParamEchoView(APIView):
    permission_classes: list = []

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [
    path("boom/", ExplodingView.as_view()),
    path("echo/", ParamEchoView.as_view()),
]


class AuthenticationRequiredTests(TestCase):
    """Every private endpoint rejects anonymous requests with 401."""

    PRIVATE_ENDPOINTS = [
        ("get", "/api/users/me/"),
        ("patch", "/api/users/me/"),
        ("post", "/api/users/me/password/"),
        ("get", "/api/favorites/"),
        ("get", "/api/favorites/ids/"),
        ("post", "/api/favorites/1/"),
        ("delete", "/api/favorites/1/"),
        ("get", "/api/preferences/"),
        ("put", "/api/preferences/"),
        ("get", "/api/recommendations/history/"),
        ("delete", "/api/recommendations/history/"),
        ("post", "/api/properties/1/inquiries/"),
        ("get", "/api/admin/analytics/"),
        ("get", "/api/admin/users/"),
        ("get", "/api/admin/properties/"),
        ("get", "/api/admin/inquiries/"),
        ("post", "/api/properties/"),
    ]

    def test_private_endpoints_return_401(self):
        make_house()
        client = APIClient()
        for method, url in self.PRIVATE_ENDPOINTS:
            with self.subTest(method=method, url=url):
                response = getattr(client, method)(url, {})
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.data["error"]["code"], "NOT_AUTHENTICATED")

    def test_public_endpoints_are_open(self):
        house = make_house()
        client = APIClient()
        self.assertEqual(client.get("/api/properties/").status_code, 200)
        self.assertEqual(client.get(f"/api/properties/{house.id}/").status_code, 200)
        self.assertEqual(client.post("/api/recommendations/", {}).status_code, 200)
        self.assertEqual(client.get("/api/health/").status_code, 200)


class AuthorizationTests(TestCase):
    """Normal users are never admins, whatever the frontend shows."""

    ADMIN_ENDPOINTS = [
        ("get", "/api/admin/analytics/"),
        ("get", "/api/admin/users/"),
        ("get", "/api/admin/properties/"),
        ("get", "/api/admin/inquiries/"),
    ]

    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)
        self.house = make_house()

    def test_admin_endpoints_return_403_for_users(self):
        for method, url in self.ADMIN_ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 403)

    def test_user_cannot_modify_properties(self):
        url = f"/api/properties/{self.house.id}/"
        self.assertEqual(self.client.put(url, {"title": "Hijacked listing"}).status_code, 403)
        self.assertEqual(self.client.patch(url, {"status": "inactive"}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_user_cannot_modify_other_users(self):
        other = make_user()
        response = self.client.patch(f"/api/admin/users/{other.id}/", {"is_active": False})
        self.assertEqual(response.status_code, 403)
        other.refresh_from_db()
        self.assertTrue(other.is_active)

    def test_deactivated_admin_loses_admin_access(self):
        admin = make_user(admin=True)
        client = auth_client(admin)
        admin.is_active = False
        admin.save()
        self.assertEqual(client.get("/api/admin/analytics/").status_code, 401)


class UserIsolationTests(TestCase):
    def setUp(self):
        self.alice, self.bob = make_user(), make_user()
        self.house = make_house()
        Favorite.objects.create(user=self.alice, property=self.house)
        RecommendationHistory.objects.create(
            user=self.alice, request_preferences={"location": "Alice's office"}
        )

    def test_bob_sees_none_of_alices_data(self):
        bob = auth_client(self.bob)
        self.assertEqual(bob.get("/api/favorites/").data["count"], 0)
        self.assertEqual(bob.get("/api/favorites/ids/").data["ids"], [])
        self.assertEqual(bob.get("/api/recommendations/history/").data["count"], 0)
        self.assertEqual(bob.get("/api/users/me/").data["email"], self.bob.email)

    def test_bob_cannot_delete_alices_favorite_or_history(self):
        bob = auth_client(self.bob)
        self.assertEqual(bob.delete(f"/api/favorites/{self.house.id}/").status_code, 404)
        bob.delete("/api/recommendations/history/")
        self.assertTrue(Favorite.objects.filter(user=self.alice).exists())
        self.assertTrue(RecommendationHistory.objects.filter(user=self.alice).exists())


@override_settings(ROOT_URLCONF="rentals.tests.test_security")
class ErrorHandlingTests(TestCase):
    def test_unhandled_exception_returns_generic_500(self):
        client = APIClient(raise_request_exception=False)
        response = client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        body = response.content.decode()
        self.assertIn("INTERNAL_ERROR", body)
        for secret in ("hunter2", "/srv/secret", "Traceback", "RuntimeError"):
            self.assertNotIn(secret, body)


class MalformedInputTests(TestCase):
    def test_malformed_json(self):
        response = APIClient().post(
            "/api/recommendations/", data="{not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "MALFORMED_REQUEST")

    def test_non_json_content_type_is_rejected(self):
        response = APIClient().post(
            "/api/recommendations/", data="location=HSR", content_type="application/x-www-form-urlencoded"
        )
        self.assertEqual(response.status_code, 415)

    def test_wrong_types_are_rejected(self):
        for payload in ({"top_n": "lots"}, {"bedrooms": 2.5}, {"priority": "high"}, {"furnished": "kinda"}):
            with self.subTest(payload=payload):
                self.assertEqual(APIClient().post("/api/recommendations/", payload).status_code, 400)

    def test_unknown_route_returns_json_404(self):
        response = self.client.get("/api/does-not-exist/")
        self.assertEqual(response.status_code, 404)


class RequestIdTests(TestCase):
    def test_request_id_is_generated(self):
        response = self.client.get("/api/health/")
        self.assertRegex(response["X-Request-ID"], r"^[0-9a-f]{32}$")

    def test_safe_client_request_id_is_echoed(self):
        response = self.client.get("/api/health/", HTTP_X_REQUEST_ID="trace-abc-12345")
        self.assertEqual(response["X-Request-ID"], "trace-abc-12345")

    def test_unsafe_client_request_id_is_replaced(self):
        response = self.client.get("/api/health/", HTTP_X_REQUEST_ID="bad\r\nheader<script>")
        self.assertRegex(response["X-Request-ID"], r"^[0-9a-f]{32}$")


@override_settings(ALLOWED_HOSTS=["rentwise.example"])
class HostValidationTests(TestCase):
    def test_health_probe_works_for_internal_hosts(self):
        response = self.client.get("/api/health/", HTTP_HOST="10.0.0.7:10000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    def test_other_paths_reject_unknown_hosts_with_json(self):
        response = self.client.get("/api/properties/", HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "BAD_REQUEST")

    def test_allowed_host_is_served(self):
        response = self.client.get("/api/properties/", HTTP_HOST="rentwise.example")
        self.assertEqual(response.status_code, 200)


class SecurityHeaderTests(TestCase):
    def test_security_headers_present(self):
        response = self.client.get("/api/properties/")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Referrer-Policy"], "same-origin")

    def test_cors_only_allows_configured_origins(self):
        with self.settings(CORS_ALLOWED_ORIGINS=["https://app.rentwise.example"]):
            allowed = self.client.get("/api/health/", HTTP_ORIGIN="https://app.rentwise.example")
            denied = self.client.get("/api/health/", HTTP_ORIGIN="https://evil.example")
        self.assertEqual(allowed["Access-Control-Allow-Origin"], "https://app.rentwise.example")
        self.assertNotIn("Access-Control-Allow-Origin", denied)


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_login_is_rate_limited(self):
        rates = {**ScopedRateThrottle.THROTTLE_RATES, "auth": "3/minute"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            client = APIClient()
            statuses = [
                client.post("/api/auth/login/", {"email": "a@b.com", "password": "x"}).status_code
                for _ in range(4)
            ]
        self.assertEqual(statuses, [401, 401, 401, 429])

    def test_session_refresh_has_its_own_budget(self):
        rates = {**ScopedRateThrottle.THROTTLE_RATES, "auth": "1/minute", "refresh": "5/minute"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            client = APIClient()
            client.post("/api/auth/login/", {"email": "a@b.com", "password": "x"})
            statuses = [client.post("/api/auth/refresh/").status_code for _ in range(5)]
        self.assertEqual(statuses, [401] * 5)  # not throttled by the exhausted login budget

    def test_recommendations_are_rate_limited_with_retry_hint(self):
        rates = {**ScopedRateThrottle.THROTTLE_RATES, "recommendations": "2/minute"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            client = APIClient()
            for _ in range(2):
                self.assertEqual(client.post("/api/recommendations/", {}).status_code, 200)
            response = client.post("/api/recommendations/", {})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["error"]["code"], "RATE_LIMITED")
        self.assertIn("retry_after_seconds", response.data["error"]["details"])


class ProductionSettingsTests(TestCase):
    """The production settings module refuses insecure configuration."""

    def import_production(self, **env):
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "DATABASE_URL", "ALLOWED_HOSTS"))}
        clean_env.update(env)
        return subprocess.run(
            [sys.executable, "-c", "import config.settings.production as s; print(s.DEBUG, s.SECURE_SSL_REDIRECT, s.SESSION_COOKIE_SECURE, s.SECURE_HSTS_SECONDS)"],
            cwd=BASE_DIR,
            env=clean_env,
            capture_output=True,
            text=True,
        )

    def test_missing_secret_key_fails(self):
        result = self.import_production(ALLOWED_HOSTS="rentwise.example", DATABASE_URL="postgres://u:p@db/x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_sqlite_is_refused_in_production(self):
        result = self.import_production(DJANGO_SECRET_KEY="x" * 50, ALLOWED_HOSTS="rentwise.example")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PostgreSQL", result.stderr)

    def test_valid_production_configuration_is_hardened(self):
        result = self.import_production(
            DJANGO_SECRET_KEY="x" * 50,
            ALLOWED_HOSTS="rentwise.example",
            DATABASE_URL="postgres://u:p@db:5432/rentwise",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["False", "True", "True", "31536000"])

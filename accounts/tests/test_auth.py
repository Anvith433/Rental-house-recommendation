from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from rentals.tests.factories import DEFAULT_PASSWORD, auth_client, make_user

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/users/me/"
COOKIE = settings.REFRESH_COOKIE_NAME


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_with_hashed_password_and_signs_in(self):
        response = self.client.post(
            REGISTER_URL,
            {"email": "Priya@Example.com", "password": "Str0ng!pass9", "first_name": "Priya"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "priya@example.com")
        self.assertEqual(response.data["user"]["role"], "USER")

        user = get_user_model().objects.get(email="priya@example.com")
        self.assertNotEqual(user.password, "Str0ng!pass9")
        self.assertTrue(user.check_password("Str0ng!pass9"))

        cookie = response.cookies[COOKIE]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["path"], settings.REFRESH_COOKIE_PATH)
        self.assertEqual(cookie["samesite"], "Lax")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        make_user(email="taken@example.com")
        response = self.client.post(
            REGISTER_URL,
            {"email": "TAKEN@example.com", "password": "Str0ng!pass9", "first_name": "A"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["error"]["details"])

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            REGISTER_URL, {"email": "weak@example.com", "password": "12345678", "first_name": "A"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "INVALID_REQUEST")

    def test_role_cannot_be_self_assigned(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "sneaky@example.com",
                "password": "Str0ng!pass9",
                "first_name": "S",
                "role": "ADMIN",
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="sneaky@example.com")
        self.assertEqual(user.role, "USER")
        self.assertFalse(user.is_superuser)

    def test_missing_fields_are_reported(self):
        response = self.client.post(REGISTER_URL, {})
        self.assertEqual(response.status_code, 400)
        details = response.data["error"]["details"]
        for field in ("email", "password", "first_name"):
            self.assertIn(field, details)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="login@example.com")

    def test_login_returns_access_token_and_refresh_cookie(self):
        response = self.client.post(
            LOGIN_URL, {"email": "LOGIN@example.com", "password": DEFAULT_PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        token = AccessToken(response.data["access"])
        self.assertEqual(int(token["user_id"]), self.user.id)
        self.assertIn(COOKIE, response.cookies)

    def test_wrong_password_and_unknown_email_share_a_generic_error(self):
        wrong = self.client.post(LOGIN_URL, {"email": "login@example.com", "password": "nope"})
        unknown = self.client.post(LOGIN_URL, {"email": "ghost@example.com", "password": "nope"})
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.data["error"]["message"], unknown.data["error"]["message"])

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            LOGIN_URL, {"email": "login@example.com", "password": DEFAULT_PASSWORD}
        )
        self.assertEqual(response.status_code, 401)

    def test_password_is_never_echoed(self):
        response = self.client.post(
            LOGIN_URL, {"email": "login@example.com", "password": DEFAULT_PASSWORD}
        )
        self.assertNotIn(DEFAULT_PASSWORD, response.content.decode())


class TokenLifecycleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="tokens@example.com")
        self.client.post(LOGIN_URL, {"email": "tokens@example.com", "password": DEFAULT_PASSWORD})

    def test_refresh_with_cookie_rotates_and_blacklists_old_token(self):
        old_refresh = self.client.cookies[COOKIE].value
        response = self.client.post(REFRESH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        new_refresh = response.cookies[COOKIE].value
        self.assertNotEqual(old_refresh, new_refresh)

        replay = APIClient().post(REFRESH_URL, {"refresh": old_refresh})
        self.assertEqual(replay.status_code, 401)

    def test_refresh_without_token_is_401(self):
        response = APIClient().post(REFRESH_URL)
        self.assertEqual(response.status_code, 401)

    def test_refresh_with_garbage_token_is_401_and_clears_cookie(self):
        client = APIClient()
        client.cookies[COOKIE] = "not-a-token"
        response = client.post(REFRESH_URL)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.cookies[COOKIE].value, "")

    def test_logout_revokes_refresh_token(self):
        refresh = self.client.cookies[COOKIE].value
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies[COOKIE].value, "")
        self.assertEqual(APIClient().post(REFRESH_URL, {"refresh": refresh}).status_code, 401)

    def test_refresh_fails_for_deactivated_user(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.post(REFRESH_URL).status_code, 401)


class AccessTokenValidationTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_invalid_token_is_rejected(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer abc.def.ghi")
        response = client.get(ME_URL)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "AUTHENTICATION_FAILED")

    def test_expired_token_is_rejected(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=1))
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(client.get(ME_URL).status_code, 401)

    def test_refresh_token_cannot_be_used_as_access_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user)}")
        self.assertEqual(client.get(ME_URL).status_code, 401)

    def test_token_signed_with_other_key_is_rejected(self):
        import jwt

        forged = jwt.encode(
            {"token_type": "access", "user_id": str(self.user.id), "exp": 9999999999, "jti": "x"},
            "attacker-controlled-key-that-is-long-enough-123",
            algorithm="HS256",
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {forged}")
        self.assertEqual(client.get(ME_URL).status_code, 401)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user(email="me@example.com", first_name="Old")
        self.client = auth_client(self.user)

    def test_me_requires_authentication(self):
        self.assertEqual(APIClient().get(ME_URL).status_code, 401)

    def test_get_profile(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "me@example.com")
        self.assertNotIn("password", response.data)

    def test_update_profile_ignores_protected_fields(self):
        response = self.client.patch(
            ME_URL,
            {"first_name": "New", "phone": "+91 98765 43210", "role": "ADMIN", "email": "x@y.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.role, "USER")
        self.assertEqual(self.user.email, "me@example.com")

    def test_invalid_phone_is_rejected(self):
        response = self.client.patch(ME_URL, {"phone": "call me maybe"})
        self.assertEqual(response.status_code, 400)

    def test_password_change_revokes_other_sessions(self):
        other_session = RefreshToken.for_user(self.user)
        response = self.client.post(
            "/api/users/me/password/",
            {"current_password": DEFAULT_PASSWORD, "new_password": "An0ther-Strong-Pass"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("An0ther-Strong-Pass"))
        replay = APIClient().post(REFRESH_URL, {"refresh": str(other_session)})
        self.assertEqual(replay.status_code, 401)

    def test_password_change_requires_current_password(self):
        response = self.client.post(
            "/api/users/me/password/",
            {"current_password": "wrong", "new_password": "An0ther-Strong-Pass"},
        )
        self.assertEqual(response.status_code, 400)

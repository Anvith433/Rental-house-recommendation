"""Issuing and revoking JWTs, and the HttpOnly refresh-token cookie."""

from django.conf import settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def get_refresh_token(request) -> str | None:
    """Browser clients send the cookie; API clients may send it in the body."""
    token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if not token and isinstance(request.data, dict):
        token = request.data.get("refresh")
    return token if isinstance(token, str) and token else None


def revoke_all_tokens(user) -> None:
    """Blacklist every outstanding refresh token, e.g. after a password change."""
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)

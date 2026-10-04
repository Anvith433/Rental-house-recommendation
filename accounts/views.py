from django.contrib.auth import authenticate
from django.db.models import Count
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import filters, generics, mixins, serializers, status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import error_payload
from core.permissions import IsAdminRole
from core.throttles import SCOPED_THROTTLES

from .models import User
from .serializers import (
    AdminUserSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    TokenResponseSerializer,
    UserSerializer,
)
from .tokens import (
    clear_refresh_cookie,
    get_refresh_token,
    issue_tokens,
    revoke_all_tokens,
    set_refresh_cookie,
)

AccessTokenSerializer = inline_serializer("AccessToken", {"access": serializers.CharField()})


class PublicAuthEndpoint(APIView):
    """Base for credential endpoints: no request authentication, but failed
    credentials still produce 401 (DRF would otherwise downgrade to 403 when
    a view has no authenticators to supply a WWW-Authenticate header)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'


def _token_response(user, status_code=status.HTTP_200_OK) -> Response:
    access, refresh = issue_tokens(user)
    response = Response({"access": access, "user": UserSerializer(user).data}, status=status_code)
    set_refresh_cookie(response, refresh)
    return response


class RegisterView(PublicAuthEndpoint):
    """Create an account and sign the new user in."""

    throttle_classes = SCOPED_THROTTLES
    throttle_scope = "register"

    @extend_schema(request=RegisterSerializer, responses={201: TokenResponseSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _token_response(user, status.HTTP_201_CREATED)


class LoginView(PublicAuthEndpoint):
    """Exchange email + password for an access token (body) and a refresh
    token (HttpOnly cookie)."""

    throttle_classes = SCOPED_THROTTLES
    throttle_scope = "auth"

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer, 401: OpenApiResponse(description="Invalid credentials")},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=serializer.validated_data["email"].lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            # Same message for unknown email, wrong password and inactive
            # accounts so the endpoint cannot be used to enumerate users.
            raise AuthenticationFailed("Invalid email or password.")
        return _token_response(user)


class RefreshView(PublicAuthEndpoint):
    """Rotate the refresh token and return a new access token. The previous
    refresh token is blacklisted."""

    throttle_classes = SCOPED_THROTTLES
    throttle_scope = "refresh"

    @extend_schema(
        request=inline_serializer(
            "RefreshRequest", {"refresh": serializers.CharField(required=False)}
        ),
        responses={200: AccessTokenSerializer},
        description="Reads the refresh token from the HttpOnly cookie (or `refresh` in the body).",
    )
    def post(self, request):
        token = get_refresh_token(request)
        if token is None:
            raise AuthenticationFailed("No refresh token provided.")
        serializer = TokenRefreshSerializer(data={"refresh": token})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, serializers.ValidationError, AuthenticationFailed):
            response = Response(
                error_payload("AUTHENTICATION_FAILED", "Session expired. Please sign in again."),
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response
        response = Response({"access": serializer.validated_data["access"]})
        new_refresh = serializer.validated_data.get("refresh")
        if new_refresh:
            set_refresh_cookie(response, new_refresh)
        return response


class LogoutView(PublicAuthEndpoint):
    """Blacklist the refresh token and clear the cookie. Access tokens expire
    on their own within ``JWT_ACCESS_TOKEN_MINUTES``."""


    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        token = get_refresh_token(request)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass  # Already invalid; logging out is still successful.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    """The authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "options"]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = SCOPED_THROTTLES
    throttle_scope = "auth"

    @extend_schema(request=PasswordChangeSerializer, responses={200: TokenResponseSerializer})
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        # Sign out every other session, then issue a fresh session for this one.
        revoke_all_tokens(user)
        return _token_response(user)


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Administrator user management: list, inspect, change role, (de)activate."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email", "last_login"]
    ordering = ["-created_at"]
    http_method_names = ["get", "patch", "options"]

    def get_queryset(self):
        queryset = User.objects.annotate(
            favorites_count=Count("favorites", distinct=True),
            recommendations_count=Count("recommendation_history", distinct=True),
        )
        role = self.request.query_params.get("role")
        if role in User.Role.values:
            queryset = queryset.filter(role=role)
        is_active = self.request.query_params.get("is_active")
        if is_active in ("true", "false"):
            queryset = queryset.filter(is_active=is_active == "true")
        return queryset

    def perform_update(self, serializer):
        user = serializer.save()
        # Keep Django-admin access aligned with the platform role.
        user.is_staff = user.role == User.Role.ADMIN or user.is_superuser
        user.save(update_fields=["is_staff"])
        if not user.is_active:
            revoke_all_tokens(user)

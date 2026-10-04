from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """The authenticated user's own profile. Role and status are read-only."""

    full_name = serializers.CharField(read_only=True)
    is_admin = serializers.BooleanField(source="is_platform_admin", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "is_admin",
            "created_at",
        ]
        read_only_fields = ["id", "email", "role", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        candidate = User(
            email=attrs["email"],
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        password_validation.validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, user=self.context["request"].user)
        return value


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    user = UserSerializer()


class AdminUserSerializer(serializers.ModelSerializer):
    """User representation for administrators, with usage counters."""

    full_name = serializers.CharField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    recommendations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "is_active",
            "last_login",
            "created_at",
            "favorites_count",
            "recommendations_count",
        ]
        read_only_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "last_login",
            "created_at",
        ]

    def validate(self, attrs):
        request_user = self.context["request"].user
        if self.instance is not None and self.instance.pk == request_user.pk:
            if attrs.get("is_active") is False:
                raise serializers.ValidationError(
                    {"is_active": "You cannot deactivate your own account."}
                )
            if attrs.get("role") == User.Role.USER:
                raise serializers.ValidationError({"role": "You cannot remove your own admin role."})
        return attrs

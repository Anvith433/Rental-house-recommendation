from rest_framework import serializers

from accounts.models import phone_validator

from ..choices import BedroomMode
from ..models import MAX_RENT, MAX_ROOMS, Favorite, Inquiry, RecommendationHistory, UserPreference
from .properties import PropertyListSerializer
from .recommendations import RecommendationPrioritySerializer, validate_rent_range


class FavoriteSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "property", "created_at"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    min_rent = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=MAX_RENT
    )
    max_rent = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=MAX_RENT
    )
    bedrooms = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=MAX_ROOMS
    )
    bedroom_mode = serializers.ChoiceField(choices=BedroomMode.choices, required=False)
    priority = RecommendationPrioritySerializer(required=False)

    class Meta:
        model = UserPreference
        fields = [
            "location",
            "min_rent",
            "max_rent",
            "bedrooms",
            "bedroom_mode",
            "furnished",
            "parking",
            "required_parking",
            "priority",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate(self, attrs):
        merged = {
            "min_rent": attrs.get("min_rent", getattr(self.instance, "min_rent", None)),
            "max_rent": attrs.get("max_rent", getattr(self.instance, "max_rent", None)),
        }
        validate_rent_range(merged)
        if "priority" in attrs:
            attrs["priority"] = dict(attrs["priority"])
        return attrs


class RecommendationHistorySerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = RecommendationHistory
        fields = [
            "id",
            "request_preferences",
            "result_property_ids",
            "results",
            "top_score",
            "total_matches",
            "budget_relaxed",
            "latency_ms",
            "created_at",
        ]

    def get_results(self, obj) -> list[dict]:
        """Lightweight summaries of the recommended properties, resolved from a
        single bulk lookup prepared by the view (``properties_by_id``)."""
        properties_by_id = self.context.get("properties_by_id", {})
        results = []
        for property_id in obj.result_property_ids:
            house = properties_by_id.get(property_id)
            if house is not None:
                results.append(
                    {
                        "id": house.id,
                        "title": house.title,
                        "location": house.location,
                        "rent": house.rent,
                        "bedrooms": house.bedrooms,
                        "status": house.status,
                    }
                )
        return results


class InquiryCreateSerializer(serializers.ModelSerializer):
    message = serializers.CharField(min_length=10, max_length=2000)
    phone = serializers.CharField(
        required=False, allow_blank=True, max_length=20, validators=[phone_validator]
    )

    class Meta:
        model = Inquiry
        fields = ["id", "message", "phone", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]


class InquirySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "property",
            "property_title",
            "user_email",
            "user_name",
            "message",
            "phone",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "property",
            "property_title",
            "user_email",
            "user_name",
            "message",
            "phone",
            "created_at",
        ]

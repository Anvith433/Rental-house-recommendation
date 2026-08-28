from rest_framework import serializers
from .models import House


class HouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = House
        fields = "__all__"


class RecommendationPrioritySerializer(serializers.Serializer):

    # -------------------------
    # Allowed Priority Levels
    # -------------------------
    location = serializers.ChoiceField(
        choices=[
            "must_have",
            "important",
            "preferred",
            "optional"
        ],
        required=False
    )

    budget = serializers.ChoiceField(
        choices=[
            "must_have",
            "important",
            "preferred",
            "optional"
        ],
        required=False
    )

    bedrooms = serializers.ChoiceField(
        choices=[
            "must_have",
            "important",
            "preferred",
            "optional"
        ],
        required=False
    )

    furnished = serializers.ChoiceField(
        choices=[
            "must_have",
            "important",
            "preferred",
            "optional"
        ],
        required=False
    )

    parking = serializers.ChoiceField(
        choices=[
            "must_have",
            "important",
            "preferred",
            "optional"
        ],
        required=False
    )


class RecommendationRequestSerializer(serializers.Serializer):

    # -------------------------
    # Location
    # -------------------------
    location = serializers.CharField(
        required=False,
        allow_blank=False
    )

    # -------------------------
    # Maximum Rent
    # -------------------------
    max_rent = serializers.FloatField(
        required=False,
        min_value=0
    )

    # -------------------------
    # Minimum Rent
    # -------------------------
    min_rent = serializers.FloatField(
        required=False,
        min_value=0
    )

    # -------------------------
    # Bedrooms
    # -------------------------
    bedrooms = serializers.IntegerField(
        required=False,
        min_value=1
    )

    # -------------------------
    # Bedroom Mode
    # -------------------------
    bedroom_mode = serializers.ChoiceField(
        choices=[
            "exact",
            "minimum"
        ],
        required=False,
        default="exact"
    )

    # -------------------------
    # Furnished
    # -------------------------
    furnished = serializers.BooleanField(
        required=False
    )

    # -------------------------
    # Parking
    # -------------------------
    parking = serializers.BooleanField(
        required=False
    )

    # -------------------------
    # Required Parking
    # -------------------------
    required_parking = serializers.BooleanField(
        required=False
    )

    # -------------------------
    # Preference Priority
    # -------------------------
    priority = RecommendationPrioritySerializer(
        required=False
    )

    # -------------------------
    # Number of Recommendations
    # -------------------------
    top_n = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=5
    )

    # -------------------------
    # Validate Rent Range
    # -------------------------
    def validate(self, data):

        min_rent = data.get("min_rent")
        max_rent = data.get("max_rent")

        if (
            min_rent is not None
            and max_rent is not None
            and min_rent > max_rent
        ):
            raise serializers.ValidationError(
                {
                    "rent": (
                        "min_rent cannot be greater "
                        "than max_rent."
                    )
                }
            )

        return data
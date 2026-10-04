from rest_framework import serializers

from ..choices import BedroomMode, Priority
from ..recommendation_config import DEFAULT_TOP_N, MAX_TOP_N

# Search bounds are looser than listing bounds: an oversized budget or bedroom
# count is a legitimate query (it simply matches nothing), but values large
# enough to overflow database integer comparisons are rejected.
MAX_SEARCH_RENT = 1_000_000_000
MAX_SEARCH_BEDROOMS = 100


def _priority_field():
    return serializers.ChoiceField(choices=Priority.values, required=False)


class RecommendationPrioritySerializer(serializers.Serializer):
    """How much each criterion matters: must_have / important / preferred / optional."""

    location = _priority_field()
    budget = _priority_field()
    bedrooms = _priority_field()
    furnished = _priority_field()
    parking = _priority_field()


def validate_rent_range(data: dict) -> None:
    min_rent = data.get("min_rent")
    max_rent = data.get("max_rent")
    if min_rent is not None and max_rent is not None and min_rent > max_rent:
        raise serializers.ValidationError({"rent": "min_rent cannot be greater than max_rent."})


class RecommendationPreferencesSerializer(serializers.Serializer):
    """The preference fields shared by recommendation requests and saved
    preferences. Validation here is authoritative – never the frontend's."""

    location = serializers.CharField(required=False, allow_blank=False, max_length=100)
    max_rent = serializers.FloatField(required=False, min_value=0, max_value=MAX_SEARCH_RENT)
    min_rent = serializers.FloatField(required=False, min_value=0, max_value=MAX_SEARCH_RENT)
    bedrooms = serializers.IntegerField(required=False, min_value=1, max_value=MAX_SEARCH_BEDROOMS)
    bedroom_mode = serializers.ChoiceField(
        choices=BedroomMode.values, required=False, default=BedroomMode.EXACT
    )
    furnished = serializers.BooleanField(required=False)
    parking = serializers.BooleanField(required=False)
    required_parking = serializers.BooleanField(required=False)
    priority = RecommendationPrioritySerializer(required=False)

    def validate(self, data):
        validate_rent_range(data)
        return data


class RecommendationRequestSerializer(RecommendationPreferencesSerializer):
    top_n = serializers.IntegerField(
        required=False, min_value=1, max_value=MAX_TOP_N, default=DEFAULT_TOP_N
    )
    allow_budget_relaxation = serializers.BooleanField(
        required=False,
        default=True,
        help_text=(
            "When no property fits max_rent, retry with progressively higher budgets "
            "(+10%, +20%, +30%). Never applied when budget priority is must_have."
        ),
    )

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttles import SCOPED_THROTTLES

from ..models import House, RecommendationHistory
from ..serializers import (
    PropertyListSerializer,
    RecommendationHistorySerializer,
    RecommendationRequestSerializer,
)
from ..services.recommendation_service import RecommendationService

RecommendationItemSchema = inline_serializer(
    "RecommendationItem",
    {
        "rank": serializers.IntegerField(),
        "property": PropertyListSerializer(),
        "house": PropertyListSerializer(help_text="Deprecated alias of `property`."),
        "score": serializers.FloatField(),
        "matched_preferences": serializers.ListField(child=serializers.CharField()),
        "unmatched_preferences": serializers.ListField(child=serializers.CharField()),
        "score_breakdown": serializers.DictField(child=serializers.FloatField()),
        "explanation": inline_serializer(
            "RecommendationExplanation",
            {
                "summary": serializers.CharField(),
                "strengths": serializers.ListField(child=serializers.CharField()),
                "weaknesses": serializers.ListField(child=serializers.CharField()),
            },
        ),
    },
)

RecommendationResponseSchema = inline_serializer(
    "RecommendationResponse",
    {
        "recommendations": RecommendationItemSchema.__class__(many=True),
        "total_matches": serializers.IntegerField(),
        "requested_top_n": serializers.IntegerField(),
        "returned_count": serializers.IntegerField(),
        "filters_applied": serializers.DictField(),
        "budget_relaxed": serializers.BooleanField(),
        "message": serializers.CharField(required=False),
        "original_max_rent": serializers.FloatField(required=False),
        "relaxed_max_rent": serializers.FloatField(required=False),
        "relaxation_percentage": serializers.IntegerField(required=False),
    },
)


class RecommendationView(APIView):
    """Personalised, explainable Top-N recommendations.

    Open to anonymous visitors (rate limited); requests by signed-in users are
    saved to their recommendation history.
    """

    permission_classes = [AllowAny]
    throttle_classes = SCOPED_THROTTLES
    throttle_scope = "recommendations"

    @extend_schema(
        request=RecommendationRequestSerializer, responses={200: RecommendationResponseSchema}
    )
    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = RecommendationService().recommend(
            serializer.validated_data, user=request.user
        )
        return Response(result.to_response(), status=status.HTTP_200_OK)


class RecommendationHistoryView(generics.ListAPIView):
    """The signed-in user's past recommendation requests (newest first)."""

    serializer_class = RecommendationHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends: list = []

    def get_queryset(self):
        return RecommendationHistory.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        property_ids = {pk for entry in page for pk in entry.result_property_ids}
        properties_by_id = House.objects.only(
            "id", "title", "location", "rent", "bedrooms", "status"
        ).in_bulk(property_ids)
        serializer = self.get_serializer(
            page, many=True, context={**self.get_serializer_context(), "properties_by_id": properties_by_id}
        )
        return self.get_paginated_response(serializer.data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        """Clear the signed-in user's recommendation history."""
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

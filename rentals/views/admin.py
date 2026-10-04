from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminRole

from ..choices import InteractionType
from ..filters import PropertyFilter
from ..models import House, Inquiry
from ..serializers import InquirySerializer, PropertyListSerializer
from ..services.analytics import platform_analytics


class AdminAnalyticsView(APIView):
    """Platform statistics: users, listings, favorites, recommendation usage
    and recommendation-engine metrics."""

    permission_classes = [IsAdminRole]

    @extend_schema(responses=serializers.DictField())
    def get(self, request):
        return Response(platform_analytics())


class AdminPropertySerializer(PropertyListSerializer):
    favorites_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    inquiries_count = serializers.IntegerField(read_only=True)

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + [
            "updated_at",
            "favorites_count",
            "views_count",
            "inquiries_count",
        ]


class AdminPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Every listing regardless of status, with engagement counters. Edits go
    through ``/api/properties/{id}/``."""

    serializer_class = AdminPropertySerializer
    permission_classes = [IsAdminRole]
    filterset_class = PropertyFilter
    search_fields = ["title", "location", "city"]
    ordering_fields = ["rent", "created_at", "updated_at", "favorites_count", "views_count"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        return House.objects.with_primary_image().annotate(
            favorites_count=Count("favorited_by", distinct=True),
            views_count=Count(
                "interactions",
                filter=Q(interactions__interaction_type=InteractionType.VIEW),
                distinct=True,
            ),
            inquiries_count=Count("inquiries", distinct=True),
        )


class AdminInquiryViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """Contact requests from users; admins can update their status."""

    serializer_class = InquirySerializer
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "property"]
    ordering = ["-created_at"]
    http_method_names = ["get", "patch", "options"]

    def get_queryset(self):
        return Inquiry.objects.select_related("user", "property")

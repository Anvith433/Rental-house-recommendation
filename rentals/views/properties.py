from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdminOrReadOnly, is_admin_user
from core.throttles import SCOPED_THROTTLES

from ..choices import InteractionType, ListingStatus
from ..filters import PropertyFilter
from ..models import House, Inquiry, PropertyInteraction, UserPreference
from ..serializers import InquiryCreateSerializer, PropertyListSerializer, PropertySerializer
from ..services.recommendation_service import RecommendationService

MIN_COMPARE = 2
MAX_COMPARE = 4


def saved_preferences_for(user) -> dict | None:
    if not user.is_authenticated:
        return None
    preference = UserPreference.objects.filter(user=user).first()
    return preference.as_preferences() if preference else None


class PropertyViewSet(viewsets.ModelViewSet):
    """Browse and search properties (public); create/update/delete (admins).

    Non-admins only ever see active listings. Signed-in users with saved
    preferences receive a ``match`` block (score + explanation) on details
    and comparisons.
    """

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = PropertyFilter
    search_fields = ["title", "location", "city", "description"]
    ordering_fields = ["rent", "created_at", "area_sqft", "bedrooms", "available_from"]
    ordering = ["-created_at", "-id"]

    def get_serializer_class(self):
        if self.action == "list":
            return PropertyListSerializer
        return PropertySerializer

    def get_queryset(self):
        if self.action == "list":
            queryset = House.objects.with_primary_image()
        else:
            queryset = House.objects.prefetch_related("images")
        if not is_admin_user(self.request.user):
            return queryset.filter(status=ListingStatus.ACTIVE)
        if self.action == "list" and "status" not in self.request.query_params:
            return queryset.filter(status=ListingStatus.ACTIVE)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        house = self.get_object()
        data = dict(self.get_serializer(house).data)
        if request.user.is_authenticated:
            PropertyInteraction.objects.create(
                user=request.user, property=house, interaction_type=InteractionType.VIEW
            )
            preferences = saved_preferences_for(request.user)
            if preferences:
                data["match"] = RecommendationService().evaluate(house, preferences)
        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "ids", OpenApiTypes.STR, required=True, description="2–4 comma-separated IDs"
            )
        ],
        responses=inline_serializer(
            "PropertyComparison",
            {
                "properties": PropertySerializer(many=True),
                "matches": serializers.DictField(),
                "has_saved_preferences": serializers.BooleanField(),
            },
        ),
    )
    @action(detail=False, methods=["get"])
    def compare(self, request):
        """Side-by-side comparison of 2–4 properties, in the requested order."""
        raw_ids = request.query_params.get("ids", "")
        try:
            ids = list(dict.fromkeys(int(value) for value in raw_ids.split(",") if value.strip()))
        except ValueError:
            raise ValidationError({"ids": "ids must be a comma-separated list of integers."})
        if not MIN_COMPARE <= len(ids) <= MAX_COMPARE:
            raise ValidationError(
                {"ids": f"Provide between {MIN_COMPARE} and {MAX_COMPARE} property IDs."}
            )

        houses_by_id = self.get_queryset().in_bulk(ids)
        houses = [houses_by_id[pk] for pk in ids if pk in houses_by_id]
        preferences = saved_preferences_for(request.user)
        service = RecommendationService()
        matches = (
            {str(house.id): service.evaluate(house, preferences) for house in houses}
            if preferences
            else {}
        )
        return Response(
            {
                "properties": PropertySerializer(houses, many=True).data,
                "matches": matches,
                "has_saved_preferences": bool(preferences),
            }
        )

    @extend_schema(
        responses=inline_serializer(
            "LocationCount",
            {"location": serializers.CharField(), "count": serializers.IntegerField()},
            many=True,
        )
    )
    @action(detail=False, methods=["get"], pagination_class=None, filter_backends=[])
    def locations(self, request):
        """Localities with active listings, for search suggestions."""
        rows = (
            House.objects.filter(status=ListingStatus.ACTIVE)
            .values("location")
            .annotate(count=Count("id"))
            .order_by("location")
        )
        return Response(list(rows))

    @extend_schema(request=InquiryCreateSerializer, responses={201: InquiryCreateSerializer})
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        throttle_classes=SCOPED_THROTTLES,
        url_path="inquiries",
    )
    def inquire(self, request, pk=None):
        """Request more information about a listing."""
        house = self.get_object()
        serializer = InquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = Inquiry.objects.create(
            user=request.user, property=house, **serializer.validated_data
        )
        PropertyInteraction.objects.create(
            user=request.user, property=house, interaction_type=InteractionType.CONTACT
        )
        return Response(InquiryCreateSerializer(inquiry).data, status=status.HTTP_201_CREATED)

    def get_throttles(self):
        if self.action == "inquire":
            self.throttle_scope = "contact"
        return super().get_throttles()

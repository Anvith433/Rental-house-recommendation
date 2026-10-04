from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..choices import InteractionType, ListingStatus
from ..models import Favorite, House, PropertyInteraction
from ..serializers import FavoriteSerializer


class FavoriteListView(generics.ListAPIView):
    """The signed-in user's saved properties. Users only ever see their own."""

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends: list = []

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user).prefetch_related(Prefetch("property", queryset=House.objects.with_primary_image()))
        )


class FavoriteIdsView(APIView):
    """IDs of every property the user has saved – lets the UI render heart
    state on any card without a per-card request."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            "FavoriteIds", {"ids": serializers.ListField(child=serializers.IntegerField())}
        )
    )
    def get(self, request):
        ids = Favorite.objects.filter(user=request.user).values_list("property_id", flat=True)
        return Response({"ids": list(ids)})


class FavoriteDetailView(APIView):
    """Save (POST, idempotent) or remove (DELETE) a property from favorites."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={201: FavoriteSerializer, 200: FavoriteSerializer})
    def post(self, request, property_id: int):
        house = get_object_or_404(House, pk=property_id, status=ListingStatus.ACTIVE)
        try:
            with transaction.atomic():
                favorite, created = Favorite.objects.get_or_create(user=request.user, property=house)
        except IntegrityError:
            favorite, created = Favorite.objects.get(user=request.user, property=house), False
        if created:
            PropertyInteraction.objects.create(
                user=request.user, property=house, interaction_type=InteractionType.FAVORITE
            )
        return Response(
            FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(responses={204: None})
    def delete(self, request, property_id: int):
        deleted, _ = Favorite.objects.filter(user=request.user, property_id=property_id).delete()
        if not deleted:
            return Response(
                {"error": {"code": "NOT_FOUND", "message": "Property is not in your favorites.", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        PropertyInteraction.objects.create(
            user=request.user, property_id=property_id, interaction_type=InteractionType.UNFAVORITE
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

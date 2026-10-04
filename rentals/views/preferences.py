from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import UserPreference
from ..serializers import UserPreferenceSerializer


class PreferenceView(APIView):
    """The signed-in user's saved recommendation preferences.

    GET returns defaults (``updated_at: null``) until preferences are saved.
    PUT replaces them; PATCH updates individual fields.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserPreferenceSerializer)
    def get(self, request):
        preference = UserPreference.objects.filter(user=request.user).first()
        return Response(UserPreferenceSerializer(preference or UserPreference()).data)

    @extend_schema(request=UserPreferenceSerializer, responses=UserPreferenceSerializer)
    def put(self, request):
        return self._save(request, partial=False)

    @extend_schema(request=UserPreferenceSerializer, responses=UserPreferenceSerializer)
    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial: bool):
        preference = UserPreference.objects.filter(user=request.user).first()
        if not partial:
            # PUT semantics: unspecified fields reset to their defaults.
            preference_defaults = UserPreference(user=request.user)
            if preference is not None:
                preference_defaults.pk = preference.pk
                preference_defaults.created_at = preference.created_at
            preference = preference_defaults
        serializer = UserPreferenceSerializer(preference, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        created = preference is None or preference.pk is None
        serializer.save(user=request.user)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

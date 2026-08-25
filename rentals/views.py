from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import House
from .serializers import HouseSerializer
from .recommendations import calculate_house_score


class HouseViewSet(viewsets.ModelViewSet):

    queryset = House.objects.all()

    serializer_class = HouseSerializer

    def get_queryset(self):

        queryset = House.objects.all()

        location = self.request.query_params.get("location")
        max_rent = self.request.query_params.get("max_rent")
        min_rent = self.request.query_params.get("min_rent")
        bedrooms = self.request.query_params.get("bedrooms")
        furnished = self.request.query_params.get("furnished")
        parking = self.request.query_params.get("parking")

        if location:
            queryset = queryset.filter(
                location__icontains=location
            )

        if max_rent:
            queryset = queryset.filter(
                rent__lte=max_rent
            )

        if min_rent:
            queryset = queryset.filter(
                rent__gte=min_rent
            )

        if bedrooms:
            queryset = queryset.filter(
                bedrooms=bedrooms
            )

        if furnished is not None:
            queryset = queryset.filter(
                furnished=furnished.lower() == "true"
            )

        if parking is not None:
            queryset = queryset.filter(
                parking=parking.lower() == "true"
            )

        return queryset


class RecommendationView(APIView):

    def post(self, request):

        preferences = request.data

        houses = House.objects.all()

        recommendations = []

        for house in houses:

            score = calculate_house_score(
                house,
                preferences
            )

            recommendations.append({
                "house": HouseSerializer(house).data,
                "score": score
            })

        recommendations.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return Response(
            recommendations,
            status=status.HTTP_200_OK
        )
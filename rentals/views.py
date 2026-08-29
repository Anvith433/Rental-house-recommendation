from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import House
from .serializers import (
    HouseSerializer,
    RecommendationRequestSerializer
)
from .recommendations import calculate_house_score
from .explanation import generate_house_explanation


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

        # -------------------------
        # FILTER: Location
        # -------------------------
        if location:
            queryset = queryset.filter(
                location__icontains=location
            )

        # -------------------------
        # FILTER: Maximum Rent
        # -------------------------
        if max_rent:
            queryset = queryset.filter(
                rent__lte=max_rent
            )

        # -------------------------
        # FILTER: Minimum Rent
        # -------------------------
        if min_rent:
            queryset = queryset.filter(
                rent__gte=min_rent
            )

        # -------------------------
        # FILTER: Bedrooms
        # -------------------------
        if bedrooms:
            queryset = queryset.filter(
                bedrooms=bedrooms
            )

        # -------------------------
        # FILTER: Furnished
        # -------------------------
        if furnished is not None:
            queryset = queryset.filter(
                furnished=furnished.lower() == "true"
            )

        # -------------------------
        # FILTER: Parking
        # -------------------------
        if parking is not None:
            queryset = queryset.filter(
                parking=parking.lower() == "true"
            )

        return queryset


class RecommendationView(APIView):

    def get_filtered_houses(self, preferences):

        houses = House.objects.all()

        max_rent = preferences.get("max_rent")
        min_rent = preferences.get("min_rent")
        bedrooms = preferences.get("bedrooms")
        location = preferences.get("location")
        required_parking = preferences.get(
            "required_parking"
        )

        # -------------------------
        # HARD FILTER: Maximum Rent
        # -------------------------
        if max_rent is not None:
            houses = houses.filter(
                rent__lte=max_rent
            )

        # -------------------------
        # HARD FILTER: Minimum Rent
        # -------------------------
        if min_rent is not None:
            houses = houses.filter(
                rent__gte=min_rent
            )

        # -------------------------
        # HARD FILTER: Bedrooms
        # -------------------------
        bedroom_mode = preferences.get(
            "bedroom_mode",
            "exact"
        )

        if bedrooms is not None:

            if bedroom_mode == "minimum":

                houses = houses.filter(
                    bedrooms__gte=bedrooms
                )

            else:

                houses = houses.filter(
                    bedrooms=bedrooms
                )

        # -------------------------
        # HARD FILTER: Location
        # -------------------------
        if location:
            houses = houses.filter(
                location__icontains=location
            )

        # -------------------------
        # HARD FILTER: Required Parking
        # -------------------------
        if required_parking:
            houses = houses.filter(
                parking=True
            )

        return houses

    def post(self, request):

        # -------------------------
        # VALIDATE REQUEST
        # -------------------------
        serializer = (
            RecommendationRequestSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        preferences = (
            serializer.validated_data.copy()
        )

        # -------------------------
        # STORE ORIGINAL REQUEST
        # -------------------------
        original_preferences = (
            preferences.copy()
        )

        # -------------------------
        # STRICT SEARCH
        # -------------------------
        houses = self.get_filtered_houses(
            preferences
        )

        # -------------------------
        # BUDGET FALLBACK TRACKING
        # -------------------------
        relaxed_budget = False

        original_max_rent = (
            preferences.get("max_rent")
        )

        relaxed_max_rent = None

        # -------------------------
        # FALLBACK: RELAX BUDGET
        # -------------------------
        if (
            not houses.exists()
            and original_max_rent is not None
        ):

            original_max_rent = float(
                original_max_rent
            )

            relaxation_percentages = [
                10,
                20,
                30
            ]

            for percentage in (
                relaxation_percentages
            ):

                relaxed_max_rent = (
                    original_max_rent
                    * (1 + percentage / 100)
                )

                relaxed_preferences = (
                    preferences.copy()
                )

                relaxed_preferences[
                    "max_rent"
                ] = relaxed_max_rent

                relaxed_houses = (
                    self.get_filtered_houses(
                        relaxed_preferences
                    )
                )

                if relaxed_houses.exists():

                    houses = relaxed_houses

                    preferences = (
                        relaxed_preferences
                    )

                    relaxed_budget = True

                    break

        # -------------------------
        # EVALUATE QUERYSET ONCE
        # -------------------------
        house_list = list(houses)

        # -------------------------
        # STILL NO RESULTS
        # -------------------------
        if not house_list:

            return Response(
                {
                    "message": (
                        "No houses matched your "
                        "requirements."
                    ),
                    "recommendations": [],
                    "total_matches": 0,
                    "requested_top_n": (
                        original_preferences.get(
                            "top_n",
                            5
                        )
                    ),
                    "returned_count": 0,
                    "filters_applied": (
                        original_preferences
                    ),
                    "budget_relaxed": False
                },
                status=status.HTTP_200_OK
            )

        # -------------------------
        # TOTAL MATCHES
        # -------------------------
        total_matches = len(house_list)

        # -------------------------
        # REQUESTED TOP N
        # -------------------------
        requested_top_n = (
            original_preferences.get(
                "top_n",
                5
            )
        )

        # ==================================================
        # SCORE CANDIDATE HOUSES
        # ==================================================
        #
        # IMPORTANT:
        # We intentionally do NOT serialize the house
        # or generate its explanation here.
        #
        # Only lightweight scoring information is stored.
        #
        # This prevents expensive work for candidates
        # that will never appear in the final Top-N results.
        #
        scored_recommendations = []

        for house in house_list:

            score_result = calculate_house_score(
                house,
                preferences
            )

            scored_recommendations.append(
                {
                    "house": house,
                    "score": score_result[
                        "score"
                    ],
                    "matched_preferences": (
                        score_result[
                            "matched_preferences"
                        ]
                    ),
                    "unmatched_preferences": (
                        score_result[
                            "unmatched_preferences"
                        ]
                    )
                }
            )

        # ==================================================
        # RANK RECOMMENDATIONS
        # ==================================================
        #
        # Ranking is performed using the actual House
        # object rather than a serialized dictionary.
        #
        # This avoids creating thousands of serialized
        # dictionaries before Top-N selection.
        #
        scored_recommendations.sort(
            key=lambda item: (
                item["score"],
                -item["house"].rent,
                item["house"].area_sqft
            ),
            reverse=True
        )

        # ==================================================
        # TOP N SELECTION
        # ==================================================
        #
        # Only the best N candidates continue to the
        # expensive explanation + serialization stage.
        #
        top_recommendations = (
            scored_recommendations[
                :requested_top_n
            ]
        )

        # ==================================================
        # BUILD FINAL RECOMMENDATIONS
        # ==================================================
        recommendations = []

        for recommendation in (
            top_recommendations
        ):

            house = recommendation["house"]

            score_result = {
                "score": recommendation["score"],
                "matched_preferences": (
                    recommendation[
                        "matched_preferences"
                    ]
                ),
                "unmatched_preferences": (
                    recommendation[
                        "unmatched_preferences"
                    ]
                )
            }

            # ------------------------------------------
            # Generate explanation ONLY for Top-N
            # ------------------------------------------
            explanation = (
                generate_house_explanation(
                    house,
                    preferences,
                    score_result
                )
            )

            # ------------------------------------------
            # Serialize ONLY Top-N
            # ------------------------------------------
            serialized_house = (
                HouseSerializer(
                    house
                ).data
            )

            recommendations.append(
                {
                    "house": serialized_house,

                    "score": (
                        score_result[
                            "score"
                        ]
                    ),

                    "matched_preferences": (
                        score_result[
                            "matched_preferences"
                        ]
                    ),

                    "unmatched_preferences": (
                        score_result[
                            "unmatched_preferences"
                        ]
                    ),

                    "explanation": explanation
                }
            )

        # -------------------------
        # RESPONSE METADATA
        # -------------------------
        response_data = {

            "recommendations": (
                recommendations
            ),

            "total_matches": (
                total_matches
            ),

            "requested_top_n": (
                requested_top_n
            ),

            "returned_count": (
                len(recommendations)
            ),

            "filters_applied": (
                original_preferences
            ),

            "budget_relaxed": (
                relaxed_budget
            )
        }

        # -------------------------
        # BUDGET FALLBACK INFORMATION
        # -------------------------
        if relaxed_budget:

            response_data["message"] = (
                "No houses matched your original "
                "budget. Showing recommendations "
                "with a slightly higher budget."
            )

            response_data[
                "original_max_rent"
            ] = original_max_rent

            response_data[
                "relaxed_max_rent"
            ] = relaxed_max_rent

        # -------------------------
        # RESPONSE
        # -------------------------
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
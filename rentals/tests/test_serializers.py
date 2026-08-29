from django.test import SimpleTestCase

from rentals.serializers import RecommendationRequestSerializer


class RecommendationRequestSerializerTests(SimpleTestCase):

    # -------------------------
    # VALID REQUEST
    # -------------------------
    def test_valid_recommendation_request(self):

        data = {
            "location": "HSR",
            "max_rent": 40000,
            "min_rent": 20000,
            "bedrooms": 2,
            "bedroom_mode": "exact",
            "furnished": True,
            "parking": False,
            "required_parking": False,
            "priority": {
                "location": "important",
                "budget": "important",
                "bedrooms": "important",
                "furnished": "preferred",
                "parking": "must_have"
            },
            "top_n": 5
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

    # -------------------------
    # NEGATIVE MAX RENT
    # -------------------------
    def test_negative_max_rent_is_rejected(self):

        data = {
            "max_rent": -1000
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "max_rent",
            serializer.errors
        )

    # -------------------------
    # NEGATIVE MIN RENT
    # -------------------------
    def test_negative_min_rent_is_rejected(self):

        data = {
            "min_rent": -5000
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "min_rent",
            serializer.errors
        )

    # -------------------------
    # INVALID BEDROOM MODE
    # -------------------------
    def test_invalid_bedroom_mode_is_rejected(self):

        data = {
            "bedrooms": 2,
            "bedroom_mode": "wrong"
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "bedroom_mode",
            serializer.errors
        )

    # -------------------------
    # MIN RENT GREATER THAN MAX RENT
    # -------------------------
    def test_min_rent_greater_than_max_rent_is_rejected(self):

        data = {
            "min_rent": 50000,
            "max_rent": 30000
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertTrue(
            "rent" in serializer.errors
            or "non_field_errors"
            in serializer.errors
        )

    # -------------------------
    # TOP N ABOVE LIMIT
    # -------------------------
    def test_top_n_above_maximum_is_rejected(self):

        data = {
            "top_n": 101
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "top_n",
            serializer.errors
        )

    # -------------------------
    # TOP N BELOW MINIMUM
    # -------------------------
    def test_top_n_below_minimum_is_rejected(self):

        data = {
            "top_n": 0
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "top_n",
            serializer.errors
        )

    # -------------------------
    # INVALID PRIORITY
    # -------------------------
    def test_invalid_priority_is_rejected(self):

        data = {
            "priority": {
                "location": "wrong"
            }
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "priority",
            serializer.errors
        )

    # -------------------------
    # VALID PRIORITY LEVELS
    # -------------------------
    def test_valid_priority_levels_are_accepted(self):

        data = {
            "priority": {
                "location": "must_have",
                "budget": "important",
                "bedrooms": "preferred",
                "furnished": "optional",
                "parking": "must_have"
            }
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

    # -------------------------
    # NEGATIVE BEDROOMS
    # -------------------------
    def test_negative_bedrooms_are_rejected(self):

        data = {
            "bedrooms": -1
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "bedrooms",
            serializer.errors
        )

    # -------------------------
    # BOOLEAN PREFERENCES
    # -------------------------
    def test_boolean_preferences_are_accepted(self):

        data = {
            "furnished": True,
            "parking": False,
            "required_parking": True
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

    # -------------------------
    # DEFAULT TOP N
    # -------------------------
    def test_top_n_has_expected_default(self):

        serializer = RecommendationRequestSerializer(
            data={}
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

        self.assertEqual(
            serializer.validated_data.get(
                "top_n",
                5
            ),
            5
        )

    # -------------------------
    # DEFAULT BEDROOM MODE
    # -------------------------
    def test_bedroom_mode_defaults_to_exact(self):

        data = {
            "bedrooms": 2
        }

        serializer = RecommendationRequestSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

        self.assertEqual(
            serializer.validated_data.get(
                "bedroom_mode"
            ),
            "exact"
        )
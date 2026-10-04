"""Enumerations shared by models, serializers and the recommendation engine."""

from django.db import models


class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "Apartment"
    INDEPENDENT_HOUSE = "independent_house", "Independent house"
    VILLA = "villa", "Villa"
    STUDIO = "studio", "Studio"
    PENTHOUSE = "penthouse", "Penthouse"


class ListingStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    # Suspicious or invalid listings held for admin review; hidden from users.
    FLAGGED = "flagged", "Flagged for review"


class Priority(models.TextChoices):
    MUST_HAVE = "must_have", "Must have"
    IMPORTANT = "important", "Important"
    PREFERRED = "preferred", "Preferred"
    OPTIONAL = "optional", "Optional"


class BedroomMode(models.TextChoices):
    EXACT = "exact", "Exact"
    MINIMUM = "minimum", "Minimum"


class InteractionType(models.TextChoices):
    VIEW = "VIEW", "View"
    FAVORITE = "FAVORITE", "Favorite"
    UNFAVORITE = "UNFAVORITE", "Unfavorite"
    CONTACT = "CONTACT", "Contact"


AMENITIES = [
    "lift",
    "power_backup",
    "security",
    "gym",
    "swimming_pool",
    "clubhouse",
    "play_area",
    "wifi",
    "air_conditioning",
    "gated_community",
    "pet_friendly",
    "balcony",
    "modular_kitchen",
    "water_supply_24x7",
    "visitor_parking",
    "cctv",
]

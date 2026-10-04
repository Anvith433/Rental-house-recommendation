"""Small test helpers for building users, properties and authenticated clients."""

from itertools import count

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from rentals.models import House, PropertyImage

_sequence = count(1)

DEFAULT_PASSWORD = "Sup3r-Secret-Pass!"


def make_user(email=None, password=DEFAULT_PASSWORD, admin=False, **extra):
    User = get_user_model()
    email = email or f"user{next(_sequence)}@example.com"
    if admin:
        return User.objects.create_superuser(email=email, password=password, **extra)
    return User.objects.create_user(email=email, password=password, **extra)


def make_house(**overrides):
    values = {
        "title": "2BHK HSR Apartment",
        "location": "HSR Layout",
        "rent": 23000,
        "bedrooms": 2,
        "bathrooms": 2,
        "furnished": True,
        "parking": False,
        "area_sqft": 1100,
    }
    values.update(overrides)
    image_url = values.pop("image_url", None)
    house = House.objects.create(**values)
    if image_url:
        PropertyImage.objects.create(property=house, image_url=image_url, is_primary=True)
    return house


def auth_client(user) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def property_payload(**overrides):
    payload = {
        "title": "Bright 2 BHK Apartment near Agara Lake",
        "description": "Well-lit apartment close to the lake.",
        "location": "HSR Layout",
        "city": "Bangalore",
        "rent": 28000,
        "security_deposit": 56000,
        "bedrooms": 2,
        "bathrooms": 2,
        "area_sqft": 1150,
        "furnished": True,
        "parking": True,
        "property_type": "apartment",
        "amenities": ["lift", "gym"],
        "images": [
            {"image_url": "/images/properties/apartment-1.svg", "caption": "Exterior"},
            {"image_url": "https://example.com/living.jpg", "caption": "Living room"},
        ],
    }
    payload.update(overrides)
    return payload

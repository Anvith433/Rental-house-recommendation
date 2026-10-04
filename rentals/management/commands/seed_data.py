"""Seed realistic demo listings across Bangalore localities.

    python manage.py seed_data                 # 64 properties (skips if any exist)
    python manage.py seed_data --count 120     # more properties
    python manage.py seed_data --reset         # delete existing properties first
    python manage.py seed_data --demo-users    # also create demo admin + user

Demo user passwords come from SEED_DEMO_PASSWORD, or are randomly generated
and printed once. Data is generated deterministically (fixed RNG seed).
"""

import os
import random
import secrets
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rentals.choices import ListingStatus, PropertyType
from rentals.models import House, PropertyImage


@dataclass(frozen=True)
class Locality:
    name: str
    latitude: float
    longitude: float
    price_factor: float
    landmarks: tuple[str, ...]


LOCALITIES = (
    Locality("HSR Layout", 12.9116, 77.6474, 1.15, ("Agara Lake", "27th Main", "Sector 2")),
    Locality("Koramangala", 12.9352, 77.6245, 1.30, ("Forum Mall", "5th Block", "Sony World Signal")),
    Locality("BTM Layout", 12.9166, 77.6101, 0.95, ("Udupi Garden", "2nd Stage", "Silk Board")),
    Locality("Electronic City", 12.8452, 77.6602, 0.70, ("Infosys Campus", "Phase 1", "Neeladri Road")),
    Locality("Whitefield", 12.9698, 77.7500, 0.95, ("ITPL", "Phoenix Marketcity", "Hope Farm")),
    Locality("Indiranagar", 12.9784, 77.6408, 1.40, ("100 Feet Road", "CMH Road", "Indiranagar Metro")),
    Locality("Marathahalli", 12.9591, 77.6974, 0.85, ("Outer Ring Road", "Kalamandir", "Munnekollal")),
    Locality("Jayanagar", 12.9250, 77.5938, 1.10, ("4th Block", "Jayanagar Metro", "Ashoka Pillar")),
    Locality("Bellandur", 12.9304, 77.6784, 1.00, ("Ecospace", "Central Mall", "Sarjapur Road")),
    Locality("JP Nagar", 12.9063, 77.5857, 0.95, ("Mini Forest", "6th Phase", "Puttenahalli Lake")),
)

# Base monthly rent (₹) by bedroom count, before locality/type adjustments.
BASE_RENT = {0: 12000, 1: 16000, 2: 25000, 3: 36000, 4: 58000}
TYPE_FACTOR = {
    PropertyType.STUDIO: 1.0,
    PropertyType.APARTMENT: 1.0,
    PropertyType.INDEPENDENT_HOUSE: 1.1,
    PropertyType.VILLA: 1.6,
    PropertyType.PENTHOUSE: 1.8,
}
AREA_PER_BEDROOM = {0: 450, 1: 650, 2: 1100, 3: 1550, 4: 2300}

TYPE_LABEL = {
    PropertyType.STUDIO: "Studio",
    PropertyType.APARTMENT: "Apartment",
    PropertyType.INDEPENDENT_HOUSE: "Independent House",
    PropertyType.VILLA: "Villa",
    PropertyType.PENTHOUSE: "Penthouse",
}
ADJECTIVES = ("Spacious", "Bright", "Well-ventilated", "Modern", "Cosy", "Newly renovated", "Premium", "Airy")
EXTERIOR_IMAGE = {
    PropertyType.STUDIO: "apartment",
    PropertyType.APARTMENT: "apartment",
    PropertyType.PENTHOUSE: "apartment",
    PropertyType.INDEPENDENT_HOUSE: "house",
    PropertyType.VILLA: "villa",
}
APARTMENT_AMENITIES = ["lift", "power_backup", "security", "cctv", "water_supply_24x7"]
OPTIONAL_AMENITIES = [
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
    "visitor_parking",
]


def _round_to(value: float, step: int) -> int:
    return int(round(value / step) * step)


def _pick_type(rng: random.Random) -> PropertyType:
    return rng.choices(
        [
            PropertyType.APARTMENT,
            PropertyType.INDEPENDENT_HOUSE,
            PropertyType.STUDIO,
            PropertyType.VILLA,
            PropertyType.PENTHOUSE,
        ],
        weights=[60, 18, 10, 7, 5],
    )[0]


def _bedrooms_for(rng: random.Random, property_type: PropertyType) -> int:
    if property_type == PropertyType.STUDIO:
        return 1
    if property_type == PropertyType.VILLA:
        return rng.choice([3, 4])
    if property_type == PropertyType.PENTHOUSE:
        return rng.choice([3, 4])
    return rng.choices([1, 2, 3, 4], weights=[25, 45, 24, 6])[0]


def build_property(rng: random.Random, index: int) -> tuple[House, list[PropertyImage]]:
    locality = LOCALITIES[index % len(LOCALITIES)]
    property_type = _pick_type(rng)
    bedrooms = _bedrooms_for(rng, property_type)
    rent_key = 0 if property_type == PropertyType.STUDIO else bedrooms
    furnished = rng.random() < 0.55
    parking = property_type != PropertyType.STUDIO and rng.random() < 0.7

    rent = BASE_RENT[rent_key] * locality.price_factor * TYPE_FACTOR[property_type]
    rent *= 1.12 if furnished else 1.0
    rent *= rng.uniform(0.9, 1.12)
    rent = _round_to(rent, 500)

    area = _round_to(AREA_PER_BEDROOM[rent_key] * TYPE_FACTOR[property_type] ** 0.5 * rng.uniform(0.9, 1.15), 10)
    bathrooms = max(1, bedrooms - (1 if bedrooms >= 3 and rng.random() < 0.4 else 0))

    is_highrise = property_type in (PropertyType.APARTMENT, PropertyType.PENTHOUSE, PropertyType.STUDIO)
    total_floors = rng.choice([4, 8, 12, 18, 24]) if is_highrise else rng.choice([2, 3])
    floor = total_floors if property_type == PropertyType.PENTHOUSE else rng.randint(0, total_floors)

    amenities = set(rng.sample(OPTIONAL_AMENITIES, k=rng.randint(2, 6)))
    if is_highrise:
        amenities.update(APARTMENT_AMENITIES)
    if property_type == PropertyType.VILLA:
        amenities.update({"gated_community", "security"})

    landmark = rng.choice(locality.landmarks)
    label = TYPE_LABEL[property_type]
    bhk = "Studio" if property_type == PropertyType.STUDIO else f"{bedrooms} BHK"
    title = (
        f"{rng.choice(ADJECTIVES)} {label} near {landmark}"
        if property_type == PropertyType.STUDIO
        else f"{rng.choice(ADJECTIVES)} {bhk} {label} near {landmark}"
    )
    furnishing = "fully furnished" if furnished else "unfurnished"
    floor_text = "on the ground floor" if floor == 0 else f"on floor {floor} of {total_floors}"
    description = (
        f"A {furnishing} {bhk.lower() if bhk != 'Studio' else 'studio'} {label.lower()} in "
        f"{locality.name}, a short walk from {landmark}. The home offers {area} sq ft with "
        f"{bathrooms} bathroom{'s' if bathrooms > 1 else ''}, {floor_text}"
        f"{', with covered parking' if parking else ''}. "
        f"Security deposit is typically {('three' if rent > 40000 else 'two')} months' rent. "
        "Ideal for working professionals and families looking for a well-connected neighbourhood."
    )

    status = ListingStatus.ACTIVE
    if index % 23 == 22:
        status = ListingStatus.INACTIVE
    elif index % 31 == 30:
        status = ListingStatus.FLAGGED

    house = House(
        title=title,
        description=description,
        location=locality.name,
        city="Bangalore",
        state="Karnataka",
        latitude=Decimal(str(round(locality.latitude + rng.uniform(-0.01, 0.01), 6))),
        longitude=Decimal(str(round(locality.longitude + rng.uniform(-0.01, 0.01), 6))),
        rent=rent,
        security_deposit=rent * (3 if rent > 40000 else 2),
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_sqft=area,
        furnished=furnished,
        parking=parking,
        property_type=property_type,
        floor=floor,
        total_floors=total_floors,
        available_from=timezone.localdate() + timedelta(days=rng.choice([0, 0, 7, 15, 30, 45])),
        amenities=sorted(amenities),
        status=status,
    )

    palette = rng.randint(1, 3)
    image_specs = [
        (f"/images/properties/{EXTERIOR_IMAGE[property_type]}-{palette}.svg", "Exterior", True),
        (f"/images/properties/living-{rng.randint(1, 3)}.svg", "Living room", False),
        (f"/images/properties/bedroom-{rng.randint(1, 3)}.svg", "Bedroom", False),
        (f"/images/properties/kitchen-{rng.randint(1, 3)}.svg", "Kitchen", False),
    ]
    images = [PropertyImage(image_url=url, caption=caption, is_primary=primary) for url, caption, primary in image_specs]
    return house, images


class Command(BaseCommand):
    help = "Seed realistic demo rental listings (and optionally demo users)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=64, help="Number of properties to create.")
        parser.add_argument("--reset", action="store_true", help="Delete all properties first.")
        parser.add_argument("--demo-users", action="store_true", help="Create demo admin and user accounts.")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible data.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["demo_users"]:
            self._create_demo_users()

        if options["reset"]:
            deleted, _ = House.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} existing rows.")
        elif House.objects.exists():
            self.stdout.write("Properties already exist; skipping (use --reset to reseed).")
            return

        rng = random.Random(options["seed"])
        admin = get_user_model().objects.filter(role="ADMIN").order_by("id").first()
        built = [build_property(rng, index) for index in range(options["count"])]
        for house, _ in built:
            house.owner = admin
        House.objects.bulk_create([house for house, _ in built])
        images = []
        for house, house_images in built:
            for image in house_images:
                image.property = house
                images.append(image)
        PropertyImage.objects.bulk_create(images)
        self.stdout.write(self.style.SUCCESS(f"Created {len(built)} properties with {len(images)} images."))

    def _create_demo_users(self):
        User = get_user_model()
        password = os.environ.get("SEED_DEMO_PASSWORD")
        generated = not password
        accounts = [
            ("admin@rentwise.dev", "Asha", "Rao", True),
            ("demo@rentwise.dev", "Rohan", "Mehta", False),
        ]
        for email, first, last, is_admin in accounts:
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"{email} already exists; leaving it unchanged.")
                continue
            account_password = password or secrets.token_urlsafe(12)
            create = User.objects.create_superuser if is_admin else User.objects.create_user
            create(email=email, password=account_password, first_name=first, last_name=last)
            shown = account_password if generated else "(from SEED_DEMO_PASSWORD)"
            self.stdout.write(self.style.SUCCESS(f"Created {'admin' if is_admin else 'user'} {email} / {shown}"))

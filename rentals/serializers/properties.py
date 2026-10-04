from django.db import transaction
from rest_framework import serializers

from ..choices import AMENITIES
from ..models import House, PropertyImage

MAX_IMAGES_PER_PROPERTY = 12


def validate_image_url(value: str) -> str:
    """Allow absolute http(s) URLs or site-relative paths only. Blocks
    ``javascript:``/``data:`` URLs and protocol-relative ``//host`` URLs."""
    value = value.strip()
    if value.startswith(("https://", "http://")) or (
        value.startswith("/") and not value.startswith("//")
    ):
        if any(char.isspace() for char in value) or '"' in value or "<" in value:
            raise serializers.ValidationError("Image URL contains invalid characters.")
        return value
    raise serializers.ValidationError("Image URL must be an http(s) URL or a path starting with '/'.")


class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(max_length=500, validators=[validate_image_url])

    class Meta:
        model = PropertyImage
        fields = ["id", "image_url", "caption", "is_primary"]
        read_only_fields = ["id"]


class PropertyListSerializer(serializers.ModelSerializer):
    """Compact representation for grids, favorites and recommendation cards."""

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = [
            "id",
            "title",
            "location",
            "city",
            "rent",
            "security_deposit",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "furnished",
            "parking",
            "property_type",
            "available_from",
            "status",
            "primary_image",
            "created_at",
        ]

    def get_primary_image(self, obj) -> str | None:
        return obj.primary_image_src


class PropertySerializer(serializers.ModelSerializer):
    """Full property representation. ``images`` is writable: when supplied on
    create/update it replaces the property's image set."""

    images = PropertyImageSerializer(many=True, required=False)
    primary_image = serializers.SerializerMethodField()
    amenities = serializers.ListField(
        child=serializers.ChoiceField(choices=AMENITIES), required=False, max_length=len(AMENITIES)
    )
    title = serializers.CharField(max_length=200, min_length=5)
    location = serializers.CharField(max_length=100, min_length=2)

    class Meta:
        model = House
        fields = [
            "id",
            "title",
            "description",
            "location",
            "city",
            "state",
            "latitude",
            "longitude",
            "rent",
            "security_deposit",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "furnished",
            "parking",
            "property_type",
            "floor",
            "total_floors",
            "available_from",
            "amenities",
            "status",
            "images",
            "primary_image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_primary_image(self, obj) -> str | None:
        return obj.primary_image_src

    def validate_amenities(self, value):
        return sorted(set(value))

    def validate_images(self, value):
        if len(value) > MAX_IMAGES_PER_PROPERTY:
            raise serializers.ValidationError(
                f"A property can have at most {MAX_IMAGES_PER_PROPERTY} images."
            )
        if sum(1 for image in value if image.get("is_primary")) > 1:
            raise serializers.ValidationError("Only one image can be marked as primary.")
        return value

    def validate(self, attrs):
        floor = attrs.get("floor", getattr(self.instance, "floor", None))
        total_floors = attrs.get("total_floors", getattr(self.instance, "total_floors", None))
        if floor is not None and total_floors is not None and floor > total_floors:
            raise serializers.ValidationError({"floor": "Floor cannot exceed total_floors."})
        return attrs

    @staticmethod
    def _replace_images(house, images):
        house.images.all().delete()
        if not images:
            return
        has_primary = any(image.get("is_primary") for image in images)
        PropertyImage.objects.bulk_create(
            PropertyImage(
                property=house,
                image_url=image["image_url"],
                caption=image.get("caption", ""),
                is_primary=image.get("is_primary", False) or (not has_primary and index == 0),
            )
            for index, image in enumerate(images)
        )

    @transaction.atomic
    def create(self, validated_data):
        images = validated_data.pop("images", [])
        house = super().create(validated_data)
        self._replace_images(house, images)
        return house

    @transaction.atomic
    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)
        house = super().update(instance, validated_data)
        if images is not None:
            self._replace_images(house, images)
        return house


# Backward-compatible name used by the original API.
HouseSerializer = PropertySerializer

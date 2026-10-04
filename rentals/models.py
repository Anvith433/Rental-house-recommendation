from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import OuterRef, Q, Subquery

from .choices import BedroomMode, InteractionType, ListingStatus, PropertyType

MAX_RENT = 10_000_000
MAX_ROOMS = 20


class HouseQuerySet(models.QuerySet):
    def with_primary_image(self):
        """Annotate ``primary_image_url`` via a correlated subquery, so list
        views get each card's image without loading every image row."""
        primary = PropertyImage.objects.filter(property=OuterRef("pk")).order_by(
            "-is_primary", "id"
        )
        return self.annotate(primary_image_url=Subquery(primary.values("image_url")[:1]))


class House(models.Model):
    """A rental property listing.

    The model keeps its original ``House`` name (and table) for backward
    compatibility; the API exposes it as a *property*.
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # ``location`` is the locality used for matching (e.g. "HSR Layout").
    location = models.CharField(max_length=100)
    city = models.CharField(max_length=100, default="Bangalore")
    state = models.CharField(max_length=100, default="Karnataka")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    rent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(MAX_RENT)])
    security_deposit = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(MAX_RENT * 12)]
    )

    bedrooms = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(MAX_ROOMS)])
    bathrooms = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(MAX_ROOMS)])
    area_sqft = models.IntegerField(validators=[MinValueValidator(50), MaxValueValidator(100_000)])
    furnished = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)

    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.APARTMENT
    )
    floor = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(-2), MaxValueValidator(200)]
    )
    total_floors = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(200)]
    )
    available_from = models.DateField(null=True, blank=True)
    amenities = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=10, choices=ListingStatus.choices, default=ListingStatus.ACTIVE
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="listed_properties",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = HouseQuerySet.as_manager()

    class Meta:
        indexes = [
            # Recommendation hard filters: exact/minimum bedrooms + rent range.
            models.Index(fields=["bedrooms", "rent"], name="house_bedrooms_rent_idx"),
            # Browsing active listings filtered/sorted by rent.
            models.Index(fields=["status", "rent"], name="house_status_rent_idx"),
            # Default listing order (newest active listings first).
            models.Index(fields=["status", "-created_at"], name="house_status_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(rent__gte=0), name="house_rent_non_negative"),
            models.CheckConstraint(
                condition=Q(security_deposit__gte=0), name="house_deposit_non_negative"
            ),
            models.CheckConstraint(
                condition=Q(bedrooms__gte=0) & Q(bedrooms__lte=MAX_ROOMS),
                name="house_bedrooms_range",
            ),
            models.CheckConstraint(
                condition=Q(bathrooms__gte=0) & Q(bathrooms__lte=MAX_ROOMS),
                name="house_bathrooms_range",
            ),
            models.CheckConstraint(condition=Q(area_sqft__gt=0), name="house_area_positive"),
        ]

    def __str__(self):
        return self.title

    @property
    def primary_image_src(self) -> str | None:
        """Primary image URL, from the ``with_primary_image()`` annotation when
        present, otherwise from (ideally prefetched) images."""
        if hasattr(self, "primary_image_url"):
            return self.primary_image_url
        images = list(self.images.all())
        if not images:
            return None
        return next((image for image in images if image.is_primary), images[0]).image_url


class PropertyImage(models.Model):
    property = models.ForeignKey(House, on_delete=models.CASCADE, related_name="images")
    image_url = models.CharField(max_length=500)
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Image for {self.property_id}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    property = models.ForeignKey(House, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "property"], name="unique_user_favorite")
        ]

    def __str__(self):
        return f"{self.user_id} ♥ {self.property_id}"


class UserPreference(models.Model):
    """A user's saved recommendation preferences (one row per user)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference"
    )
    location = models.CharField(max_length=100, blank=True)
    min_rent = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    max_rent = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    bedrooms = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(MAX_ROOMS)]
    )
    bedroom_mode = models.CharField(
        max_length=10, choices=BedroomMode.choices, default=BedroomMode.EXACT
    )
    furnished = models.BooleanField(null=True, blank=True)
    parking = models.BooleanField(null=True, blank=True)
    required_parking = models.BooleanField(default=False)
    # {"location": "must_have", "budget": "important", ...}
    priority = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences of {self.user_id}"

    def as_preferences(self) -> dict:
        """The saved preferences in the recommendation engine's input format."""
        preferences = {"bedroom_mode": self.bedroom_mode, "required_parking": self.required_parking}
        for field in ("location", "min_rent", "max_rent", "bedrooms", "furnished", "parking"):
            value = getattr(self, field)
            if value not in (None, ""):
                preferences[field] = value
        if self.priority:
            preferences["priority"] = dict(self.priority)
        return preferences


class RecommendationHistory(models.Model):
    """One recommendation request by a signed-in user, with the IDs it
    returned and lightweight pipeline metrics (not the full payload)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_history"
    )
    request_preferences = models.JSONField()
    result_property_ids = models.JSONField(default=list)
    top_score = models.FloatField(null=True, blank=True)
    total_matches = models.PositiveIntegerField(default=0)
    budget_relaxed = models.BooleanField(default=False)
    latency_ms = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="rechistory_user_created_idx"),
            models.Index(fields=["created_at"], name="rechistory_created_idx"),
        ]
        verbose_name_plural = "recommendation history"


class PropertyInteraction(models.Model):
    """Implicit feedback events – the raw material for a future learned ranker."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interactions"
    )
    property = models.ForeignKey(House, on_delete=models.CASCADE, related_name="interactions")
    interaction_type = models.CharField(max_length=12, choices=InteractionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["property", "interaction_type"], name="interaction_property_type_idx"
            ),
            models.Index(fields=["user", "-created_at"], name="interaction_user_created_idx"),
        ]


class Inquiry(models.Model):
    """A user's request for more information about a listing."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        RESPONDED = "responded", "Responded"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries"
    )
    property = models.ForeignKey(House, on_delete=models.CASCADE, related_name="inquiries")
    message = models.TextField(max_length=2000)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

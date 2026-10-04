import django_filters
from django.db.models import Q

from .choices import ListingStatus, PropertyType
from .models import MAX_RENT, MAX_ROOMS, House


class PropertyFilter(django_filters.FilterSet):
    """Database-level property search. Invalid values produce a 400 response."""

    location = django_filters.CharFilter(method="filter_location", max_length=100)
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact", max_length=100)
    min_rent = django_filters.NumberFilter(
        field_name="rent", lookup_expr="gte", min_value=0, max_value=MAX_RENT
    )
    max_rent = django_filters.NumberFilter(
        field_name="rent", lookup_expr="lte", min_value=0, max_value=MAX_RENT
    )
    bedrooms = django_filters.NumberFilter(
        field_name="bedrooms", min_value=0, max_value=MAX_ROOMS
    )
    min_bedrooms = django_filters.NumberFilter(
        field_name="bedrooms", lookup_expr="gte", min_value=0, max_value=MAX_ROOMS
    )
    bathrooms = django_filters.NumberFilter(
        field_name="bathrooms", lookup_expr="gte", min_value=0, max_value=MAX_ROOMS
    )
    min_area = django_filters.NumberFilter(field_name="area_sqft", lookup_expr="gte", min_value=0)
    max_area = django_filters.NumberFilter(field_name="area_sqft", lookup_expr="lte", min_value=0)
    furnished = django_filters.BooleanFilter()
    parking = django_filters.BooleanFilter()
    property_type = django_filters.ChoiceFilter(choices=PropertyType.choices)
    available_by = django_filters.DateFilter(method="filter_available_by")
    status = django_filters.ChoiceFilter(choices=ListingStatus.choices)

    class Meta:
        model = House
        fields: list[str] = []

    def filter_location(self, queryset, name, value):
        return queryset.filter(Q(location__icontains=value) | Q(city__icontains=value))

    def filter_available_by(self, queryset, name, value):
        """Properties available on or before ``value`` (or with no date set,
        meaning available immediately)."""
        return queryset.filter(Q(available_from__isnull=True) | Q(available_from__lte=value))

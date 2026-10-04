from django.contrib import admin

from .models import (
    Favorite,
    House,
    Inquiry,
    PropertyImage,
    PropertyInteraction,
    RecommendationHistory,
    UserPreference,
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ["title", "location", "rent", "bedrooms", "property_type", "status", "created_at"]
    list_filter = ["status", "property_type", "furnished", "parking", "city"]
    search_fields = ["title", "location", "city"]
    list_editable = ["status"]
    inlines = [PropertyImageInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ["property", "user", "status", "created_at"]
    list_filter = ["status"]
    raw_id_fields = ["property", "user"]


admin.site.register(Favorite)
admin.site.register(UserPreference)
admin.site.register(RecommendationHistory)
admin.site.register(PropertyInteraction)

"""Platform statistics for the admin dashboard, computed with aggregate
queries (no per-row Python work)."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from core.metrics import recommendation_metrics

from ..choices import InteractionType, ListingStatus
from ..models import Favorite, House, Inquiry, PropertyInteraction, RecommendationHistory

TREND_DAYS = 14
TOP_LIMIT = 5


def platform_analytics() -> dict:
    User = get_user_model()
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    trend_start = (now - timedelta(days=TREND_DAYS - 1)).date()

    users = User.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        admins=Count("id", filter=Q(role=User.Role.ADMIN)),
        new_last_7_days=Count("id", filter=Q(created_at__gte=week_ago)),
    )
    properties = House.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=ListingStatus.ACTIVE)),
        inactive=Count("id", filter=Q(status=ListingStatus.INACTIVE)),
        flagged=Count("id", filter=Q(status=ListingStatus.FLAGGED)),
        average_rent=Avg("rent", filter=Q(status=ListingStatus.ACTIVE)),
    )
    recommendations = RecommendationHistory.objects.aggregate(
        total=Count("id"),
        last_7_days=Count("id", filter=Q(created_at__gte=week_ago)),
        average_latency_ms=Avg("latency_ms"),
        average_candidates=Avg("total_matches"),
        relaxed=Count("id", filter=Q(budget_relaxed=True)),
    )
    relaxed_count = recommendations.pop("relaxed")
    recommendations["budget_relaxation_rate"] = (
        round(relaxed_count / recommendations["total"], 4)
        if recommendations["total"]
        else None
    )
    for key in ("average_latency_ms", "average_candidates"):
        if recommendations[key] is not None:
            recommendations[key] = round(recommendations[key], 2)
    if properties["average_rent"] is not None:
        properties["average_rent"] = round(properties["average_rent"])

    daily = (
        RecommendationHistory.objects.filter(created_at__date__gte=trend_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    counts_by_day = {row["day"]: row["count"] for row in daily}
    trend = [
        {
            "date": (trend_start + timedelta(days=offset)).isoformat(),
            "count": counts_by_day.get(trend_start + timedelta(days=offset), 0),
        }
        for offset in range(TREND_DAYS)
    ]

    most_favorited = list(
        House.objects.annotate(favorites_total=Count("favorited_by"))
        .filter(favorites_total__gt=0)
        .order_by("-favorites_total", "id")
        .values("id", "title", "location", "favorites_total")[:TOP_LIMIT]
    )
    most_viewed = list(
        House.objects.annotate(
            views_total=Count(
                "interactions", filter=Q(interactions__interaction_type=InteractionType.VIEW)
            )
        )
        .filter(views_total__gt=0)
        .order_by("-views_total", "id")
        .values("id", "title", "location", "views_total")[:TOP_LIMIT]
    )
    listings_by_location = list(
        House.objects.filter(status=ListingStatus.ACTIVE)
        .values("location")
        .annotate(count=Count("id"))
        .order_by("-count", "location")[:10]
    )

    return {
        "users": users,
        "properties": properties,
        "favorites": {"total": Favorite.objects.count()},
        "inquiries": {
            "total": Inquiry.objects.count(),
            "new": Inquiry.objects.filter(status=Inquiry.Status.NEW).count(),
        },
        "interactions": {
            "views_last_7_days": PropertyInteraction.objects.filter(
                interaction_type=InteractionType.VIEW, created_at__gte=week_ago
            ).count()
        },
        "recommendations": recommendations,
        "recommendation_trend": trend,
        "most_favorited": most_favorited,
        "most_viewed": most_viewed,
        "listings_by_location": listings_by_location,
        "engine_metrics": recommendation_metrics.snapshot(),
    }

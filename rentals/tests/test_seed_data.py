import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from rentals.models import House, PropertyImage


class SeedDataCommandTests(TestCase):
    def test_seed_creates_varied_realistic_listings(self):
        call_command("seed_data", count=40, stdout=StringIO())
        self.assertEqual(House.objects.count(), 40)
        self.assertEqual(PropertyImage.objects.count(), 160)
        self.assertGreaterEqual(House.objects.values("location").distinct().count(), 8)
        self.assertGreaterEqual(House.objects.values("property_type").distinct().count(), 3)
        self.assertGreaterEqual(House.objects.values("bedrooms").distinct().count(), 3)
        self.assertTrue(House.objects.filter(furnished=True).exists())
        self.assertTrue(House.objects.filter(furnished=False).exists())
        self.assertTrue(House.objects.filter(parking=False).exists())
        for house in House.objects.all():
            house.full_clean()

    def test_seed_is_deterministic_and_skips_when_data_exists(self):
        call_command("seed_data", count=10, stdout=StringIO())
        titles = list(House.objects.order_by("id").values_list("title", flat=True))
        output = StringIO()
        call_command("seed_data", count=10, stdout=output)
        self.assertIn("skipping", output.getvalue())
        call_command("seed_data", count=10, reset=True, stdout=StringIO())
        self.assertEqual(list(House.objects.order_by("id").values_list("title", flat=True)), titles)

    @mock.patch.dict(os.environ, {"SEED_DEMO_PASSWORD": "Demo-Pass-2026!"})
    def test_demo_users_use_provided_password(self):
        call_command("seed_data", count=1, demo_users=True, stdout=StringIO())
        User = get_user_model()
        admin = User.objects.get(email="admin@rentwise.dev")
        self.assertTrue(admin.is_platform_admin)
        self.assertTrue(admin.check_password("Demo-Pass-2026!"))
        self.assertFalse(User.objects.get(email="demo@rentwise.dev").is_platform_admin)

from django.db import models


class House(models.Model):

    title = models.CharField(max_length=200)

    location = models.CharField(max_length=100)

    rent = models.IntegerField()

    bedrooms = models.IntegerField()

    bathrooms = models.IntegerField()

    furnished = models.BooleanField(default=False)

    parking = models.BooleanField(default=False)

    area_sqft = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        indexes = [
            models.Index(
                fields=["bedrooms", "rent"],
                name="house_bedrooms_rent_idx"
            ),
        ]

    def __str__(self):
        return self.title
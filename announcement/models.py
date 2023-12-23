
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from images.models import Images
from users.models import User


# Create your models here.
class CurrencyTypes(models.TextChoices):
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    UZS = 'UZS', 'So`m'


class TransportTypes(models.TextChoices):
    BUS = 'BUS', 'Avtobus'
    METRO = 'METRO', 'Metro'
    MARSHUTKA = 'MARSHUTKA', 'Marshutka'


class Transports(models.Model):
    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(choices=TransportTypes.choices, max_length=20)

    def __str__(self):
        return f"{self.name} {self.type}"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    images = models.ManyToManyField(Images, related_name="announcement")
    partnership = models.BooleanField(default=False)
    need_people_count = models.IntegerField(default=0)
    room_count = models.IntegerField(default=1)
    address = models.CharField(max_length=255, null=True, blank=True)
    location_x = models.CharField(max_length=255, null=True, blank=True)
    location_y = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CurrencyTypes.choices, default=CurrencyTypes.UZS)
    total_price = models.FloatField(null=True, blank=True)
    price_for_one = models.FloatField(null=True, blank=True)
    appartment_status = models.IntegerField(
        validators=[MaxValueValidator(10)]
    )
    description = models.TextField(null=True, blank=True)
    conditioner = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    transports = models.ManyToManyField(Transports, related_name="announcements")


class Like(models.Model):
    created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="likes")


class Comment(models.Model):
    created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField(null=True, blank=True)

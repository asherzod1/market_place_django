import uuid

from django.db import models


def image_upload_path(instance, filename):
    return f"images/{instance.uuid}/{filename}"


class Images(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    image = models.ImageField(upload_to=image_upload_path)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.uuid}/{self.name}"

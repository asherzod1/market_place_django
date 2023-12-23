from rest_framework import serializers

from announcement.models import Transports, Announcement
from images.serializers import ImageSerializer


class TransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transports
        fields = ["name", "type"]


class AnnouncementSerializer(serializers.ModelSerializer):
    transports = TransportSerializer(many=True)
    images = ImageSerializer(many=True)

    class Meta:
        model = Announcement
        fields = "__all__"

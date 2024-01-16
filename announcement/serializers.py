from rest_framework import serializers

from announcement.models import Transports, Announcement, Like, Comment
from images.serializers import ImageSerializer


class TransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transports
        fields = ["name", "type", "id"]


class AnnouncementSerializer(serializers.ModelSerializer):
    transports = TransportSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"


class LikeSerializer(serializers.ModelSerializer):
    announcement = AnnouncementSerializer(read_only=True)

    class Meta:
        model = Like
        fields = "__all__"


class CreateLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = ["created", "announcement"]


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = "__all__"

from rest_framework import serializers

from chat.models import ChatRoom, Message
from images.serializers import ImageSerializer
from users.models import User
from users.serializer import UserMeSerializer


class UserForChatSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'images', 'is_online']


class ChatRoomSerializer(serializers.ModelSerializer):
    users = UserForChatSerializer(read_only=True, many=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "created_at", "users", "messages"]

    def get_messages(self, obj):
        # Filtering messages where is_read is False
        messages = obj.messages.filter(is_read=False)  # Assuming 'messages' is the related name in the ChatRoom model
        return MessageSendSerializer(messages, many=True, read_only=True, context=self.context).data


class MessageSerializer(serializers.ModelSerializer):
    sender = UserForChatSerializer(read_only=True)
    receiver = UserForChatSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "receiver", "created_at", "room", "is_read", "message"]


class MessageSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "sender", "receiver", "created_at", "room", "is_read", "message"]


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    users = UserForChatSerializer(read_only=True, many=True)
    messages = MessageSendSerializer(read_only=True, many=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "created_at", "users", "messages"]


class ChatRoomCreatedSerializer(serializers.ModelSerializer):
    users = UserForChatSerializer(read_only=True, many=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "created_at", "users"]

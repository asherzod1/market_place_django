import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from announcement.models import Comment, Announcement
from announcement.serializers import CommentSerializer
from users.models import User


def get_serialized_data(db_result):
    serializer = CommentSerializer(db_result)
    return serializer.data

class AnnouncementComments(AsyncWebsocketConsumer):
    announcement_id = None
    group_name = None

    async def connect(self):
        self.announcement_id = self.scope['url_route']['kwargs']['announcement_id']
        self.group_name = f'comments_{self.announcement_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': "401"
                }
            )
        text_data_json = json.loads(text_data)
        message = text_data_json['text']
        announcement = await Announcement.objects.aget(id=self.announcement_id)
        comment = await Comment.objects.acreate(
            announcement=announcement,
            user=user,
            comment=message
        )
        # Send message to room group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': await sync_to_async(get_serialized_data)(comment)
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        print("CHAT")
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

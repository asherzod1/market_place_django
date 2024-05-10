import random
import string

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, ChatRoom
from .serializers import MessageSendSerializer, ChatRoomCreatedSerializer, MessageIsReadSerializer

User = get_user_model()


def get_serialized_data(db_result):
    serializer = MessageSendSerializer(db_result)
    return serializer.data


def get_room_serialized_data(db_result):
    serializer = ChatRoomCreatedSerializer(db_result)
    return serializer.data


def get_connected_users(current_user_id):
    # Get all users that are in the same room as the current user, directly excluding the current user
    # Since there are exactly two users per room, we directly target the other user.
    connected_users = User.objects.filter(
        rooms__users=current_user_id
    ).exclude(id=current_user_id).distinct().values_list("id", flat=True)
    return connected_users


def check_message_room(db_result, current_room_id):
    message = db_result
    room = message.room
    return room.id == current_room_id


class ChatConsumer(AsyncWebsocketConsumer):
    room_name = None
    room_group_name = None

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "401",
                    'message': 'You are not authenticated'
                }
            )

        user_ids = self.room_name.split('-')
        if str(user.id) not in user_ids:
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "403",
                    'message': 'You are not allowed to join this room'
                }
            )

        # Ensure the room exists or create it
        # await self.get_or_create_room(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = self.user.id
        receiver_id = text_data_json['receiver']

        # Save message to database

        obj = await self.save_message(sender_id, receiver_id, message, self.room_name)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': await sync_to_async(get_serialized_data)(obj)
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def not_allowed(self, event):
        status = event['status']
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'room_name': self.room_name,
            'status': status,
            'message': message,
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, room_name):
        sender = User.objects.get(pk=sender_id)
        receiver = User.objects.get(pk=receiver_id)
        room, created = ChatRoom.objects.get_or_create(name=room_name)

        if created:
            room.users.add(sender, receiver)

        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            room=room
        )

    @database_sync_to_async
    def get_or_create_room(self, room_name):
        return ChatRoom.objects.get_or_create(name=room_name)


def generate_unique_string(length=10):
    """ Berilgan uzunlikdagi takrorlanmas string yaratadi. """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class Chat(AsyncWebsocketConsumer):
    room_name = None
    room_group_name = None
    user = None

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.room_group_name = generate_unique_string(10)
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "401",
                    'message': 'You are not authenticated'
                }
            )
        self.room_group_name = f'chat_for_user_{self.user.id}'

        # Ensure the room exists or create it
        # await self.get_or_create_room(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        async for same_room_user_id in User.objects.filter(rooms__users=self.user.id).exclude(id=self.user.id).distinct().values_list("id", flat=True):
            await self.channel_layer.group_send(
                f'chat_for_user_{same_room_user_id}',
                {
                    'type': 'say_online',
                    'message': self.user.id
                }
            )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        async for same_room_user_id in User.objects.filter(rooms__users=self.user.id).exclude(id=self.user.id).distinct().values_list("id", flat=True):
            await self.channel_layer.group_send(
                f'chat_for_user_{same_room_user_id}',
                {
                    'type': 'say_offline',
                    'message': self.user.id
                }
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Read message
        if text_data_json.get('type', None) == 'read':
            return await self.read_message(text_data_json)
        # End read message

        # create room name
        message = text_data_json['message']
        sender_id = self.user.id
        receiver_id = text_data_json['receiver']
        user_ids = [int(sender_id), int(receiver_id)]
        user_ids = sorted(user_ids)
        room_name = f"chat_room_{user_ids[0]}-{user_ids[1]}"

        receiver_group_name = f'chat_for_user_{receiver_id}'

        message_obj, room_created, room = await self.save_message(sender_id, receiver_id, message, room_name)
        # if room created send it to room users
        if room_created:
            room_serialized_obj = await sync_to_async(get_room_serialized_data)(room)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'group_created',
                    'message': room_serialized_obj
                }
            )
            await self.channel_layer.group_send(
                receiver_group_name,
                {
                    'type': 'group_created',
                    'message': room_serialized_obj
                }
            )

        serialized_obj = await sync_to_async(get_serialized_data)(message_obj)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': serialized_obj
            }
        )
        await self.channel_layer.group_send(
            receiver_group_name,
            {
                'type': 'chat_message',
                'message': serialized_obj
            }
        )

    async def read_message(self, text_data_json):
        ids = text_data_json.get('ids', None)
        room_id = text_data_json['room_id']
        if not room_id:
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "400",
                    'message': 'Room id is required'
                }
            )
        message_objs = Message.objects.filter(pk__in=ids)
        first_message = await message_objs.afirst()
        if not first_message:
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "404",
                    'message': 'Message not found'
                }
            )
        if not await sync_to_async(check_message_room)(first_message, room_id):
            return await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'not_allowed',
                    'status': "403",
                    'message': 'You are not allowed to read this message, room id is not correct'
                }
            )
        message_sender_id = text_data_json.get('sender', None)

        await message_objs.aupdate(is_read=True)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read',
                'message': {
                    'is_read': 'true',
                    'ids': ids,
                    'room_id': room_id,
                    'sender': message_sender_id,
                    'receiver': self.user.id
                }
            }
        )
        receiver_group_name = f'chat_for_user_{message_sender_id}'
        await self.channel_layer.group_send(
            receiver_group_name,
            {
                'type': 'read',
                'message': {
                    'is_read': 'true',
                    'ids': ids,
                    'room_id': room_id,
                    'sender': message_sender_id,
                    'receiver': self.user.id
                }
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
        }))

    async def group_created(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'group_created',
            'message': message
        }))

    async def say_online(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'online',
            'message': {"user_id": message},
        }))

    async def say_offline(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'offline',
            'message': {"user_id": message},
        }))

    async def not_allowed(self, event):
        status = event['status']
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'room_name': self.room_name,
            'status': status,
            'message': message,
        }))

    async def read(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message': message,
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, room_name):
        sender = User.objects.get(pk=sender_id)
        receiver = User.objects.get(pk=receiver_id)
        room, created = ChatRoom.objects.get_or_create(name=room_name)

        if created:
            room.users.add(sender, receiver)

        message_obj = Message.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            room=room
        )
        return message_obj, created, room

    @database_sync_to_async
    def get_or_create_room(self, room_name):
        return ChatRoom.objects.get_or_create(name=room_name)

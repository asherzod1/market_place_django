from django.urls import path

from announcement.socket import AnnouncementComments
from chat.socket import ChatConsumer, Chat

websocket_urlpatterns = [
    path('ws/announcement/<int:announcement_id>/', AnnouncementComments.as_asgi()),
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),
    path('ws/chat/', Chat.as_asgi()),
]

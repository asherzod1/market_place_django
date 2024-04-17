from django.urls import path

from announcement.socket import AnnouncementComments

websocket_urlpatterns = [
    path('ws/announcement/<int:announcement_id>/', AnnouncementComments.as_asgi()),
]

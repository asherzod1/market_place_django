from django.contrib import admin

from chat.models import ChatRoom, Message


# Register your models here.


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "name", "created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "created_at", "room", "is_read", "message"]

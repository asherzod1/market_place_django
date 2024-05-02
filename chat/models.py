from django.db import models

from users.models import User


# Create your models here.


class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField("users.User", related_name="rooms")

    def __str__(self):
        return self.name


class Message(models.Model):
    sender = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="send_messages")
    receiver = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="receive_messages")
    created_at = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    is_read = models.BooleanField(default=False)
    message = models.TextField()

    def __str__(self):
        return f"{self.sender} - {self.message}, room: {self.room}"

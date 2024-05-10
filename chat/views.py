from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from chat.models import ChatRoom
from chat.serializers import ChatRoomSerializer, ChatRoomDetailSerializer


# Create your views here.


class UserRoomsViewSet(ReadOnlyModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ChatRoomSerializer
        return ChatRoomDetailSerializer

    def get_queryset(self):
        """
            This view should return a list of all the rooms
            for the currently authenticated user.
        """
        user = self.request.user
        return super().get_queryset().filter(users=user)

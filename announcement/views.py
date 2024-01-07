from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework_simplejwt.authentication import JWTAuthentication

from announcement.models import Transports, Announcement
from announcement.serializers import TransportSerializer, AnnouncementSerializer
from images.models import Images


# Create your views here.
class TransportViewSet(ModelViewSet):
    queryset = Transports.objects.all()
    serializer_class = TransportSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class AnnouncementViewSet(ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        serializer = self.get_serializer(data=request.data)
        try:
            images_uuid = request.data.get("images", [])
            images = Images.objects.filter(uuid__in=images_uuid)
        except TypeError as e:
            return Response("Images not found, Please send images uuid as list", status=status.HTTP_400_BAD_REQUEST)
        try:
            transports_ids = request.data.get("transports", [])
            transports = Transports.objects.filter(id__in=transports_ids)
        except TypeError as e:
            return Response("Transports not found, Please send transports id as list", status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        created_instance = serializer.instance
        created_instance.images.set(images)
        created_instance.transports.set(transports)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SelfAnnouncementViewSet(ListModelMixin, GenericViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


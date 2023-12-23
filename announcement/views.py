from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from announcement.models import Transports, Announcement
from announcement.serializers import TransportSerializer, AnnouncementSerializer


# Create your views here.
class TransportViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Transports.objects.all()
    serializer_class = TransportSerializer


class AnnouncementViewSet(ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

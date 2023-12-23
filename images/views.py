from rest_framework.viewsets import ModelViewSet

from images.models import Images
from images.serializers import ImageSerializer


# Create your views here.

class ImageViewSet(ModelViewSet):
    queryset = Images.objects.all()
    serializer_class = ImageSerializer

import requests
from django.db.models import F
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin

from announcement.models import Transports, Announcement, Like, Comment
from announcement.serializers import TransportSerializer, AnnouncementSerializer, LikeSerializer, CommentSerializer, \
    CreateLikeSerializer, CreateCommentSerializer
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = [
        'total_price', 'total_price_reverse',
        'price_for_one', 'price_for_one_reverse',
        'appartment_status', 'appartment_status_reverse',
    ]
    search_fields = ['title', 'description', "address"]
    filterset_fields = {
        'partnership': ["exact"],
        'need_people_count': ["exact"],
        'room_count': ["exact"],
        'conditioner': ["exact"],
        'washing_machine': ["exact"],
        'price_for_one': ['gte', 'lte'],
        'total_price': ['gte', 'lte'],
        'appartment_status': ['gte', 'lte'],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', None)
        if ordering is not None:
            if ordering.endswith('_reverse'):
                queryset = queryset.order_by(F(ordering[:-8]).desc())
            else:
                queryset = queryset.order_by(ordering)

        return queryset




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


class LikeViewSet(ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        serializer = CreateLikeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = Like.objects.filter(user=self.request.user, announcement=kwargs.get("pk")).first()
        print(instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        serializer = CreateCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProxyView(APIView):

    def get(self, request, *args, **kwargs):
        url = request.GET.get('url')
        if not url:
            return JsonResponse({'error': 'URL parameter is missing'}, status=400)

        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': 'full_version=1; city[key]=tashkent; lang=en; _ga=GA1.1.1646358430.1706364508; __gads=ID=9f2c0369ba9bcf63:T=1706364507:RT=1706364507:S=ALNI_Mb4Vq7N_H5hWevaofaqd8CMUi7SaQ; __gpi=UID=00000d4aae391291:T=1706364507:RT=1706364507:S=ALNI_MZ2-7rqdZNUiUcJZOoYOVAsSCVtSw; _ga_W8DR0B6NSF=GS1.1.1706364507.1.0.1706364512.55.0.0',
            'Referer': 'https://uz.easyway.info/en/cities/tashkent/routes',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        try:
            response = requests.get(url, headers=headers)
            print(response.json())
            data = response.json()
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

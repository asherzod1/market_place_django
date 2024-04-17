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
    CreateLikeSerializer, CreateCommentSerializer, EmptySerializer
from announcement.utilits import CustomPagination
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
    pagination_class = CustomPagination
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
        'fridge': ["exact"],
        'price_for_one': ['gte', 'lte'],
        'total_price': ['gte', 'lte'],
        'appartment_status': ['gte', 'lte'],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', None)
        transport_names = self.request.GET.getlist('transports[]', None)
        if transport_names:
            queryset = queryset.filter(transports__ri__in=transport_names).distinct()
        if ordering:
            desc_order = ordering.endswith('_reverse')
            if desc_order:
                field_name = ordering[:-8]  # Removes the '_reverse' suffix to get the field name
                queryset = queryset.order_by(F(field_name).desc())
            else:
                queryset = queryset.order_by(ordering)

        return queryset

    def filter_images(self, image_uuids):
        try:
            return Images.objects.filter(uuid__in=image_uuids)
        except TypeError:
            raise ValueError("Images not found. Please send image UUIDs as a list.")

    def create_transports(self, transport_data):
        transports = []
        for item in transport_data:
            transport, created = Transports.objects.get_or_create(name=item.get("name"), type=item.get("type"))
            transports.append(transport)
        return transports

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            images_uuid = request.data.get("images", [])
            images = self.filter_images(images_uuid)

            transports_ids = request.data.get("transports", [])
            transports = self.create_transports(transports_ids)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        created_instance = serializer.instance
        created_instance.images.set(images)
        created_instance.transports.set(transports)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            images_uuid = request.data.get("images", [])
            images = self.filter_images(images_uuid)

            transports_ids = request.data.get("transports", [])
            transports = self.create_transports(transports_ids)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        created_instance = serializer.instance
        created_instance.images.set(images)
        created_instance.transports.set(transports)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class SelfAnnouncementViewSet(ListModelMixin, GenericViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        announcement_id = request.GET.get("announcement_id")
        if announcement_id:
            queryset = queryset.filter(announcement_id=announcement_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProxyView(APIView):
    serializer_class = EmptySerializer

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

    def post(self, request, *args, **kwargs):
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
        url = request.data.get('url')
        data = request.data.copy()
        data.pop('url', None)
        if not url:
            return JsonResponse({'error': 'URL parameter is missing in the request data'}, status=400)
        try:
            response = requests.post(url, data=data, headers=headers)
            data = response.json()
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

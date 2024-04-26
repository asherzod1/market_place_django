import random

from django.contrib.auth import get_user_model, authenticate
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import GenericViewSet

from images.models import Images
from users.serializer import UserCreateSerializer, UserLoginSerializer, UserSerializer, UserUpdateSerializer, \
    UserMeSerializer, VerificationPhoneSerializer, VerificationCodeSerializer
from users.utilits import check_rate_limit, SmsOtp, verify_otp

User = get_user_model()


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "pk"

    def filter_images(self, image_uuids):
        try:
            return Images.objects.filter(uuid__in=image_uuids)
        except TypeError:
            raise ValueError("Images not found. Please send image UUIDs as a list.")

    def get_serializer(self, *args, **kwargs):
        if self.request.method == "PUT":
            kwargs['data'] = self.request.data  # Ensure the data is passed for validation
            kwargs['context'] = {'request': self.request}  # Pass request context if needed
            return UserUpdateSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user != self.get_object():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "You can't update because you are not this user. You can update your account"}
            )
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            with transaction.atomic():
                self.perform_update(serializer)

                # Handle image UUIDs
                images_uuid = request.data.get("images", [])
                images = self.filter_images(images_uuid)
                request.user.images.set(images)

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def me(self, request):
        serializer = UserMeSerializer(request.user, context={'request': request})
        # images = request.user.images.all()
        # images_serializer = ImageSerializer(images, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class UserCreateView(CreateAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        user = User.objects.filter(phone_number=phone_number).first()
        if not cache.get(f"verified_{phone_number}") and not user:
            return Response({"error": "Phone number is not verified"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        cache.delete(f"verified_{phone_number}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserLoginView(GenericAPIView):
    serializer_class = UserLoginSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            password = serializer.validated_data['password']
            user = authenticate(request, phone_number=phone_number, password=password)
            if user:
                userr = User.objects.get(phone_number=user.phone_number)
                token, created = Token.objects.get_or_create(user=userr)
                return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class GetPhoneNumberVerification(GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = VerificationPhoneSerializer

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_rate_limit(phone_number):
            return Response({"message": "Rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = User.objects.filter(phone_number=phone_number).first()
        if user:
            return Response({"message": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        otp = str(random.randint(10000, 99999))
        sms = SmsOtp(phone_number, otp)

        try:
            sms.send_otp()
        except Exception as e:
            return Response(
                {"message": "SMS service bilan xatolik", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"phone_number": phone_number}, status=status.HTTP_200_OK)


class VerificationCodeCheck(GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = VerificationCodeSerializer

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('code')
        if not phone_number or not otp:
            return Response({"error": "Phone number and Code is required"}, status=status.HTTP_400_BAD_REQUEST)

        if verify_otp(phone_number, otp):
            return Response({"message": "Phone number verified"}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

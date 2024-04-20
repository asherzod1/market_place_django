from django.contrib.auth import get_user_model, authenticate
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import GenericViewSet

from images.serializers import ImageSerializer
from users.serializer import UserCreateSerializer, UserLoginSerializer, UserSerializer, UserUpdateSerializer, \
    UserMeSerializer

User = get_user_model()


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_serializer(self, *args, **kwargs):
        if self.request.method == "PUT":
            kwargs['data'] = self.request.data  # Ensure the data is passed for validation
            kwargs['context'] = {'request': self.request}  # Pass request context if needed
            return UserUpdateSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user == self.get_object():
            # images_uuid = request.data.get("images", [])
            # images = self.filter_images(images_uuid)
            # request.user.images.set(images)
            return super().update(request, *args, **kwargs)
        return Response(
            status=400,
            data={"message": "You can't update, because you are not this user. You can update your account"}
        )

    @action(detail=False)
    def me(self, request):
        serializer = UserMeSerializer(request.user)
        # images = request.user.images.all()
        # images_serializer = ImageSerializer(images, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class UserCreateView(CreateAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer


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

from django.contrib.auth import get_user_model
from rest_framework import serializers

from images.serializers import ImageSerializer
from users.models import User as UserType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    class Meta:
        model = User
        fields = ["name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'phone_number', 'password']

    def create(self, validated_data):
        user = User.objects.create(
            phone_number=validated_data['phone_number'],
            name=validated_data.get('name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()


class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['name', 'first_name', 'last_name', 'email']


class UserMeSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'first_name', 'last_name', 'email', 'phone_number', 'images']

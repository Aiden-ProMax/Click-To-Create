from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
import secrets
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


def _generate_placeholder_password(length: int = 32) -> str:
    token = secrets.token_urlsafe(length)
    if len(token) < length:
        token = secrets.token_urlsafe(length + 8)
    return token


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
            )
            UserProfile.objects.create(
                user=user,
                radicale_username=validated_data['username'],
                radicale_password=_generate_placeholder_password(32),
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username_or_email, password=password)
        if not user and username_or_email:
            user_obj = User.objects.filter(email=username_or_email).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        attrs['user'] = user
        return attrs

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {'id': user.id, 'username': user.username, 'email': user.email},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        return Response({'detail': 'ok'})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'ok'})


class CsrfView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({'csrfToken': token})


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({'id': user.id, 'username': user.username, 'email': user.email})


class CheckUsernameView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth.models import User
        username = request.data.get('username', '').strip()
        
        if not username:
            return Response(
                {'exists': False, 'error': 'Username is required'},
                status=status.HTTP_200_OK
            )
        
        exists = User.objects.filter(username=username).exists()
        return Response(
            {'exists': exists, 'username': username},
            status=status.HTTP_200_OK
        )


class CheckEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth.models import User
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response(
                {'exists': False, 'error': 'Email is required'},
                status=status.HTTP_200_OK
            )
        
        exists = User.objects.filter(email__iexact=email).exists()
        return Response(
            {'exists': exists, 'email': email},
            status=status.HTTP_200_OK
        )

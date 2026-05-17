from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DeviceToken, Notification, AppConfig
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    UserSerializer,
    DeviceTokenSerializer,
    NotificationSerializer,
    AppConfigSerializer,
)


def health_check(request):
    return JsonResponse({'status': _('ok')})


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp'

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': _('OTP kod yuborildi.')}, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp'

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response({
            'user': UserSerializer(data['user'], context={'request': request}).data,
            'created': data['created'],
            'access': data['access'],
            'refresh': data['refresh'],
        })


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeviceTokenView(generics.CreateAPIView):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        token = serializer.validated_data['token']
        DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': self.request.user,
                'platform': serializer.validated_data.get('platform', 'ios'),
                'device_id': serializer.validated_data.get('device_id', ''),
                'device_name': serializer.validated_data.get('device_name', ''),
                'app_version': serializer.validated_data.get('app_version', ''),
                'is_active': True,
            },
        )


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        qs = Notification.objects.filter(user=request.user)
        if pk:
            qs = qs.filter(pk=pk)
        updated = qs.filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})


class AppConfigView(generics.RetrieveAPIView):
    serializer_class = AppConfigSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return AppConfig.get_solo()

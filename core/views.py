from django.http import JsonResponse
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, AppConfig
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    LogoutSerializer,
    UserSerializer,
    DeviceTokenSerializer,
    NotificationSerializer,
    AppConfigSerializer,
)


def health_check(request):
    return JsonResponse({'status': _('ok')})


class SendOTPView(generics.GenericAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp'

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': _('OTP kod yuborildi.')}, status=status.HTTP_201_CREATED)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
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


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceTokenView(generics.CreateAPIView):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.for_user(self.request.user)


notification_mark_read_response = inline_serializer(
    name='NotificationMarkReadResponse',
    fields={'updated': serializers.IntegerField()},
)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def mark_read(self, request, pk=None):
        qs = Notification.objects.for_user(request.user)
        if pk:
            qs = qs.filter(pk=pk)
        updated = qs.filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})

    @extend_schema(
        operation_id='notifications_mark_read',
        request=None,
        responses=notification_mark_read_response,
    )
    def post(self, request, pk):
        return self.mark_read(request, pk)


class NotificationMarkAllReadView(NotificationMarkReadView):
    @extend_schema(
        operation_id='notifications_mark_all_read',
        request=None,
        responses=notification_mark_read_response,
    )
    def post(self, request):
        return self.mark_read(request)


class AppConfigView(generics.RetrieveAPIView):
    serializer_class = AppConfigSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        # get_solo() would INSERT a row on an anonymous GET.
        return AppConfig.load()

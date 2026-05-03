from django.urls import path

from .views import (
    SendOTPView,
    VerifyOTPView,
    MeView,
    DeviceTokenView,
    NotificationListView,
    NotificationMarkReadView,
    AppConfigView,
)

urlpatterns = [
    path('auth/otp/send/', SendOTPView.as_view(), name='otp-send'),
    path('auth/otp/verify/', VerifyOTPView.as_view(), name='otp-verify'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('devices/token/', DeviceTokenView.as_view(), name='device-token'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', NotificationMarkReadView.as_view(), name='notification-read-all'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('config/', AppConfigView.as_view(), name='app-config'),
]

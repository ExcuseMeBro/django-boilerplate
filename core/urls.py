from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    SendOTPView,
    VerifyOTPView,
    LogoutView,
    MeView,
    DeviceTokenView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    AppConfigView,
)

urlpatterns = [
    path('auth/otp/send/', SendOTPView.as_view(), name='otp-send'),
    path('auth/otp/verify/', VerifyOTPView.as_view(), name='otp-verify'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('devices/token/', DeviceTokenView.as_view(), name='device-token'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', NotificationMarkAllReadView.as_view(), name='notification-read-all'),
    path('notifications/<uuid:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('config/', AppConfigView.as_view(), name='app-config'),
]

"""Versioned API URL configuration used for OpenAPI generation."""

from django.urls import include, path


def filter_api_v1_endpoints(endpoints):
    """Keep legacy unversioned aliases out of the public OpenAPI contract."""
    return [endpoint for endpoint in endpoints if endpoint[0].startswith('/api/v1/')]


urlpatterns = [
    path('api/v1/', include('core.urls')),
    path('api/v1/', include('messaging.urls')),
]

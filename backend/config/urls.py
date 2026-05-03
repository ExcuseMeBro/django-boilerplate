"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from core.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/v1/', include('core.urls')),
    path('api/v1/', include('messaging.urls')),
    path('api/', include('core.urls')),
    path('api/', include('messaging.urls')),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

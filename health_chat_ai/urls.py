from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Initialize URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Core app URLs
]

# Add API URLs
from core.api.v1 import api as api_v1
urlpatterns += [
    path('api/v1/', api_v1.urls),  # API v1 endpoints
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
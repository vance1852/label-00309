"""URL configuration for disk inspection project."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/servers/', include('apps.servers.urls')),
    path('api/inspections/', include('apps.inspections.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/schedule/', include('apps.schedules.urls')),
]

"""Alert URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('recipients', views.AlertRecipientViewSet, basename='recipient')

urlpatterns = [
    path('config/', views.AlertConfigView.as_view(), name='alert-config'),
    path('test/', views.TestEmailView.as_view(), name='test-email'),
    path('', include(router.urls)),
]

"""Schedule URLs."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ScheduleView.as_view(), name='schedule'),
    path('run-now/', views.RunNowView.as_view(), name='run-now'),
]

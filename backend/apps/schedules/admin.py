"""Schedule admin."""
from django.contrib import admin
from .models import InspectionSchedule


@admin.register(InspectionSchedule)
class InspectionScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'interval_type', 'execute_time', 'is_active', 'last_run', 'next_run']
    list_filter = ['is_active', 'interval_type']

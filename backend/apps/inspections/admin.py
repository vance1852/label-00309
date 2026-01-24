"""Inspection admin."""
from django.contrib import admin
from .models import InspectionRecord


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['server', 'status', 'has_alert', 'inspection_time', 'is_scheduled']
    list_filter = ['status', 'has_alert', 'is_scheduled']
    search_fields = ['server__name', 'server__ip_address']
    readonly_fields = ['inspection_time']

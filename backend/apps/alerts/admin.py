"""Alert admin."""
from django.contrib import admin
from .models import AlertConfig, AlertRecipient


@admin.register(AlertConfig)
class AlertConfigAdmin(admin.ModelAdmin):
    list_display = ['smtp_server', 'sender_email', 'disk_threshold', 'is_active', 'updated_at']


@admin.register(AlertRecipient)
class AlertRecipientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active']

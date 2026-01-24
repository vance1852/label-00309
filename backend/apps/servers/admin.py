"""Server admin."""
from django.contrib import admin
from .models import Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'port', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'ip_address']

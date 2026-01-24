"""Inspection serializers."""
from rest_framework import serializers
from .models import InspectionRecord


class InspectionRecordSerializer(serializers.ModelSerializer):
    """Inspection record serializer."""
    server_name = serializers.CharField(source='server.name', read_only=True)
    server_ip = serializers.CharField(source='server.ip_address', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InspectionRecord
        fields = [
            'id', 'server', 'server_name', 'server_ip',
            'executed_by', 'executed_by_name', 'command',
            'raw_output', 'parsed_result', 'status', 'status_display',
            'has_alert', 'alert_message', 'inspection_time', 'is_scheduled'
        ]
        read_only_fields = ['id', 'inspection_time']


class InspectionExecuteSerializer(serializers.Serializer):
    """Serializer for executing inspection."""
    server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )
    command = serializers.CharField(required=False, default='df -h')

    def validate_server_ids(self, value):
        if not value:
            raise serializers.ValidationError('请选择至少一台服务器')
        return value

"""Schedule serializers."""
from rest_framework import serializers
from .models import InspectionSchedule


class InspectionScheduleSerializer(serializers.ModelSerializer):
    """Inspection schedule serializer."""
    interval_type_display = serializers.CharField(source='get_interval_type_display', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = InspectionSchedule
        fields = [
            'id', 'name', 'interval_type', 'interval_type_display',
            'interval_value', 'execute_time', 'execute_day',
            'inspection_command', 'is_active', 'last_run', 'next_run',
            'created_at', 'updated_at', 'updated_by_name'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']

    def validate_interval_value(self, value):
        if value < 1:
            raise serializers.ValidationError('周期值必须大于0')
        return value

    def validate_execute_day(self, value):
        if value < 1 or value > 31:
            raise serializers.ValidationError('执行日必须在1-31之间')
        return value

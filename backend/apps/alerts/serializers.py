"""Alert serializers."""
from rest_framework import serializers
from .models import AlertConfig, AlertRecipient


class AlertRecipientSerializer(serializers.ModelSerializer):
    """Alert recipient serializer."""
    class Meta:
        model = AlertRecipient
        fields = ['id', 'name', 'email', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AlertConfigSerializer(serializers.ModelSerializer):
    """Alert config serializer."""
    smtp_password = serializers.CharField(write_only=True, required=False)
    recipients = AlertRecipientSerializer(many=True, read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = AlertConfig
        fields = [
            'id', 'smtp_server', 'smtp_port', 'smtp_username',
            'smtp_password', 'sender_email', 'sender_name',
            'use_tls', 'use_ssl', 'disk_threshold', 'is_active',
            'recipients', 'updated_at', 'updated_by_name'
        ]
        read_only_fields = ['id', 'updated_at']

    def validate_smtp_port(self, value):
        if value < 1 or value > 65535:
            raise serializers.ValidationError('端口号必须在1-65535之间')
        return value

    def validate_disk_threshold(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError('阈值必须在1-100之间')
        return value

    def create(self, validated_data):
        password = validated_data.pop('smtp_password', None)
        config = AlertConfig(**validated_data)
        if password:
            config.set_password(password)
        config.save()
        return config

    def update(self, instance, validated_data):
        password = validated_data.pop('smtp_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TestEmailSerializer(serializers.Serializer):
    """Test email serializer."""
    recipient_email = serializers.EmailField(required=True)

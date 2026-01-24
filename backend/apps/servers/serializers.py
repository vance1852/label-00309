"""Server serializers."""
from rest_framework import serializers
from .models import Server


class ServerSerializer(serializers.ModelSerializer):
    """Server serializer."""
    ssh_password = serializers.CharField(write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'ip_address', 'port', 'ssh_username',
            'ssh_password', 'description', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_ip_address(self, value):
        """Validate IP address."""
        if not value:
            raise serializers.ValidationError('IP地址不能为空')
        return value

    def validate_port(self, value):
        """Validate port number."""
        if value < 1 or value > 65535:
            raise serializers.ValidationError('端口号必须在1-65535之间')
        return value

    def create(self, validated_data):
        password = validated_data.pop('ssh_password', None)
        server = Server(**validated_data)
        if password:
            server.set_password(password)
        server.save()
        return server

    def update(self, instance, validated_data):
        password = validated_data.pop('ssh_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ServerListSerializer(serializers.ModelSerializer):
    """Server list serializer (without sensitive data)."""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'ip_address', 'port', 'ssh_username',
            'description', 'is_active', 'created_by_name', 'created_at'
        ]

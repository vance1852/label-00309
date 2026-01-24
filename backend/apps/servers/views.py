"""Server views."""
import logging
import paramiko
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.core.response import success_response, error_response
from apps.core.pagination import StandardPagination
from .models import Server
from .serializers import ServerSerializer, ServerListSerializer

logger = logging.getLogger(__name__)


class ServerViewSet(viewsets.ModelViewSet):
    """Server viewset for CRUD operations."""
    queryset = Server.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filterset_fields = ['is_active']
    search_fields = ['name', 'ip_address', 'description']
    ordering_fields = ['created_at', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ServerListSerializer
        return ServerSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        serializer.save(created_by=request.user)
        logger.info(f"User {request.user.username} created server: {serializer.data['name']}")
        return success_response(data=serializer.data, message='服务器添加成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        serializer.save()
        logger.info(f"User {request.user.username} updated server: {instance.name}")
        return success_response(data=serializer.data, message='服务器更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        server_name = instance.name
        instance.delete()
        logger.info(f"User {request.user.username} deleted server: {server_name}")
        return success_response(message='服务器删除成功')

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test SSH connection to server."""
        server = self.get_object()
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server.ip_address,
                port=server.port,
                username=server.ssh_username,
                password=server.get_password(),
                timeout=10
            )
            client.close()
            logger.info(f"SSH connection test successful for server: {server.name}")
            return success_response(message='SSH连接测试成功')
        except paramiko.AuthenticationException:
            return error_response(message='SSH认证失败，请检查用户名和密码')
        except paramiko.SSHException as e:
            return error_response(message=f'SSH连接错误: {str(e)}')
        except Exception as e:
            return error_response(message=f'连接失败: {str(e)}')

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active servers."""
        servers = Server.objects.filter(is_active=True)
        serializer = ServerListSerializer(servers, many=True)
        return success_response(data=serializer.data)

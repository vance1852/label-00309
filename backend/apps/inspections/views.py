"""Inspection views."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.core.response import success_response, error_response
from apps.core.pagination import StandardPagination
from apps.servers.models import Server
from .models import InspectionRecord
from .serializers import InspectionRecordSerializer, InspectionExecuteSerializer
from .services import InspectionService

logger = logging.getLogger(__name__)


class InspectionViewSet(viewsets.ModelViewSet):
    """Inspection viewset."""
    queryset = InspectionRecord.objects.select_related('server', 'executed_by')
    serializer_class = InspectionRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['server', 'status', 'has_alert', 'is_scheduled']
    search_fields = ['server__name', 'server__ip_address']
    ordering_fields = ['inspection_time', 'status']

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        logger.info(f"User {request.user.username} deleted inspection record: {instance.id}")
        return success_response(message='巡检记录删除成功')

    @action(detail=False, methods=['post'])
    def execute(self, request):
        """Execute inspection on selected servers."""
        serializer = InspectionExecuteSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])

        server_ids = serializer.validated_data['server_ids']
        command = serializer.validated_data.get('command', 'df -h')

        servers = Server.objects.filter(id__in=server_ids, is_active=True)
        if not servers.exists():
            return error_response(message='未找到有效的服务器')

        service = InspectionService()
        results = []
        for server in servers:
            try:
                record = service.execute_inspection(server, command, request.user)
                results.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'status': record.status,
                    'has_alert': record.has_alert,
                    'record_id': record.id
                })
            except Exception as e:
                logger.error(f"Inspection failed for server {server.name}: {str(e)}")
                results.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'status': 'failed',
                    'error': str(e)
                })

        logger.info(f"User {request.user.username} executed inspection on {len(servers)} servers")
        return success_response(data=results, message='巡检执行完成')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get inspection statistics."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        total = InspectionRecord.objects.count()
        today_count = InspectionRecord.objects.filter(
            inspection_time__date=today
        ).count()
        alert_count = InspectionRecord.objects.filter(has_alert=True).count()
        
        status_stats = InspectionRecord.objects.values('status').annotate(
            count=Count('id')
        )

        return success_response(data={
            'total': total,
            'today': today_count,
            'alerts': alert_count,
            'status_stats': list(status_stats)
        })

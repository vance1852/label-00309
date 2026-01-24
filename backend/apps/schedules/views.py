"""Schedule views."""
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.response import success_response, error_response
from apps.servers.models import Server
from apps.inspections.services import InspectionService
from .models import InspectionSchedule
from .serializers import InspectionScheduleSerializer

logger = logging.getLogger(__name__)


class ScheduleView(APIView):
    """Schedule configuration view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get schedule configuration."""
        schedule = InspectionSchedule.objects.first()
        if not schedule:
            # Create default schedule
            schedule = InspectionSchedule.objects.create()
        serializer = InspectionScheduleSerializer(schedule)
        return success_response(data=serializer.data)

    def put(self, request):
        """Update schedule configuration."""
        schedule = InspectionSchedule.objects.first()
        if not schedule:
            schedule = InspectionSchedule.objects.create()
        
        serializer = InspectionScheduleSerializer(schedule, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        serializer.save(updated_by=request.user)
        logger.info(f"User {request.user.username} updated schedule configuration")
        return success_response(data=serializer.data, message='调度配置更新成功')


class RunNowView(APIView):
    """Run inspection now view."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Execute inspection immediately on all active servers."""
        servers = Server.objects.filter(is_active=True)
        if not servers.exists():
            return error_response(message='没有可用的服务器')

        schedule = InspectionSchedule.objects.first()
        command = schedule.inspection_command if schedule else 'df -h'

        service = InspectionService()
        results = []
        success_count = 0
        fail_count = 0

        for server in servers:
            try:
                record = service.execute_inspection(server, command, request.user, is_scheduled=True)
                results.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'status': record.status,
                    'has_alert': record.has_alert
                })
                if record.status != 'failed':
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                fail_count += 1
                results.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'status': 'failed',
                    'error': str(e)
                })

        logger.info(f"User {request.user.username} executed manual inspection: {success_count} success, {fail_count} failed")
        return success_response(
            data={'results': results, 'success': success_count, 'failed': fail_count},
            message=f'巡检完成: 成功 {success_count}, 失败 {fail_count}'
        )

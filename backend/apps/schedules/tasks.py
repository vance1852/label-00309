"""Celery tasks for scheduled inspections."""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def run_scheduled_inspection():
    """Run scheduled inspection on all active servers."""
    from apps.servers.models import Server
    from apps.inspections.services import InspectionService
    from .models import InspectionSchedule

    schedule = InspectionSchedule.objects.filter(is_active=True).first()
    if not schedule:
        logger.info("No active schedule found, skipping inspection")
        return

    servers = Server.objects.filter(is_active=True)
    if not servers.exists():
        logger.info("No active servers found, skipping inspection")
        return

    command = schedule.inspection_command
    service = InspectionService()
    
    success_count = 0
    fail_count = 0

    for server in servers:
        try:
            record = service.execute_inspection(server, command, None, is_scheduled=True)
            if record.status != 'failed':
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Scheduled inspection failed for {server.name}: {str(e)}")
            fail_count += 1

    # Update last run time
    schedule.last_run = timezone.now()
    schedule.save()

    logger.info(f"Scheduled inspection completed: {success_count} success, {fail_count} failed")
    return {'success': success_count, 'failed': fail_count}

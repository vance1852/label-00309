"""Inspection services."""
import logging
import re
import paramiko
from .models import InspectionRecord
from apps.alerts.services import AlertService

logger = logging.getLogger(__name__)


class InspectionService:
    """Service for executing server inspections."""

    def __init__(self):
        self.alert_service = AlertService()

    def execute_inspection(self, server, command, user=None, is_scheduled=False):
        """Execute inspection on a server."""
        logger.info(f"Starting inspection on server: {server.name}")
        
        try:
            # Connect via SSH
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server.ip_address,
                port=server.port,
                username=server.ssh_username,
                password=server.get_password(),
                timeout=30
            )

            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=60)
            raw_output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            client.close()

            if error_output and not raw_output:
                raise Exception(error_output)

            # Parse result
            parsed_result = self.parse_disk_output(raw_output)
            
            # Check for alerts
            has_alert, alert_message = self.check_alerts(parsed_result)
            
            # Determine status
            if has_alert:
                status = 'warning'
            else:
                status = 'success'

            # Create record
            record = InspectionRecord.objects.create(
                server=server,
                executed_by=user,
                command=command,
                raw_output=raw_output,
                parsed_result=parsed_result,
                status=status,
                has_alert=has_alert,
                alert_message=alert_message,
                is_scheduled=is_scheduled
            )

            # Send alert if needed
            if has_alert:
                self.alert_service.send_alert(server, record, alert_message)

            logger.info(f"Inspection completed for server: {server.name}, status: {status}")
            return record

        except Exception as e:
            logger.error(f"Inspection failed for server {server.name}: {str(e)}")
            record = InspectionRecord.objects.create(
                server=server,
                executed_by=user,
                command=command,
                raw_output=str(e),
                parsed_result={},
                status='failed',
                has_alert=True,
                alert_message=f'巡检执行失败: {str(e)}',
                is_scheduled=is_scheduled
            )
            return record

    def parse_disk_output(self, output):
        """Parse df -h output."""
        result = {
            'disks': [],
            'total_size': 0,
            'total_used': 0,
            'total_available': 0
        }

        lines = output.strip().split('\n')
        if len(lines) < 2:
            return result

        for line in lines[1:]:
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 6:
                try:
                    filesystem = parts[0]
                    size = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4].replace('%', '')
                    mount_point = parts[5]

                    # Skip special filesystems
                    if filesystem.startswith('tmpfs') or filesystem.startswith('devtmpfs'):
                        continue

                    disk_info = {
                        'filesystem': filesystem,
                        'size': size,
                        'used': used,
                        'available': available,
                        'use_percent': int(use_percent) if use_percent.isdigit() else 0,
                        'mount_point': mount_point
                    }
                    result['disks'].append(disk_info)
                except (ValueError, IndexError):
                    continue

        return result

    def check_alerts(self, parsed_result):
        """Check if any disk exceeds threshold."""
        from apps.alerts.models import AlertConfig
        
        try:
            config = AlertConfig.objects.filter(is_active=True).first()
            threshold = config.disk_threshold if config else 80
        except:
            threshold = 80

        alert_disks = []
        for disk in parsed_result.get('disks', []):
            if disk['use_percent'] >= threshold:
                alert_disks.append(
                    f"{disk['mount_point']}: {disk['use_percent']}%"
                )

        if alert_disks:
            message = f"磁盘使用率超过阈值({threshold}%): " + ", ".join(alert_disks)
            return True, message
        
        return False, None

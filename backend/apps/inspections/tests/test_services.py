import pytest
from unittest.mock import patch, MagicMock
from ..services import InspectionService
from ..models import InspectionRecord
from apps.alerts.models import AlertConfig

pytestmark = pytest.mark.django_db

class TestInspectionService:
    def test_parse_disk_output_basic(self):
        service = InspectionService()
        df_output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
tmpfs           16G     0   16G   0% /dev/shm"""
        
        result = service.parse_disk_output(df_output)
        
        assert len(result['disks']) == 1
        assert result['disks'][0]['filesystem'] == '/dev/sda1'
        assert result['disks'][0]['use_percent'] == 50
        assert result['disks'][0]['mount_point'] == '/'

    def test_parse_disk_output_empty(self):
        service = InspectionService()
        result = service.parse_disk_output('')
        assert len(result['disks']) == 0

    def test_parse_disk_output_invalid_format(self):
        service = InspectionService()
        result = service.parse_disk_output('Header only')
        assert len(result['disks']) == 0

    def test_check_alerts_below_threshold(self):
        service = InspectionService()
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 50}
            ]
        }
        
        has_alert, message = service.check_alerts(parsed_result)
        assert has_alert is False
        assert message is None

    def test_check_alerts_above_threshold(self, alert_config):
        alert_config.disk_threshold = 80
        alert_config.save()
        
        service = InspectionService()
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 85}
            ]
        }
        
        has_alert, message = service.check_alerts(parsed_result)
        assert has_alert is True
        assert '85%' in message
        assert '/' in message

    def test_check_alerts_multiple_disks(self, alert_config):
        alert_config.disk_threshold = 70
        alert_config.save()
        
        service = InspectionService()
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 75},
                {'mount_point': '/data', 'use_percent': 80},
                {'mount_point': '/tmp', 'use_percent': 50}
            ]
        }
        
        has_alert, message = service.check_alerts(parsed_result)
        assert has_alert is True
        assert '/' in message
        assert '/data' in message
        assert '/tmp' not in message

    def test_check_alerts_no_config(self):
        AlertConfig.objects.all().delete()
        
        service = InspectionService()
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 85}
            ]
        }
        
        has_alert, message = service.check_alerts(parsed_result)
        assert has_alert is True

    def test_execute_inspection_success(self, server, user, mock_ssh_client, alert_config, alert_recipient):
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   30G   70G  30% /"""
        stderr.read.return_value = b""
        
        service = InspectionService()
        record = service.execute_inspection(server, 'df -h', user=user)
        
        assert record is not None
        assert record.status == 'success'
        assert record.has_alert is False
        assert len(record.parsed_result['disks']) == 1
        mock_ssh_client.return_value.connect.assert_called_once()

    def test_execute_inspection_with_alert(self, server, user, mock_ssh_client, alert_config, alert_recipient, mock_smtp):
        alert_config.disk_threshold = 20
        alert_config.save()
        
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   30G   70G  30% /"""
        stderr.read.return_value = b""
        
        service = InspectionService()
        record = service.execute_inspection(server, 'df -h', user=user)
        
        assert record.status == 'warning'
        assert record.has_alert is True
        assert record.alert_message is not None

    def test_execute_inspection_ssh_exception(self, server, user, mock_ssh_client):
        mock_ssh_client.return_value.connect.side_effect = Exception('Connection refused')
        
        service = InspectionService()
        record = service.execute_inspection(server, 'df -h', user=user)
        
        assert record is not None
        assert record.status == 'failed'
        assert record.has_alert is True
        assert 'Connection refused' in record.raw_output
        assert '巡检执行失败' in record.alert_message

    def test_execute_inspection_command_error(self, server, user, mock_ssh_client):
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b""
        stderr.read.return_value = b"bash: df: command not found"
        
        service = InspectionService()
        record = service.execute_inspection(server, 'df -h', user=user)
        
        assert record.status == 'failed'
        assert record.has_alert is True

    def test_inspection_record_creation(self, server, user):
        record = InspectionRecord.objects.create(
            server=server,
            executed_by=user,
            command='df -h',
            raw_output='test output',
            parsed_result={'disks': []},
            status='success',
            has_alert=False
        )
        assert str(record).startswith(server.name)
        assert record.is_scheduled is False

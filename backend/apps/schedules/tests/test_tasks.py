"""Tests for schedule tasks."""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.schedules.tasks import run_scheduled_inspection


class TestRunScheduledInspectionTask:
    """Tests for run_scheduled_inspection task."""

    def test_no_active_schedule(self, db):
        """Test when no active schedule exists."""
        result = run_scheduled_inspection()
        assert result is None

    def test_no_active_servers(self, db, inspection_schedule):
        """Test when no active servers exist."""
        result = run_scheduled_inspection()
        assert result is None

    def test_successful_inspection(self, db, server, inspection_schedule, mock_ssh_client):
        """Test successful scheduled inspection."""
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""/dev/sda1       200G   50G  150G  25% /
/dev/sdb1       500G  100G  400G  20% /data"""

        with patch('apps.alerts.services.AlertService') as mock_alert_service:
            mock_alert_service.return_value.send_alert.return_value = None
            result = run_scheduled_inspection()

        assert result == {'success': 1, 'failed': 0}
        inspection_schedule.refresh_from_db()
        assert inspection_schedule.last_run is not None

    def test_inspection_with_failed_server(self, db, server, inspection_schedule, mock_ssh_auth_failure):
        """Test scheduled inspection with server connection failure."""
        result = run_scheduled_inspection()

        assert result == {'success': 0, 'failed': 1}
        inspection_schedule.refresh_from_db()
        assert inspection_schedule.last_run is not None

    def test_multiple_servers_mixed_results(self, db, user, inspection_schedule, mock_ssh_client):
        """Test multiple servers with mixed success and failure."""
        from apps.servers.models import Server
        
        server1 = Server.objects.create(
            name='Server 1',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=user
        )
        server1.set_password('pass')
        server1.save()

        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=user
        )
        server2.set_password('pass')
        server2.save()

        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""/dev/sda1       200G   50G  150G  25% /"""

        with patch('apps.alerts.services.AlertService'):
            result = run_scheduled_inspection()

        assert result == {'success': 2, 'failed': 0}

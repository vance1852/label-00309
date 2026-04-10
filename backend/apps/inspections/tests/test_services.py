"""Tests for inspection services."""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.servers.models import Server
from apps.inspections.models import InspectionRecord
from apps.inspections.services import InspectionService
from apps.alerts.models import AlertConfig, AlertRecipient


User = get_user_model()


class InspectionServiceTests(TestCase):
    """Test cases for InspectionService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        self.server.set_password('test_password')
        self.server.save()
        self.service = InspectionService()

    @patch('apps.inspections.services.paramiko.SSHClient')
    @patch('apps.inspections.services.AlertService.send_alert')
    def test_execute_inspection_success(self, mock_send_alert, mock_ssh_client):
        """Test successful inspection execution."""
        # Mock SSH client
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'Filesystem  Size  Used Avail Use% Mounted on\n/dev/sda1   100G   50G   50G  50% /'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', self.user)
        
        self.assertIsNotNone(record)
        self.assertEqual(record.server, self.server)
        self.assertEqual(record.command, 'df -h')
        self.assertEqual(record.status, 'success')
        self.assertFalse(record.has_alert)
        mock_send_alert.assert_not_called()

    @patch('apps.inspections.services.paramiko.SSHClient')
    @patch('apps.inspections.services.AlertService.send_alert')
    def test_execute_inspection_with_alert(self, mock_send_alert, mock_ssh_client):
        """Test inspection execution that triggers alert."""
        # Create alert config
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_port=587,
            smtp_username='test@test.com',
            sender_email='test@test.com',
            sender_name='Test',
            disk_threshold=80
        )
        config.set_password('password')
        config.save()
        
        # Mock SSH client with high disk usage
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'Filesystem  Size  Used Avail Use% Mounted on\n/dev/sda1   100G   90G   10G  90% /'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', self.user)
        
        self.assertEqual(record.status, 'warning')
        self.assertTrue(record.has_alert)
        self.assertIsNotNone(record.alert_message)
        mock_send_alert.assert_called_once()

    @patch('apps.inspections.services.paramiko.SSHClient')
    def test_execute_inspection_ssh_error(self, mock_ssh_client):
        """Test inspection execution with SSH error."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception('Connection refused')
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', self.user)
        
        self.assertEqual(record.status, 'failed')
        self.assertTrue(record.has_alert)
        self.assertIn('Connection refused', record.alert_message)

    @patch('apps.inspections.services.paramiko.SSHClient')
    def test_execute_inspection_command_error(self, mock_ssh_client):
        """Test inspection execution with command error."""
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b''
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b'Command not found'
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'invalid_cmd', self.user)
        
        self.assertEqual(record.status, 'failed')
        self.assertTrue(record.has_alert)

    @patch('apps.inspections.services.paramiko.SSHClient')
    def test_execute_inspection_scheduled(self, mock_ssh_client):
        """Test scheduled inspection execution."""
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'Filesystem  Size  Used Avail Use% Mounted on\n/dev/sda1   100G   50G   50G  50% /'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', None, is_scheduled=True)
        
        self.assertTrue(record.is_scheduled)
        self.assertIsNone(record.executed_by)

    def test_parse_disk_output_normal(self):
        """Test parsing normal df -h output."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
/dev/sdb1       200G  100G  100G  50% /data"""
        
        result = self.service.parse_disk_output(output)
        
        self.assertEqual(len(result['disks']), 2)
        self.assertEqual(result['disks'][0]['filesystem'], '/dev/sda1')
        self.assertEqual(result['disks'][0]['use_percent'], 50)
        self.assertEqual(result['disks'][0]['mount_point'], '/')

    def test_parse_disk_output_with_tmpfs(self):
        """Test parsing df output that includes tmpfs."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
tmpfs           391M  1.6M  390M   1% /run
/dev/sda1       100G   50G   50G  50% /"""
        
        result = self.service.parse_disk_output(output)
        
        # tmpfs should be skipped
        self.assertEqual(len(result['disks']), 1)
        self.assertEqual(result['disks'][0]['filesystem'], '/dev/sda1')

    def test_parse_disk_output_with_devtmpfs(self):
        """Test parsing df output that includes devtmpfs."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
devtmpfs        1.9G     0  1.9G   0% /dev
/dev/sda1       100G   50G   50G  50% /"""
        
        result = self.service.parse_disk_output(output)
        
        # devtmpfs should be skipped
        self.assertEqual(len(result['disks']), 1)
        self.assertEqual(result['disks'][0]['filesystem'], '/dev/sda1')

    def test_parse_disk_output_empty(self):
        """Test parsing empty output."""
        result = self.service.parse_disk_output('')
        self.assertEqual(result['disks'], [])

    def test_parse_disk_output_header_only(self):
        """Test parsing output with only header."""
        output = "Filesystem      Size  Used Avail Use% Mounted on"
        result = self.service.parse_disk_output(output)
        self.assertEqual(result['disks'], [])

    def test_parse_disk_output_invalid_lines(self):
        """Test parsing output with invalid lines."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
invalid line without enough parts
/dev/sdb1       200G  100G  100G  50% /data"""
        
        result = self.service.parse_disk_output(output)
        self.assertEqual(len(result['disks']), 2)

    def test_parse_disk_output_non_numeric_percentage(self):
        """Test parsing output with non-numeric percentage."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G   -  /"""
        
        result = self.service.parse_disk_output(output)
        self.assertEqual(len(result['disks']), 1)
        self.assertEqual(result['disks'][0]['use_percent'], 0)

    def test_check_alerts_no_threshold_exceeded(self):
        """Test alert check when no threshold is exceeded."""
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 50},
                {'mount_point': '/data', 'use_percent': 70}
            ]
        }
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        self.assertFalse(has_alert)
        self.assertIsNone(message)

    def test_check_alerts_threshold_exceeded(self):
        """Test alert check when threshold is exceeded."""
        # Create alert config with 80% threshold
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_port=587,
            smtp_username='test@test.com',
            sender_email='test@test.com',
            sender_name='Test',
            disk_threshold=80
        )
        config.set_password('password')
        config.save()
        
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 85},
                {'mount_point': '/data', 'use_percent': 90}
            ]
        }
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        self.assertTrue(has_alert)
        self.assertIn('磁盘使用率超过阈值', message)
        self.assertIn('/: 85%', message)
        self.assertIn('/data: 90%', message)

    def test_check_alerts_at_threshold(self):
        """Test alert check when usage equals threshold."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_port=587,
            smtp_username='test@test.com',
            sender_email='test@test.com',
            sender_name='Test',
            disk_threshold=80
        )
        config.set_password('password')
        config.save()
        
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 80}
            ]
        }
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        self.assertTrue(has_alert)
        self.assertIn('80%', message)

    def test_check_alerts_no_disks(self):
        """Test alert check with no disks."""
        parsed_result = {'disks': []}
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        self.assertFalse(has_alert)
        self.assertIsNone(message)

    def test_check_alerts_no_config(self):
        """Test alert check with no alert config uses default threshold."""
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 85}
            ]
        }
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        # Should use default threshold of 80
        self.assertTrue(has_alert)
        self.assertIn('80%', message)

    def test_check_alerts_inactive_config(self):
        """Test alert check with inactive config."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_port=587,
            smtp_username='test@test.com',
            sender_email='test@test.com',
            sender_name='Test',
            disk_threshold=70,
            is_active=False
        )
        config.set_password('password')
        config.save()
        
        parsed_result = {
            'disks': [
                {'mount_point': '/', 'use_percent': 85}
            ]
        }
        
        has_alert, message = self.service.check_alerts(parsed_result)
        
        # Should use default threshold since config is inactive
        self.assertTrue(has_alert)
        self.assertIn('80%', message)

    @patch('apps.inspections.services.paramiko.SSHClient')
    def test_execute_inspection_with_connection_timeout(self, mock_ssh_client):
        """Test inspection with connection timeout."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = TimeoutError('Connection timed out')
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', self.user)
        
        self.assertEqual(record.status, 'failed')
        self.assertTrue(record.has_alert)
        self.assertIn('timed out', record.alert_message)

    @patch('apps.inspections.services.paramiko.SSHClient')
    def test_execute_inspection_with_authentication_error(self, mock_ssh_client):
        """Test inspection with authentication error."""
        from paramiko import AuthenticationException
        
        mock_client = MagicMock()
        mock_client.connect.side_effect = AuthenticationException('Auth failed')
        mock_ssh_client.return_value = mock_client
        
        record = self.service.execute_inspection(self.server, 'df -h', self.user)
        
        self.assertEqual(record.status, 'failed')
        self.assertTrue(record.has_alert)

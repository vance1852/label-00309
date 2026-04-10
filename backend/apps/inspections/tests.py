"""Tests for inspections app."""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import InspectionRecord
from apps.servers.models import Server
from apps.users.models import User
from .services import InspectionService
from .serializers import InspectionRecordSerializer


class InspectionServiceTests(TestCase):
    """Test InspectionService."""

    def setUp(self):
        """Set up test data."""
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root'
        )
        self.server.set_password('testpass')
        self.server.save()
        self.service = InspectionService()

    def test_parse_disk_output(self):
        """Test parsing disk output."""
        df_output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
/dev/sdb1       200G  180G   20G  90% /data"""
        result = self.service.parse_disk_output(df_output)
        self.assertEqual(len(result['disks']), 2)
        self.assertEqual(result['disks'][0]['filesystem'], '/dev/sda1')
        self.assertEqual(result['disks'][0]['use_percent'], 50)

    def test_parse_disk_output_empty(self):
        """Test parsing empty disk output."""
        result = self.service.parse_disk_output('')
        self.assertEqual(len(result['disks']), 0)

    def test_check_alerts_below_threshold(self):
        """Test checking alerts when usage is below threshold."""
        parsed_result = {
            'disks': [{'filesystem': '/dev/sda1', 'use_percent': 50, 'mount_point': '/'}]
        }
        has_alert, alert_message = self.service.check_alerts(parsed_result)
        self.assertFalse(has_alert)
        self.assertIsNone(alert_message)

    def test_check_alerts_above_threshold(self):
        """Test checking alerts when usage is above threshold."""
        parsed_result = {
            'disks': [
                {'filesystem': '/dev/sda1', 'use_percent': 95, 'mount_point': '/'},
                {'filesystem': '/dev/sdb1', 'use_percent': 75, 'mount_point': '/data'}
            ]
        }
        has_alert, alert_message = self.service.check_alerts(parsed_result)
        self.assertTrue(has_alert)
        self.assertIsNotNone(alert_message)

    @patch('paramiko.SSHClient')
    def test_execute_inspection_success(self, mock_ssh_class):
        """Test successful inspection execution."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (
            None,
            MagicMock(read=MagicMock(return_value=b'Filesystem Size Used Avail Use% Mounted on\n/dev/sda1 100G 50G 50G 50% /')),
            MagicMock(read=MagicMock(return_value=b''))
        )
        mock_instance.close.return_value = None
        user = User.objects.create_user(username='test', email='test@test.com', password='pass')
        record = self.service.execute_inspection(self.server, 'df -h', user=user)
        self.assertIsNotNone(record)
        self.assertEqual(record.status, 'success')

    @patch('paramiko.SSHClient')
    def test_execute_inspection_ssh_error(self, mock_ssh_class):
        """Test inspection with SSH error."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        from paramiko.ssh_exception import SSHException
        mock_instance.connect.side_effect = SSHException('Connection failed')
        user = User.objects.create_user(username='test', email='test@test.com', password='pass')
        record = self.service.execute_inspection(self.server, 'df -h', user=user)
        self.assertIsNotNone(record)
        self.assertEqual(record.status, 'failed')

    @patch('paramiko.SSHClient')
    def test_execute_inspection_command_error(self, mock_ssh_class):
        """Test inspection with command error."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (
            None,
            MagicMock(read=MagicMock(return_value=b'')),
            MagicMock(read=MagicMock(return_value=b'Command not found'))
        )
        mock_instance.close.return_value = None
        user = User.objects.create_user(username='test', email='test@test.com', password='pass')
        record = self.service.execute_inspection(self.server, 'df -h', user=user)
        self.assertIsNotNone(record)
        self.assertEqual(record.status, 'failed')


class InspectionViewSetTests(APITestCase):
    """Test Inspection ViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root'
        )
        self.server.set_password('testpass')
        self.server.save()
        self.record = InspectionRecord.objects.create(
            server=self.server,
            executed_by=self.user,
            command='df -h',
            status='success'
        )

    def test_inspection_list_authenticated(self):
        """Test inspection list with authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_inspection_list_unauthenticated(self):
        """Test inspection list without authentication."""
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inspection_detail(self):
        """Test getting inspection detail."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/inspections/{self.record.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    @patch('paramiko.SSHClient')
    def test_execute_inspection_success(self, mock_ssh_class):
        """Test executing inspection via API."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (
            None,
            MagicMock(read=MagicMock(return_value=b'Filesystem Size Used Avail Use% Mounted on\n/dev/sda1 100G 50G 50G 50% /')),
            MagicMock(read=MagicMock(return_value=b''))
        )
        self.client.force_authenticate(user=self.user)
        data = {'server_ids': [self.server.id], 'command': 'df -h'}
        response = self.client.post('/api/inspections/execute/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_execute_inspection_no_server(self):
        """Test executing inspection without server ID."""
        self.client.force_authenticate(user=self.user)
        data = {'command': 'df -h'}
        response = self.client.post('/api/inspections/execute/', data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_execute_inspection_invalid_server(self):
        """Test executing inspection with invalid server ID."""
        self.client.force_authenticate(user=self.user)
        data = {'server_ids': [9999], 'command': 'df -h'}
        response = self.client.post('/api/inspections/execute/', data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_inspection_statistics(self):
        """Test getting inspection statistics."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inspections/statistics/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_filter_by_status(self):
        """Test filtering inspections by status."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inspections/?status=success')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_inspection_delete(self):
        """Test deleting an inspection record."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/inspections/{self.record.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

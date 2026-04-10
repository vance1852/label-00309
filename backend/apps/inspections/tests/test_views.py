"""Tests for inspection views."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.servers.models import Server
from apps.inspections.models import InspectionRecord


User = get_user_model()


class InspectionViewSetTests(TestCase):
    """Test cases for InspectionViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        self.server.set_password('test_password')
        self.server.save()

    def test_list_inspections(self):
        """Test listing inspection records."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_list_inspections_unauthenticated(self):
        """Test listing inspections without authentication."""
        self.client.credentials()
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.status_code, 401)

    def test_retrieve_inspection(self):
        """Test retrieving a single inspection record."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test output',
            parsed_result={'disks': []},
            status='success'
        )
        
        response = self.client.get(f'/api/inspections/{record.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['command'], 'df -h')

    def test_retrieve_nonexistent_inspection(self):
        """Test retrieving non-existent inspection record."""
        response = self.client.get('/api/inspections/999/')
        self.assertEqual(response.status_code, 404)

    def test_delete_inspection(self):
        """Test deleting an inspection record."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        
        response = self.client.delete(f'/api/inspections/{record.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(InspectionRecord.objects.count(), 0)

    def test_delete_nonexistent_inspection(self):
        """Test deleting non-existent inspection record."""
        response = self.client.delete('/api/inspections/999/')
        self.assertEqual(response.status_code, 404)

    @patch('apps.inspections.views.InspectionService')
    def test_execute_inspection_success(self, mock_service_class):
        """Test executing inspection successfully."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        data = {
            'server_ids': [self.server.id],
            'command': 'df -h'
        }
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '巡检执行完成')

    @patch('apps.inspections.views.InspectionService')
    def test_execute_inspection_multiple_servers(self, mock_service_class):
        """Test executing inspection on multiple servers."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        data = {
            'server_ids': [self.server.id, server2.id],
            'command': 'df -h'
        }
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)

    def test_execute_inspection_no_valid_servers(self):
        """Test executing inspection with no valid servers."""
        data = {
            'server_ids': [999],  # Non-existent server
            'command': 'df -h'
        }
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('未找到有效的服务器', response.data['message'])

    def test_execute_inspection_inactive_servers(self):
        """Test executing inspection filters inactive servers."""
        inactive_server = Server.objects.create(
            name='Inactive Server',
            ip_address='192.168.1.102',
            port=22,
            ssh_username='root',
            is_active=False,
            created_by=self.user
        )
        
        data = {
            'server_ids': [inactive_server.id],
            'command': 'df -h'
        }
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_execute_inspection_missing_server_ids(self):
        """Test executing inspection without server_ids."""
        data = {'command': 'df -h'}
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_execute_inspection_empty_server_ids(self):
        """Test executing inspection with empty server_ids."""
        data = {'server_ids': [], 'command': 'df -h'}
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    @patch('apps.inspections.views.InspectionService')
    def test_execute_inspection_exception(self, mock_service_class):
        """Test executing inspection when exception occurs."""
        mock_service = MagicMock()
        mock_service.execute_inspection.side_effect = Exception('SSH Error')
        mock_service_class.return_value = mock_service
        
        data = {
            'server_ids': [self.server.id],
            'command': 'df -h'
        }
        response = self.client.post(
            '/api/inspections/execute/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        # Should still return success with error info in data
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data'][0]['status'], 'failed')
        self.assertIn('SSH Error', response.data['data'][0]['error'])

    def test_statistics_empty(self):
        """Test statistics endpoint with no records."""
        response = self.client.get('/api/inspections/statistics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['total'], 0)
        self.assertEqual(response.data['data']['today'], 0)
        self.assertEqual(response.data['data']['alerts'], 0)

    def test_statistics_with_records(self):
        """Test statistics endpoint with records."""
        from django.utils import timezone
        
        # Create records
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success',
            has_alert=False,
            inspection_time=timezone.now()
        )
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed',
            has_alert=True,
            inspection_time=timezone.now()
        )
        
        response = self.client.get('/api/inspections/statistics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['total'], 2)
        self.assertEqual(response.data['data']['today'], 2)
        self.assertEqual(response.data['data']['alerts'], 1)
        self.assertEqual(len(response.data['data']['status_stats']), 2)

    def test_filter_by_server(self):
        """Test filtering inspections by server."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        InspectionRecord.objects.create(
            server=server2,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        
        response = self.client.get(f'/api/inspections/?server={self.server.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_filter_by_status(self):
        """Test filtering inspections by status."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        
        response = self.client.get('/api/inspections/?status=success')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_filter_by_has_alert(self):
        """Test filtering inspections by has_alert."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success',
            has_alert=False
        )
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='warning',
            has_alert=True
        )
        
        response = self.client.get('/api/inspections/?has_alert=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_filter_by_is_scheduled(self):
        """Test filtering inspections by is_scheduled."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success',
            is_scheduled=False
        )
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success',
            is_scheduled=True
        )
        
        response = self.client.get('/api/inspections/?is_scheduled=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_search_inspections(self):
        """Test searching inspections."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        
        response = self.client.get('/api/inspections/?search=Test Server')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_order_inspections(self):
        """Test ordering inspections."""
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test1',
            parsed_result={},
            status='success'
        )
        InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test2',
            parsed_result={},
            status='failed'
        )
        
        response = self.client.get('/api/inspections/?ordering=status')
        self.assertEqual(response.status_code, 200)
        # Should have results ordered by status

    def test_pagination(self):
        """Test inspection list pagination."""
        for i in range(15):
            InspectionRecord.objects.create(
                server=self.server,
                command='df -h',
                raw_output=f'test{i}',
                parsed_result={},
                status='success'
            )
        
        response = self.client.get('/api/inspections/?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['list']), 10)
        self.assertEqual(response.data['data']['total'], 15)

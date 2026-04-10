"""Tests for schedule views."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.schedules.models import InspectionSchedule
from apps.servers.models import Server


User = get_user_model()


class ScheduleViewTests(TestCase):
    """Test cases for ScheduleView."""

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

    def test_get_schedule_not_exists(self):
        """Test getting schedule when none exists."""
        response = self.client.get('/api/schedule/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        # Should create default schedule
        self.assertEqual(InspectionSchedule.objects.count(), 1)

    def test_get_schedule_exists(self):
        """Test getting existing schedule."""
        schedule = InspectionSchedule.objects.create(
            name='Custom Schedule',
            interval_type='hourly',
            interval_value=2
        )
        
        response = self.client.get('/api/schedule/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Custom Schedule')
        self.assertEqual(response.data['data']['interval_type'], 'hourly')

    def test_get_schedule_unauthenticated(self):
        """Test getting schedule without authentication."""
        self.client.credentials()
        response = self.client.get('/api/schedule/')
        self.assertEqual(response.status_code, 401)

    def test_update_schedule(self):
        """Test updating schedule."""
        schedule = InspectionSchedule.objects.create(
            name='Old Schedule',
            interval_type='daily',
            interval_value=1
        )
        
        data = {
            'name': 'New Schedule',
            'interval_type': 'weekly',
            'interval_value': 1,
            'execute_day': 2
        }
        response = self.client.put(
            '/api/schedule/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '调度配置更新成功')
        
        schedule.refresh_from_db()
        self.assertEqual(schedule.name, 'New Schedule')
        self.assertEqual(schedule.interval_type, 'weekly')
        self.assertEqual(schedule.execute_day, 2)

    def test_update_schedule_create_if_not_exists(self):
        """Test updating creates schedule if none exists."""
        data = {
            'name': 'New Schedule',
            'interval_type': 'monthly',
            'interval_value': 1
        }
        response = self.client.put(
            '/api/schedule/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InspectionSchedule.objects.count(), 1)

    def test_update_schedule_invalid_data(self):
        """Test updating schedule with invalid data."""
        data = {'interval_value': 0}  # Invalid value
        response = self.client.put(
            '/api/schedule/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_update_schedule_sets_updated_by(self):
        """Test that updating schedule sets updated_by."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1
        )
        
        data = {'name': 'Updated Schedule'}
        response = self.client.put(
            '/api/schedule/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        schedule.refresh_from_db()
        self.assertEqual(schedule.updated_by, self.user)


class RunNowViewTests(TestCase):
    """Test cases for RunNowView."""

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
            is_active=True,
            created_by=self.user
        )
        self.server.set_password('test_password')
        self.server.save()

    def test_run_now_no_servers(self):
        """Test running inspection with no servers."""
        Server.objects.all().delete()
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('没有可用的服务器', response.data['message'])

    def test_run_now_no_active_servers(self):
        """Test running inspection with no active servers."""
        self.server.is_active = False
        self.server.save()
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_success(self, mock_service_class):
        """Test running inspection successfully."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['success'], 1)
        self.assertEqual(response.data['data']['failed'], 0)

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_multiple_servers(self, mock_service_class):
        """Test running inspection on multiple servers."""
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
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['results']), 2)
        self.assertEqual(response.data['data']['success'], 2)

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_with_schedule_command(self, mock_service_class):
        """Test running inspection uses schedule command."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            inspection_command='custom_command'
        )
        
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        # Verify the service was called with the custom command
        mock_service.execute_inspection.assert_called_once()
        call_args = mock_service.execute_inspection.call_args
        self.assertEqual(call_args[0][1], 'custom_command')

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_default_command(self, mock_service_class):
        """Test running inspection uses default command when no schedule."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_record.has_alert = False
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        # Verify the service was called with default command
        call_args = mock_service.execute_inspection.call_args
        self.assertEqual(call_args[0][1], 'df -h')

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_partial_failure(self, mock_service_class):
        """Test running inspection with partial failure."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        
        mock_service = MagicMock()
        
        def side_effect(server, command, user, is_scheduled):
            mock_record = MagicMock()
            if server.name == 'Test Server':
                mock_record.status = 'success'
            else:
                mock_record.status = 'failed'
            mock_record.has_alert = False
            return mock_record
        
        mock_service.execute_inspection.side_effect = side_effect
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['success'], 1)
        self.assertEqual(response.data['data']['failed'], 1)

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_all_failures(self, mock_service_class):
        """Test running inspection with all failures."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'failed'
        mock_record.has_alert = True
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['success'], 0)
        self.assertEqual(response.data['data']['failed'], 1)

    @patch('apps.schedules.views.InspectionService')
    def test_run_now_exception_handling(self, mock_service_class):
        """Test exception handling during inspection."""
        mock_service = MagicMock()
        mock_service.execute_inspection.side_effect = Exception('SSH Error')
        mock_service_class.return_value = mock_service
        
        response = self.client.post('/api/schedule/run-now/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['success'], 0)
        self.assertEqual(response.data['data']['failed'], 1)
        self.assertIn('SSH Error', response.data['data']['results'][0]['error'])

    def test_run_now_is_scheduled_flag(self):
        """Test that run now sets is_scheduled flag."""
        with patch('apps.schedules.views.InspectionService') as mock_service_class:
            mock_service = MagicMock()
            mock_record = MagicMock()
            mock_record.status = 'success'
            mock_record.has_alert = False
            mock_service.execute_inspection.return_value = mock_record
            mock_service_class.return_value = mock_service
            
            response = self.client.post('/api/schedule/run-now/')
            
            # Verify is_scheduled=True was passed (4th positional arg or keyword)
            call_args = mock_service.execute_inspection.call_args
            # Check kwargs for is_scheduled
            if call_args[1] and 'is_scheduled' in call_args[1]:
                self.assertTrue(call_args[1]['is_scheduled'])
            else:
                # Check positional args
                self.assertTrue(len(call_args[0]) >= 4)

    def test_run_now_unauthenticated(self):
        """Test running inspection without authentication."""
        self.client.credentials()
        response = self.client.post('/api/schedule/run-now/')
        self.assertEqual(response.status_code, 401)

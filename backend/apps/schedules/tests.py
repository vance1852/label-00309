"""Unit tests for schedules module."""
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import InspectionSchedule
from .tasks import run_scheduled_inspection
from apps.servers.models import Server

User = get_user_model()


@pytest.mark.django_db
class ScheduleModelTests(TestCase):
    """Tests for InspectionSchedule model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_schedule_creation_default(self):
        """Test InspectionSchedule creation with default values."""
        schedule = InspectionSchedule.objects.create(
            updated_by=self.user
        )
        
        self.assertEqual(schedule.name, '定时巡检')
        self.assertEqual(schedule.interval_type, 'daily')
        self.assertEqual(schedule.interval_value, 1)
        self.assertEqual(str(schedule.execute_time), '02:00:00')
        self.assertEqual(schedule.inspection_command, 'df -h')
        self.assertTrue(schedule.is_active)

    def test_schedule_creation_custom(self):
        """Test InspectionSchedule creation with custom values."""
        schedule = InspectionSchedule.objects.create(
            name='每周巡检',
            interval_type='weekly',
            interval_value=2,
            execute_time='03:30:00',
            execute_day=1,
            inspection_command='df -h && lsblk',
            is_active=False,
            updated_by=self.user
        )
        
        self.assertEqual(str(schedule), '每周巡检 - 每周')
        self.assertEqual(schedule.interval_type, 'weekly')
        self.assertFalse(schedule.is_active)


@pytest.mark.django_db
class CeleryTaskTests(TestCase):
    """Tests for Celery tasks."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.schedule = InspectionSchedule.objects.create(
            is_active=True,
            inspection_command='df -h'
        )
        self.server1 = Server.objects.create(
            name='Server 1',
            ip_address='192.168.1.1',
            ssh_username='root',
            is_active=True
        )
        self.server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.2',
            ssh_username='root',
            is_active=True
        )

    def test_run_scheduled_inspection_success(self):
        """Test running scheduled inspection successfully."""
        with patch('apps.inspections.services.InspectionService.execute_inspection') as mock_execute:
            mock_execute.return_value = MagicMock(status='success')
            
            result = run_scheduled_inspection()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['success'], 2)
            self.assertEqual(result['failed'], 0)
            self.assertEqual(mock_execute.call_count, 2)
            
            self.schedule.refresh_from_db()
            self.assertIsNotNone(self.schedule.last_run)

    def test_run_scheduled_inspection_partial_failure(self):
        """Test scheduled inspection with some failures."""
        with patch('apps.inspections.services.InspectionService.execute_inspection') as mock_execute:
            mock_execute.side_effect = [
                MagicMock(status='success'),
                MagicMock(status='failed')
            ]
            
            result = run_scheduled_inspection()
            
            self.assertEqual(result['success'], 1)
            self.assertEqual(result['failed'], 1)

    def test_run_scheduled_inspection_no_schedule(self):
        """Test running inspection when no schedule is active."""
        self.schedule.is_active = False
        self.schedule.save()
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)

    def test_run_scheduled_inspection_no_servers(self):
        """Test running inspection when there are no active servers."""
        Server.objects.update(is_active=False)
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)

    def test_run_scheduled_inspection_exception(self):
        """Test handling exceptions during inspection."""
        with patch('apps.inspections.services.InspectionService.execute_inspection') as mock_execute:
            mock_execute.side_effect = Exception('SSH Error')
            
            result = run_scheduled_inspection()
            
            self.assertEqual(result['success'], 0)
            self.assertEqual(result['failed'], 2)


@pytest.mark.django_db
class ScheduleViewTests(APITestCase):
    """Tests for Schedule views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.schedule = InspectionSchedule.objects.create(
            name='默认巡检',
            interval_type='daily',
            updated_by=self.user
        )
        
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            ssh_username='root',
            is_active=True
        )

    def test_get_schedule(self):
        """Test getting schedule configuration."""
        url = reverse('schedule')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], '默认巡检')

    def test_get_schedule_creates_default(self):
        """Test that getting schedule creates a default if none exists."""
        self.schedule.delete()
        
        url = reverse('schedule')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(InspectionSchedule.objects.count(), 1)
        self.assertIsNotNone(response.data['data'])

    def test_update_schedule(self):
        """Test updating schedule."""
        url = reverse('schedule')
        data = {
            'name': '更新后的巡检',
            'interval_type': 'hourly',
            'interval_value': 4,
            'is_active': False
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.name, '更新后的巡检')
        self.assertEqual(self.schedule.interval_type, 'hourly')
        self.assertEqual(self.schedule.interval_value, 4)
        self.assertFalse(self.schedule.is_active)

    def test_update_schedule_creates_new(self):
        """Test updating schedule creates new if none exists."""
        self.schedule.delete()
        
        url = reverse('schedule')
        data = {
            'name': '新建巡检',
            'interval_type': 'weekly',
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(InspectionSchedule.objects.count(), 1)
        schedule = InspectionSchedule.objects.first()
        self.assertEqual(schedule.name, '新建巡检')
        self.assertEqual(schedule.interval_type, 'weekly')

    def test_run_now_success(self):
        """Test running inspection now."""
        url = reverse('run-now')
        
        with patch('apps.inspections.services.InspectionService.execute_inspection') as mock_execute:
            mock_execute.return_value = MagicMock(
                status='success',
                has_alert=False,
                server=self.server
            )
            
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('巡检完成', response.data['message'])
            mock_execute.assert_called_once()

    def test_run_now_no_servers(self):
        """Test running inspection now with no servers."""
        self.server.is_active = False
        self.server.save()
        
        url = reverse('run-now')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('没有可用的服务器', response.data['message'])

    def test_run_now_with_failures(self):
        """Test running inspection now with some failures."""
        url = reverse('run-now')
        
        with patch('apps.inspections.services.InspectionService.execute_inspection') as mock_execute:
            mock_execute.side_effect = Exception('Connection error')
            
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['data']['success'], 0)
            self.assertEqual(response.data['data']['failed'], 1)

    def test_unauthenticated_access_schedule(self):
        """Test that unauthenticated users cannot access schedule."""
        unauthenticated_client = APIClient()
        url = reverse('schedule')
        response = unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access_run_now(self):
        """Test that unauthenticated users cannot run inspection now."""
        unauthenticated_client = APIClient()
        url = reverse('run-now')
        response = unauthenticated_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

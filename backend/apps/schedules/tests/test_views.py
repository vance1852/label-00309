"""Tests for schedule views."""
import pytest
from django.urls import reverse
from unittest.mock import patch
from apps.schedules.models import InspectionSchedule


class TestScheduleView:
    """Tests for ScheduleView."""

    def test_get_schedule_authenticated(self, authenticated_client, db):
        """Test getting schedule when authenticated."""
        url = reverse('schedule')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert 'data' in data
        assert InspectionSchedule.objects.count() == 1

    def test_get_schedule_unauthenticated(self, api_client, db):
        """Test getting schedule when unauthenticated."""
        url = reverse('schedule')
        response = api_client.get(url)

        assert response.status_code == 401

    def test_get_existing_schedule(self, authenticated_client, inspection_schedule):
        """Test getting existing schedule."""
        url = reverse('schedule')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert data['data']['name'] == 'Daily Inspection'
        assert InspectionSchedule.objects.count() == 1

    def test_update_schedule(self, authenticated_client, inspection_schedule, user):
        """Test updating schedule."""
        url = reverse('schedule')
        update_data = {
            'name': 'Updated Schedule',
            'interval_type': 'hourly',
            'interval_value': 2,
            'inspection_command': 'df -i',
            'is_active': True
        }
        response = authenticated_client.put(url, update_data, format='json')

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert data['data']['name'] == 'Updated Schedule'
        assert data['data']['interval_type'] == 'hourly'
        
        inspection_schedule.refresh_from_db()
        assert inspection_schedule.name == 'Updated Schedule'
        assert inspection_schedule.updated_by == user

    def test_update_schedule_invalid_interval_value(self, authenticated_client, inspection_schedule):
        """Test updating schedule with invalid interval value."""
        url = reverse('schedule')
        update_data = {
            'interval_value': 0
        }
        response = authenticated_client.put(url, update_data, format='json')

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False
        assert '必须大于0' in data['message']

    def test_update_schedule_invalid_execute_day(self, authenticated_client, inspection_schedule):
        """Test updating schedule with invalid execute day."""
        url = reverse('schedule')
        update_data = {
            'execute_day': 35
        }
        response = authenticated_client.put(url, update_data, format='json')

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False
        assert '必须在1-31之间' in data['message']


class TestRunNowView:
    """Tests for RunNowView."""

    def test_run_now_no_servers(self, authenticated_client, db):
        """Test run now with no servers."""
        url = reverse('run-now')
        response = authenticated_client.post(url)

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False
        assert '没有可用的服务器' in data['message']

    def test_run_now_success(self, authenticated_client, server, inspection_schedule, mock_ssh_client):
        """Test successful manual inspection run."""
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""/dev/sda1       200G   50G  150G  25% /"""

        url = reverse('run-now')
        
        with patch('apps.alerts.services.AlertService'):
            response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert data['data']['success'] == 1
        assert data['data']['failed'] == 0
        assert '巡检完成' in data['message']

    def test_run_now_failed_connection(self, authenticated_client, server, inspection_schedule, mock_ssh_auth_failure):
        """Test manual inspection run with connection failure."""
        url = reverse('run-now')
        response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert data['data']['success'] == 0
        assert data['data']['failed'] == 1

    def test_run_now_unauthenticated(self, api_client, db):
        """Test run now when unauthenticated."""
        url = reverse('run-now')
        response = api_client.post(url)

        assert response.status_code == 401

    def test_run_now_multiple_servers(self, authenticated_client, user, inspection_schedule, mock_ssh_client):
        """Test run now with multiple servers."""
        from apps.servers.models import Server
        
        for i in range(3):
            s = Server.objects.create(
                name=f'Server {i}',
                ip_address=f'192.168.1.{i}',
                port=22,
                ssh_username='root',
                is_active=True,
                created_by=user
            )
            s.set_password('pass')
            s.save()

        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""/dev/sda1       200G   50G  150G  25% /"""

        url = reverse('run-now')
        
        with patch('apps.alerts.services.AlertService'):
            response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert data['success'] == True
        assert data['data']['success'] == 3
        assert data['data']['failed'] == 0

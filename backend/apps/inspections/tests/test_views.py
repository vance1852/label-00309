import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db

class TestInspectionViewSet:
    def test_list_records_authenticated(self, authenticated_client, inspection_record):
        url = reverse('inspection-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data

    def test_list_records_unauthenticated(self, api_client, inspection_record):
        url = reverse('inspection-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_record(self, authenticated_client, inspection_record):
        url = reverse('inspection-detail', kwargs={'pk': inspection_record.pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == inspection_record.id

    def test_retrieve_nonexistent_record(self, authenticated_client):
        url = reverse('inspection-detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_record(self, authenticated_client, inspection_record):
        url = reverse('inspection-detail', kwargs={'pk': inspection_record.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '巡检记录删除成功'

    def test_execute_inspection_no_servers(self, authenticated_client):
        url = reverse('inspection-execute')
        data = {
            'server_ids': [9999],
            'command': 'df -h'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False
        assert '未找到有效的服务器' in response.data['message']

    def test_execute_inspection_success(self, authenticated_client, server, mock_ssh_client, alert_config):
        stdin, stdout, stderr = mock_ssh_client.return_value.exec_command.return_value
        stdout.read.return_value = b"""Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   30G   70G  30% /"""
        stderr.read.return_value = b""
        
        url = reverse('inspection-execute')
        data = {
            'server_ids': [server.pk],
            'command': 'df -h'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '巡检执行完成'
        assert len(response.data['data']) == 1

    def test_execute_inspection_with_exception(self, authenticated_client, server, mock_ssh_client):
        mock_ssh_client.return_value.connect.side_effect = Exception('Connection failed')
        
        url = reverse('inspection-execute')
        data = {
            'server_ids': [server.pk],
            'command': 'df -h'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert '巡检执行完成' in response.data['message'] or response.data['code'] == 200

    def test_execute_inspection_invalid_data(self, authenticated_client, server):
        url = reverse('inspection-execute')
        data = {}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_filter_by_status(self, authenticated_client, inspection_record):
        url = reverse('inspection-list')
        response = authenticated_client.get(url, {'status': 'success'})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_has_alert(self, authenticated_client, inspection_record):
        url = reverse('inspection-list')
        response = authenticated_client.get(url, {'has_alert': 'false'})
        assert response.status_code == status.HTTP_200_OK

    def test_statistics(self, authenticated_client, inspection_record):
        url = reverse('inspection-statistics')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data['data']
        assert 'today' in response.data['data']
        assert 'alerts' in response.data['data']
        assert 'status_stats' in response.data['data']

    def test_statistics_with_alert_records(self, db, authenticated_client, server, user):
        from apps.inspections.models import InspectionRecord
        InspectionRecord.objects.create(
            server=server,
            executed_by=user,
            command='df -h',
            raw_output='output',
            parsed_result={'disks': []},
            status='warning',
            has_alert=True
        )
        
        url = reverse('inspection-statistics')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['alerts'] >= 1

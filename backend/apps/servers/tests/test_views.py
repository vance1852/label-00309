import pytest
import paramiko
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db

class TestServerViewSet:
    def test_list_servers_authenticated(self, authenticated_client, server):
        url = reverse('server-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_list_servers_unauthenticated(self, api_client, server):
        url = reverse('server-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_server(self, authenticated_client, user):
        url = reverse('server-list')
        data = {
            'name': 'New Server',
            'ip_address': '10.0.0.1',
            'port': 22,
            'ssh_username': 'admin',
            'ssh_password': 'newpassword',
            'description': 'New server',
            'is_active': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '服务器添加成功'

    def test_create_server_invalid_data(self, authenticated_client):
        url = reverse('server-list')
        data = {
            'name': 'New Server',
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_retrieve_server(self, authenticated_client, server):
        url = reverse('server-detail', kwargs={'pk': server.pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == server.name

    def test_update_server(self, authenticated_client, server):
        url = reverse('server-detail', kwargs={'pk': server.pk})
        data = {
            'name': 'Updated Server',
            'description': 'Updated description'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '服务器更新成功'

    def test_update_server_invalid(self, authenticated_client, server):
        url = reverse('server-detail', kwargs={'pk': server.pk})
        data = {
            'ip_address': 'invalid_ip'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_delete_server(self, authenticated_client, server):
        url = reverse('server-detail', kwargs={'pk': server.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '服务器删除成功'

    def test_delete_nonexistent_server(self, authenticated_client):
        url = reverse('server-detail', kwargs={'pk': 99999})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_test_ssh_connection_success(self, authenticated_client, server, mock_ssh_connect_success):
        url = reverse('server-test', kwargs={'pk': server.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'SSH连接测试成功'

    def test_test_ssh_connection_auth_failure(self, authenticated_client, server, mock_ssh_auth_failure):
        url = reverse('server-test', kwargs={'pk': server.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False
        assert 'SSH认证失败' in response.data['message']

    def test_test_ssh_connection_ssh_exception(self, authenticated_client, server, mock_ssh_exception):
        url = reverse('server-test', kwargs={'pk': server.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False
        assert 'SSH连接错误' in response.data['message']

    def test_test_ssh_connection_general_exception(self, authenticated_client, server):
        url = reverse('server-test', kwargs={'pk': server.pk})
        with patch('paramiko.SSHClient') as mock:
            mock.return_value.connect.side_effect = Exception('Unknown error')
            response = authenticated_client.post(url)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] == False
            assert '连接失败' in response.data['message']

    def test_active_servers(self, authenticated_client, server):
        url = reverse('server-active')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

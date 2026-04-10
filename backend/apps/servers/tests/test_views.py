"""Tests for server views."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.servers.models import Server


User = get_user_model()


class ServerViewSetTests(TestCase):
    """Test cases for ServerViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        self.server_data = {
            'name': 'Test Server',
            'ip_address': '192.168.1.100',
            'port': 22,
            'ssh_username': 'root',
            'ssh_password': 'secret123',
            'description': 'Test description',
            'is_active': True
        }

    def test_list_servers_authenticated(self):
        """Test listing servers when authenticated."""
        Server.objects.create(
            name='Server 1',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        response = self.client.get('/api/servers/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_list_servers_unauthenticated(self):
        """Test listing servers when not authenticated."""
        self.client.credentials()  # Clear credentials
        response = self.client.get('/api/servers/')
        self.assertEqual(response.status_code, 401)

    def test_create_server_success(self):
        """Test creating a server successfully."""
        response = self.client.post(
            '/api/servers/',
            data=json.dumps(self.server_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '服务器添加成功')
        self.assertEqual(Server.objects.count(), 1)

    def test_create_server_missing_required_field(self):
        """Test creating a server with missing required field."""
        data = self.server_data.copy()
        del data['name']
        response = self.client.post(
            '/api/servers/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_create_server_invalid_port(self):
        """Test creating a server with invalid port."""
        data = self.server_data.copy()
        data['port'] = 70000
        response = self.client.post(
            '/api/servers/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_retrieve_server(self):
        """Test retrieving a single server."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        response = self.client.get(f'/api/servers/{server.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Test Server')

    def test_retrieve_nonexistent_server(self):
        """Test retrieving a non-existent server."""
        response = self.client.get('/api/servers/999/')
        self.assertEqual(response.status_code, 404)

    def test_update_server(self):
        """Test updating a server."""
        server = Server.objects.create(
            name='Old Name',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        update_data = {'name': 'New Name'}
        response = self.client.patch(
            f'/api/servers/{server.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '服务器更新成功')
        
        server.refresh_from_db()
        self.assertEqual(server.name, 'New Name')

    def test_update_server_invalid_data(self):
        """Test updating a server with invalid data."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        update_data = {'port': 0}
        response = self.client.patch(
            f'/api/servers/{server.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_delete_server(self):
        """Test deleting a server."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        response = self.client.delete(f'/api/servers/{server.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '服务器删除成功')
        self.assertEqual(Server.objects.count(), 0)

    def test_delete_nonexistent_server(self):
        """Test deleting a non-existent server."""
        response = self.client.delete('/api/servers/999/')
        self.assertEqual(response.status_code, 404)

    @patch('apps.servers.views.paramiko.SSHClient')
    def test_test_ssh_connection_success(self, mock_ssh_client):
        """Test SSH connection test with successful connection."""
        # Mock SSH client
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('correct_password')
        server.save()
        
        response = self.client.post(f'/api/servers/{server.id}/test/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'SSH连接测试成功')

    @patch('apps.servers.views.paramiko.SSHClient')
    def test_test_ssh_connection_auth_failure(self, mock_ssh_client):
        """Test SSH connection test with authentication failure."""
        from paramiko import AuthenticationException
        
        mock_client = MagicMock()
        mock_client.connect.side_effect = AuthenticationException()
        mock_ssh_client.return_value = mock_client
        
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('wrong_password')
        server.save()
        
        response = self.client.post(f'/api/servers/{server.id}/test/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('认证失败', response.data['message'])

    @patch('apps.servers.views.paramiko.SSHClient')
    def test_test_ssh_connection_ssh_exception(self, mock_ssh_client):
        """Test SSH connection test with SSH exception."""
        from paramiko import SSHException
        
        mock_client = MagicMock()
        mock_client.connect.side_effect = SSHException('Connection refused')
        mock_ssh_client.return_value = mock_client
        
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('password')
        server.save()
        
        response = self.client.post(f'/api/servers/{server.id}/test/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('SSH连接错误', response.data['message'])

    @patch('apps.servers.views.paramiko.SSHClient')
    def test_test_ssh_connection_general_exception(self, mock_ssh_client):
        """Test SSH connection test with general exception."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception('Network error')
        mock_ssh_client.return_value = mock_client
        
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('password')
        server.save()
        
        response = self.client.post(f'/api/servers/{server.id}/test/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('连接失败', response.data['message'])

    def test_test_ssh_connection_nonexistent_server(self):
        """Test SSH connection test for non-existent server."""
        response = self.client.post('/api/servers/999/test/')
        self.assertEqual(response.status_code, 404)

    def test_active_servers_list(self):
        """Test getting active servers list."""
        Server.objects.create(
            name='Active Server',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        Server.objects.create(
            name='Inactive Server',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            is_active=False,
            created_by=self.user
        )
        
        response = self.client.get('/api/servers/active/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Active Server')

    def test_filter_servers_by_is_active(self):
        """Test filtering servers by is_active status."""
        Server.objects.create(
            name='Active Server',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        Server.objects.create(
            name='Inactive Server',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            is_active=False,
            created_by=self.user
        )
        
        response = self.client.get('/api/servers/?is_active=true')
        self.assertEqual(response.status_code, 200)
        # Pagination response
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_search_servers(self):
        """Test searching servers."""
        Server.objects.create(
            name='Web Server',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        Server.objects.create(
            name='Database Server',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        response = self.client.get('/api/servers/?search=Web')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['list']), 1)

    def test_order_servers(self):
        """Test ordering servers."""
        Server.objects.create(
            name='Server B',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        Server.objects.create(
            name='Server A',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        response = self.client.get('/api/servers/?ordering=name')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        names = [s['name'] for s in response.data['data']['list']]
        self.assertEqual(names, ['Server A', 'Server B'])

    def test_pagination(self):
        """Test server list pagination."""
        for i in range(15):
            Server.objects.create(
                name=f'Server {i}',
                ip_address=f'192.168.1.{i}',
                port=22,
                ssh_username='root',
                created_by=self.user
            )
        
        response = self.client.get('/api/servers/?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['list']), 10)
        self.assertEqual(response.data['data']['total'], 15)
        self.assertEqual(response.data['data']['total_pages'], 2)

    def test_list_serializer_used_for_list_action(self):
        """Test that ServerListSerializer is used for list action."""
        Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        response = self.client.get('/api/servers/')
        self.assertEqual(response.status_code, 200)
        # List serializer doesn't include created_by field
        server_data = response.data['data']['list'][0]
        self.assertNotIn('created_by', server_data)
        self.assertIn('created_by_name', server_data)

    def test_detail_serializer_used_for_retrieve_action(self):
        """Test that ServerSerializer is used for retrieve action."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        response = self.client.get(f'/api/servers/{server.id}/')
        self.assertEqual(response.status_code, 200)
        # Detail serializer includes more fields
        self.assertIn('created_by', response.data['data'])

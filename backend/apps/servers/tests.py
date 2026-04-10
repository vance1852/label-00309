"""Tests for servers app."""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Server
from .serializers import ServerSerializer
from cryptography.fernet import Fernet


class ServerModelTests(TestCase):
    """Test Server model."""

    def test_create_server(self):
        """Test creating a server."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            port=22
        )
        server.set_password('testpass')
        server.save()
        self.assertEqual(server.name, 'Test Server')
        self.assertEqual(server.ip_address, '192.168.1.1')

    def test_password_encryption_decryption(self):
        """Test password encryption and decryption."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            port=22
        )
        server.set_password('secretpass')
        server.save()
        # Verify password is encrypted
        self.assertNotEqual(server.ssh_password_encrypted, 'secretpass')
        # Verify password can be decrypted
        decrypted = server.get_password()
        self.assertEqual(decrypted, 'secretpass')

    def test_server_str(self):
        """Test server string representation."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.1',
            port=22
        )
        self.assertEqual(str(server), 'Test Server (192.168.1.1)')


class ServerSerializerTests(TestCase):
    """Test Server serializer."""

    def test_serializer_create(self):
        """Test serializer creating a server."""
        data = {
            'name': 'New Server',
            'ip_address': '10.0.0.1',
            'port': 22,
            'ssh_username': 'root',
            'ssh_password': 'testpass'
        }
        serializer = ServerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        server = serializer.save()
        self.assertEqual(server.name, 'New Server')

    def test_serializer_port_validation(self):
        """Test serializer port validation."""
        data = {
            'name': 'New Server',
            'ip_address': '10.0.0.1',
            'port': 70000,
            'ssh_password': 'testpass'
        }
        serializer = ServerSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_serializer_ip_validation(self):
        """Test serializer IP address validation."""
        data = {
            'name': 'New Server',
            'ip_address': 'invalid-ip',
            'port': 22,
            'ssh_password': 'testpass'
        }
        serializer = ServerSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ServerViewSetTests(APITestCase):
    """Test Server ViewSet."""

    def setUp(self):
        """Set up test data."""
        from apps.users.models import User
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

    def test_server_list_authenticated(self):
        """Test server list with authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/servers/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_server_list_unauthenticated(self):
        """Test server list without authentication."""
        response = self.client.get('/api/servers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_server_create(self):
        """Test creating a server."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Server',
            'ip_address': '10.0.0.2',
            'port': 22,
            'ssh_username': 'root',
            'ssh_password': 'testpass'
        }
        response = self.client.post('/api/servers/', data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_server_detail(self):
        """Test getting server detail."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/servers/{self.server.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Test Server')

    def test_server_update(self):
        """Test updating a server."""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Updated Server'}
        response = self.client.patch(f'/api/servers/{self.server.id}/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.server.refresh_from_db()
        self.assertEqual(self.server.name, 'Updated Server')

    def test_server_delete(self):
        """Test deleting a server."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/servers/{self.server.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Server.objects.count(), 0)

    def test_server_filter_by_name(self):
        """Test filtering servers by name."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/servers/?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    @patch('paramiko.SSHClient')
    def test_ssh_connection_success(self, mock_ssh_class):
        """Test SSH connection success."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/servers/{self.server.id}/test/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        mock_instance.connect.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_ssh_connection_authentication_failure(self, mock_ssh_class):
        """Test SSH connection authentication failure."""
        from paramiko.ssh_exception import AuthenticationException
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.side_effect = AuthenticationException('Auth failed')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/servers/{self.server.id}/test/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    @patch('paramiko.SSHClient')
    def test_ssh_connection_timeout(self, mock_ssh_class):
        """Test SSH connection timeout."""
        import socket
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.side_effect = socket.timeout('Timeout')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/servers/{self.server.id}/test/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_active_servers_list(self):
        """Test active servers list."""
        self.server.is_active = True
        self.server.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/servers/active/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

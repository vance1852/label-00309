"""Tests for server serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.servers.models import Server
from apps.servers.serializers import ServerSerializer, ServerListSerializer


User = get_user_model()


class ServerSerializerTests(TestCase):
    """Test cases for ServerSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.valid_data = {
            'name': 'Test Server',
            'ip_address': '192.168.1.100',
            'port': 22,
            'ssh_username': 'root',
            'ssh_password': 'secret123',
            'description': 'Test description',
            'is_active': True
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = ServerSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_without_password(self):
        """Test serializer without password is valid."""
        data = self.valid_data.copy()
        del data['ssh_password']
        serializer = ServerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_missing_required_fields(self):
        """Test serializer with missing required fields."""
        required_fields = ['name', 'ip_address', 'ssh_username']
        for field in required_fields:
            data = self.valid_data.copy()
            del data[field]
            serializer = ServerSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)

    def test_validate_ip_address_empty(self):
        """Test IP address validation with empty value."""
        data = self.valid_data.copy()
        data['ip_address'] = ''
        serializer = ServerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ip_address', serializer.errors)

    def test_validate_port_too_low(self):
        """Test port validation with value too low."""
        data = self.valid_data.copy()
        data['port'] = 0
        serializer = ServerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('port', serializer.errors)

    def test_validate_port_too_high(self):
        """Test port validation with value too high."""
        data = self.valid_data.copy()
        data['port'] = 65536
        serializer = ServerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('port', serializer.errors)

    def test_validate_port_boundary_values(self):
        """Test port validation with boundary values."""
        # Valid boundary values
        for port in [1, 22, 65535]:
            data = self.valid_data.copy()
            data['port'] = port
            serializer = ServerSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Port {port} should be valid")

    def test_create_server_with_password(self):
        """Test creating server with password through serializer."""
        serializer = ServerSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        server = serializer.save(created_by=self.user)
        
        self.assertEqual(server.name, 'Test Server')
        self.assertEqual(server.ip_address, '192.168.1.100')
        self.assertEqual(server.get_password(), 'secret123')

    def test_create_server_without_password(self):
        """Test creating server without password through serializer."""
        data = self.valid_data.copy()
        del data['ssh_password']
        serializer = ServerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        server = serializer.save(created_by=self.user)
        
        self.assertEqual(server.name, 'Test Server')
        # Password should be empty or None
        self.assertFalse(server.ssh_password_encrypted)

    def test_update_server_with_password(self):
        """Test updating server with new password."""
        server = Server.objects.create(
            name='Old Name',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('old_password')
        server.save()
        
        update_data = {
            'name': 'New Name',
            'ssh_password': 'new_password'
        }
        serializer = ServerSerializer(server, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_server = serializer.save()
        
        self.assertEqual(updated_server.name, 'New Name')
        self.assertEqual(updated_server.get_password(), 'new_password')

    def test_update_server_without_password(self):
        """Test updating server without changing password."""
        server = Server.objects.create(
            name='Old Name',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('existing_password')
        server.save()
        
        update_data = {'name': 'New Name'}
        serializer = ServerSerializer(server, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_server = serializer.save()
        
        self.assertEqual(updated_server.name, 'New Name')
        self.assertEqual(updated_server.get_password(), 'existing_password')

    def test_serializer_output_contains_expected_fields(self):
        """Test serializer output contains expected fields."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        serializer = ServerSerializer(server)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'ip_address', 'port', 'ssh_username',
            'description', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_ssh_password_is_write_only(self):
        """Test that ssh_password is write-only."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server.set_password('secret123')
        server.save()
        
        serializer = ServerSerializer(server)
        self.assertNotIn('ssh_password', serializer.data)

    def test_created_by_name_in_output(self):
        """Test that created_by_name is in serializer output."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        serializer = ServerSerializer(server)
        self.assertEqual(serializer.data['created_by_name'], 'testuser')

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set."""
        data = self.valid_data.copy()
        data['id'] = 999
        data['created_at'] = '2020-01-01T00:00:00Z'
        data['updated_at'] = '2020-01-01T00:00:00Z'
        
        serializer = ServerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # id should not be in validated_data
        self.assertNotIn('id', serializer.validated_data)


class ServerListSerializerTests(TestCase):
    """Test cases for ServerListSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_list_serializer_excludes_sensitive_data(self):
        """Test that list serializer excludes sensitive data like password."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        serializer = ServerListSerializer(server)
        data = serializer.data
        
        # Should not contain password-related fields
        self.assertNotIn('ssh_password', data)
        self.assertNotIn('ssh_password_encrypted', data)
        
        # Should contain basic fields
        self.assertIn('name', data)
        self.assertIn('ip_address', data)
        self.assertIn('ssh_username', data)

    def test_list_serializer_fields(self):
        """Test list serializer has correct fields."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            description='Test desc',
            is_active=True,
            created_by=self.user
        )
        serializer = ServerListSerializer(server)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'ip_address', 'port', 'ssh_username',
            'description', 'is_active', 'created_by_name', 'created_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_list_serializer_created_by_name(self):
        """Test list serializer includes created_by_name."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        serializer = ServerListSerializer(server)
        self.assertEqual(serializer.data['created_by_name'], 'testuser')

    def test_list_serializer_with_null_created_by(self):
        """Test list serializer handles null created_by."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=None
        )
        serializer = ServerListSerializer(server)
        # When created_by is None, the field may not be present
        if 'created_by_name' in serializer.data:
            self.assertIsNone(serializer.data['created_by_name'])

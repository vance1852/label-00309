"""Tests for server models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.servers.models import Server, get_encryption_key


User = get_user_model()


class ServerModelTests(TestCase):
    """Test cases for Server model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.server_data = {
            'name': 'Test Server',
            'ip_address': '192.168.1.100',
            'port': 22,
            'ssh_username': 'root',
            'description': 'Test server description',
            'is_active': True,
            'created_by': self.user
        }

    def test_create_server_without_password(self):
        """Test creating a server without password."""
        server = Server.objects.create(**self.server_data)
        self.assertEqual(server.name, 'Test Server')
        self.assertEqual(server.ip_address, '192.168.1.100')
        self.assertEqual(server.port, 22)
        self.assertEqual(server.ssh_username, 'root')
        self.assertTrue(server.is_active)
        self.assertEqual(str(server), 'Test Server (192.168.1.100)')

    def test_create_server_with_password(self):
        """Test creating a server with password encryption."""
        server = Server(**self.server_data)
        server.set_password('secret_password')
        server.save()
        
        # Verify password is encrypted
        self.assertNotEqual(server.ssh_password_encrypted, 'secret_password')
        self.assertTrue(len(server.ssh_password_encrypted) > 0)
        
        # Verify password can be decrypted
        decrypted = server.get_password()
        self.assertEqual(decrypted, 'secret_password')

    def test_password_encryption_is_reversible(self):
        """Test that password encryption is reversible."""
        server = Server(**self.server_data)
        original_password = 'my_secure_password_123'
        server.set_password(original_password)
        server.save()
        
        retrieved_password = server.get_password()
        self.assertEqual(retrieved_password, original_password)

    def test_password_encryption_with_special_characters(self):
        """Test password encryption with special characters."""
        server = Server(**self.server_data)
        special_password = 'p@$$w0rd!#$%^&*()_+-=[]{}|;:,.<>?'
        server.set_password(special_password)
        server.save()
        
        retrieved_password = server.get_password()
        self.assertEqual(retrieved_password, special_password)

    def test_server_str_representation(self):
        """Test server string representation."""
        server = Server.objects.create(**self.server_data)
        expected_str = f"{server.name} ({server.ip_address})"
        self.assertEqual(str(server), expected_str)

    def test_server_ordering(self):
        """Test server ordering."""
        server1 = Server.objects.create(
            name='Server 1',
            ip_address='192.168.1.1',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.2',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        
        servers = list(Server.objects.all())
        # Verify both servers exist
        self.assertEqual(len(servers), 2)
        self.assertIn(server1, servers)
        self.assertIn(server2, servers)

    def test_server_is_active_default(self):
        """Test server is_active defaults to True."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        self.assertTrue(server.is_active)

    def test_server_port_default(self):
        """Test server port defaults to 22."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            ssh_username='root',
            created_by=self.user
        )
        self.assertEqual(server.port, 22)

    def test_server_description_optional(self):
        """Test server description is optional."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )
        self.assertIsNone(server.description)

    def test_server_created_by_nullable(self):
        """Test server created_by can be null."""
        server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=None
        )
        self.assertIsNone(server.created_by)


class EncryptionKeyTests(TestCase):
    """Test cases for encryption key generation."""

    def test_get_encryption_key_returns_bytes(self):
        """Test that get_encryption_key returns bytes."""
        key = get_encryption_key()
        self.assertIsInstance(key, bytes)

    def test_get_encryption_key_is_consistent(self):
        """Test that get_encryption_key returns consistent key."""
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        self.assertEqual(key1, key2)

    def test_get_encryption_key_length(self):
        """Test that encryption key has correct length."""
        key = get_encryption_key()
        # Fernet key is 32 bytes base64 encoded, resulting in 44 bytes
        self.assertEqual(len(key), 44)

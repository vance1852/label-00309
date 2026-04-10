import pytest
from django.test import TestCase
from ..models import Server, get_encryption_key
from cryptography.fernet import Fernet
import base64
import hashlib
from django.conf import settings

pytestmark = pytest.mark.django_db

class TestServerModel:
    def test_server_creation(self, server):
        assert server.name == 'Test Server'
        assert server.ip_address == '192.168.1.1'
        assert server.port == 22
        assert server.ssh_username == 'root'
        assert server.is_active is True

    def test_password_encryption_decryption(self, server):
        original_password = 'testpassword123'
        server.set_password(original_password)
        server.save()
        
        decrypted = server.get_password()
        assert decrypted == original_password

    def test_get_encryption_key(self):
        key = get_encryption_key()
        expected_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        expected_key = base64.urlsafe_b64encode(expected_key)
        assert key == expected_key

    def test_server_str_method(self, server):
        expected_str = f"{server.name} ({server.ip_address})"
        assert str(server) == expected_str

    def test_server_inactive(self, server):
        server.is_active = False
        server.save()
        assert server.is_active is False

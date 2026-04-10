"""Tests for alert serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.alerts.models import AlertConfig, AlertRecipient
from apps.alerts.serializers import (
    AlertConfigSerializer,
    AlertRecipientSerializer,
    TestEmailSerializer
)


User = get_user_model()


class AlertRecipientSerializerTests(TestCase):
    """Test cases for AlertRecipientSerializer."""

    def setUp(self):
        """Set up test data."""
        self.config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        self.valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'is_active': True
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = AlertRecipientSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_output_fields(self):
        """Test serializer output contains expected fields."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com',
            is_active=True
        )
        serializer = AlertRecipientSerializer(recipient)
        data = serializer.data
        
        expected_fields = ['id', 'name', 'email', 'is_active', 'created_at']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_missing_required_fields(self):
        """Test serializer with missing required fields."""
        required_fields = ['name', 'email']
        for field in required_fields:
            data = self.valid_data.copy()
            del data[field]
            serializer = AlertRecipientSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)

    def test_serializer_invalid_email(self):
        """Test serializer with invalid email."""
        data = self.valid_data.copy()
        data['email'] = 'invalid_email'
        serializer = AlertRecipientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_serializer_create_recipient(self):
        """Test creating recipient through serializer."""
        serializer = AlertRecipientSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        recipient = serializer.save(config=self.config)
        
        self.assertEqual(recipient.name, 'John Doe')
        self.assertEqual(recipient.email, 'john@example.com')
        self.assertEqual(recipient.config, self.config)

    def test_serializer_update_recipient(self):
        """Test updating recipient through serializer."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='Old Name',
            email='old@example.com',
            is_active=True
        )
        update_data = {'name': 'New Name', 'email': 'new@example.com'}
        serializer = AlertRecipientSerializer(recipient, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.name, 'New Name')
        self.assertEqual(updated.email, 'new@example.com')

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set."""
        data = self.valid_data.copy()
        data['id'] = 999
        data['created_at'] = '2020-01-01T00:00:00Z'
        
        serializer = AlertRecipientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('id', serializer.validated_data)


class AlertConfigSerializerTests(TestCase):
    """Test cases for AlertConfigSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.valid_data = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'smtp_username': 'test@test.com',
            'smtp_password': 'smtp_secret',
            'sender_email': 'test@test.com',
            'sender_name': 'Test System',
            'use_tls': True,
            'use_ssl': False,
            'disk_threshold': 80,
            'is_active': True
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = AlertConfigSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_output_fields(self):
        """Test serializer output contains expected fields."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        serializer = AlertConfigSerializer(config)
        data = serializer.data
        
        expected_fields = [
            'id', 'smtp_server', 'smtp_port', 'smtp_username',
            'sender_email', 'sender_name', 'use_tls', 'use_ssl',
            'disk_threshold', 'is_active', 'recipients',
            'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_smtp_password_write_only(self):
        """Test that smtp_password is write-only."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        config.set_password('secret123')
        config.save()
        
        serializer = AlertConfigSerializer(config)
        self.assertNotIn('smtp_password', serializer.data)
        self.assertNotIn('smtp_password_encrypted', serializer.data)

    def test_recipients_field(self):
        """Test recipients are included in serializer output."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        AlertRecipient.objects.create(
            config=config,
            name='John Doe',
            email='john@example.com'
        )
        
        serializer = AlertConfigSerializer(config)
        self.assertEqual(len(serializer.data['recipients']), 1)
        self.assertEqual(serializer.data['recipients'][0]['name'], 'John Doe')

    def test_updated_by_name_field(self):
        """Test updated_by_name is included in serializer output."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com',
            updated_by=self.user
        )
        serializer = AlertConfigSerializer(config)
        self.assertEqual(serializer.data['updated_by_name'], 'testuser')

    def test_updated_by_name_null(self):
        """Test updated_by_name is not present when updated_by is null."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com',
            updated_by=None
        )
        serializer = AlertConfigSerializer(config)
        # When updated_by is None, the field may not be present
        if 'updated_by_name' in serializer.data:
            self.assertIsNone(serializer.data['updated_by_name'])

    def test_validate_smtp_port_too_low(self):
        """Test smtp_port validation with value too low."""
        data = self.valid_data.copy()
        data['smtp_port'] = 0
        serializer = AlertConfigSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('smtp_port', serializer.errors)

    def test_validate_smtp_port_too_high(self):
        """Test smtp_port validation with value too high."""
        data = self.valid_data.copy()
        data['smtp_port'] = 70000
        serializer = AlertConfigSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('smtp_port', serializer.errors)

    def test_validate_smtp_port_boundary_values(self):
        """Test smtp_port validation with boundary values."""
        for port in [1, 25, 587, 465, 65535]:
            data = self.valid_data.copy()
            data['smtp_port'] = port
            serializer = AlertConfigSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Port {port} should be valid")

    def test_validate_disk_threshold_too_low(self):
        """Test disk_threshold validation with value too low."""
        data = self.valid_data.copy()
        data['disk_threshold'] = 0
        serializer = AlertConfigSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('disk_threshold', serializer.errors)

    def test_validate_disk_threshold_too_high(self):
        """Test disk_threshold validation with value too high."""
        data = self.valid_data.copy()
        data['disk_threshold'] = 101
        serializer = AlertConfigSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('disk_threshold', serializer.errors)

    def test_validate_disk_threshold_boundary_values(self):
        """Test disk_threshold validation with boundary values."""
        for threshold in [1, 50, 80, 99, 100]:
            data = self.valid_data.copy()
            data['disk_threshold'] = threshold
            serializer = AlertConfigSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Threshold {threshold} should be valid")

    def test_create_config_with_password(self):
        """Test creating config with password through serializer."""
        serializer = AlertConfigSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        config = serializer.save()
        
        self.assertEqual(config.smtp_server, 'smtp.test.com')
        self.assertEqual(config.get_password(), 'smtp_secret')

    def test_create_config_without_password(self):
        """Test creating config without password through serializer."""
        data = self.valid_data.copy()
        del data['smtp_password']
        serializer = AlertConfigSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        config = serializer.save()
        
        self.assertEqual(config.smtp_server, 'smtp.test.com')
        self.assertFalse(config.smtp_password_encrypted)

    def test_update_config_with_password(self):
        """Test updating config with new password."""
        config = AlertConfig.objects.create(
            smtp_server='old.smtp.com',
            smtp_username='old@test.com',
            sender_email='old@test.com'
        )
        config.set_password('old_password')
        config.save()
        
        update_data = {
            'smtp_server': 'new.smtp.com',
            'smtp_password': 'new_password'
        }
        serializer = AlertConfigSerializer(config, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.smtp_server, 'new.smtp.com')
        self.assertEqual(updated.get_password(), 'new_password')

    def test_update_config_without_password(self):
        """Test updating config without changing password."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        config.set_password('existing_password')
        config.save()
        
        update_data = {'smtp_server': 'new.smtp.com'}
        serializer = AlertConfigSerializer(config, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.smtp_server, 'new.smtp.com')
        self.assertEqual(updated.get_password(), 'existing_password')

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set."""
        data = self.valid_data.copy()
        data['id'] = 999
        data['updated_at'] = '2020-01-01T00:00:00Z'
        
        serializer = AlertConfigSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('id', serializer.validated_data)
        self.assertNotIn('updated_at', serializer.validated_data)


class TestEmailSerializerTests(TestCase):
    """Test cases for TestEmailSerializer."""

    def test_serializer_with_valid_email(self):
        """Test serializer with valid email."""
        data = {'recipient_email': 'test@example.com'}
        serializer = TestEmailSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_missing_email(self):
        """Test serializer with missing email."""
        data = {}
        serializer = TestEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('recipient_email', serializer.errors)

    def test_serializer_invalid_email(self):
        """Test serializer with invalid email."""
        data = {'recipient_email': 'invalid_email'}
        serializer = TestEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('recipient_email', serializer.errors)

    def test_serializer_empty_email(self):
        """Test serializer with empty email."""
        data = {'recipient_email': ''}
        serializer = TestEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('recipient_email', serializer.errors)

    def test_serializer_email_with_special_characters(self):
        """Test serializer with email containing special characters."""
        data = {'recipient_email': 'user+tag@example.co.uk'}
        serializer = TestEmailSerializer(data=data)
        self.assertTrue(serializer.is_valid())

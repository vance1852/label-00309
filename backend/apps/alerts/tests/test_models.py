"""Tests for alert models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.alerts.models import AlertConfig, AlertRecipient, get_encryption_key


User = get_user_model()


class AlertConfigModelTests(TestCase):
    """Test cases for AlertConfig model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.config_data = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'smtp_username': 'test@test.com',
            'sender_email': 'test@test.com',
            'sender_name': 'Test System',
            'use_tls': True,
            'use_ssl': False,
            'disk_threshold': 80,
            'is_active': True
        }

    def test_create_alert_config(self):
        """Test creating alert configuration."""
        config = AlertConfig.objects.create(**self.config_data)
        self.assertEqual(config.smtp_server, 'smtp.test.com')
        self.assertEqual(config.smtp_port, 587)
        self.assertEqual(config.smtp_username, 'test@test.com')
        self.assertEqual(config.sender_email, 'test@test.com')
        self.assertEqual(config.sender_name, 'Test System')
        self.assertTrue(config.use_tls)
        self.assertFalse(config.use_ssl)
        self.assertEqual(config.disk_threshold, 80)
        self.assertTrue(config.is_active)

    def test_alert_config_str_representation(self):
        """Test alert config string representation."""
        config = AlertConfig.objects.create(**self.config_data)
        self.assertEqual(str(config), '告警配置 - smtp.test.com')

    def test_set_password_encryption(self):
        """Test password encryption."""
        config = AlertConfig.objects.create(**self.config_data)
        config.set_password('secret_smtp_password')
        config.save()
        
        # Verify password is encrypted
        self.assertNotEqual(config.smtp_password_encrypted, 'secret_smtp_password')
        self.assertTrue(len(config.smtp_password_encrypted) > 0)
        
        # Verify password can be decrypted
        decrypted = config.get_password()
        self.assertEqual(decrypted, 'secret_smtp_password')

    def test_get_password_reversibility(self):
        """Test that password encryption is reversible."""
        config = AlertConfig.objects.create(**self.config_data)
        original_password = 'my_smtp_password_123!@#'
        config.set_password(original_password)
        config.save()
        
        retrieved_password = config.get_password()
        self.assertEqual(retrieved_password, original_password)

    def test_password_with_special_characters(self):
        """Test password encryption with special characters."""
        config = AlertConfig.objects.create(**self.config_data)
        special_password = 'p@$$w0rd!#$%^&*()_+-=[]{}|;:,.<>?'
        config.set_password(special_password)
        config.save()
        
        retrieved_password = config.get_password()
        self.assertEqual(retrieved_password, special_password)

    def test_default_values(self):
        """Test default values for alert config."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.use_tls)
        self.assertFalse(config.use_ssl)
        self.assertEqual(config.disk_threshold, 80)
        self.assertTrue(config.is_active)
        self.assertEqual(config.sender_name, '巡检系统')

    def test_null_updated_by(self):
        """Test updated_by can be null."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com',
            updated_by=None
        )
        self.assertIsNone(config.updated_by)

    def test_disk_threshold_range(self):
        """Test disk threshold can be set to various values."""
        for threshold in [1, 50, 80, 99, 100]:
            config = AlertConfig.objects.create(
                smtp_server='smtp.test.com',
                smtp_username='test@test.com',
                sender_email='test@test.com',
                disk_threshold=threshold
            )
            self.assertEqual(config.disk_threshold, threshold)


class AlertRecipientModelTests(TestCase):
    """Test cases for AlertRecipient model."""

    def setUp(self):
        """Set up test data."""
        self.config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )

    def test_create_recipient(self):
        """Test creating alert recipient."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com',
            is_active=True
        )
        self.assertEqual(recipient.name, 'John Doe')
        self.assertEqual(recipient.email, 'john@example.com')
        self.assertTrue(recipient.is_active)
        self.assertEqual(recipient.config, self.config)

    def test_recipient_str_representation(self):
        """Test recipient string representation."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        self.assertEqual(str(recipient), 'John Doe <john@example.com>')

    def test_recipient_default_is_active(self):
        """Test recipient is_active defaults to True."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        self.assertTrue(recipient.is_active)

    def test_multiple_recipients_per_config(self):
        """Test multiple recipients can be created for one config."""
        recipient1 = AlertRecipient.objects.create(
            config=self.config,
            name='User 1',
            email='user1@example.com'
        )
        recipient2 = AlertRecipient.objects.create(
            config=self.config,
            name='User 2',
            email='user2@example.com'
        )
        
        self.assertEqual(self.config.recipients.count(), 2)
        self.assertIn(recipient1, self.config.recipients.all())
        self.assertIn(recipient2, self.config.recipients.all())

    def test_cascade_delete_config(self):
        """Test recipients are deleted when config is deleted."""
        AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        self.assertEqual(AlertRecipient.objects.count(), 1)
        
        self.config.delete()
        self.assertEqual(AlertRecipient.objects.count(), 0)

    def test_recipient_ordering_by_created_at(self):
        """Test recipients are ordered by created_at."""
        recipient1 = AlertRecipient.objects.create(
            config=self.config,
            name='First',
            email='first@example.com'
        )
        recipient2 = AlertRecipient.objects.create(
            config=self.config,
            name='Second',
            email='second@example.com'
        )
        
        recipients = list(AlertRecipient.objects.all())
        self.assertEqual(recipients[0], recipient1)
        self.assertEqual(recipients[1], recipient2)


class EncryptionKeyTests(TestCase):
    """Test cases for alert module encryption key generation."""

    def test_get_encryption_key_returns_bytes(self):
        """Test that get_encryption_key returns bytes."""
        key = get_encryption_key()
        self.assertIsInstance(key, bytes)

    def test_get_encryption_key_is_consistent(self):
        """Test that get_encryption_key returns consistent key."""
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        self.assertEqual(key1, key2)

    def test_encryption_key_same_as_servers(self):
        """Test that alert and server modules use same encryption key."""
        from apps.servers.models import get_encryption_key as server_get_key
        
        alert_key = get_encryption_key()
        server_key = server_get_key()
        self.assertEqual(alert_key, server_key)

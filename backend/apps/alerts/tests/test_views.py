"""Tests for alert views."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.alerts.models import AlertConfig, AlertRecipient


User = get_user_model()


class AlertConfigViewTests(TestCase):
    """Test cases for AlertConfigView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_get_config_not_exists(self):
        """Test getting config when none exists."""
        response = self.client.get('/api/alerts/config/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIsNone(response.data['data'])

    def test_get_config_exists(self):
        """Test getting existing config."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        
        response = self.client.get('/api/alerts/config/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['smtp_server'], 'smtp.test.com')

    def test_get_config_unauthenticated(self):
        """Test getting config without authentication."""
        self.client.credentials()
        response = self.client.get('/api/alerts/config/')
        self.assertEqual(response.status_code, 401)

    def test_create_config(self):
        """Test creating new config."""
        data = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'smtp_username': 'test@test.com',
            'smtp_password': 'secret123',
            'sender_email': 'test@test.com',
            'sender_name': 'Test System',
            'use_tls': True,
            'disk_threshold': 80
        }
        response = self.client.put(
            '/api/alerts/config/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '告警配置更新成功')
        self.assertEqual(AlertConfig.objects.count(), 1)

    def test_update_existing_config(self):
        """Test updating existing config."""
        config = AlertConfig.objects.create(
            smtp_server='old.smtp.com',
            smtp_username='old@test.com',
            sender_email='old@test.com'
        )
        
        data = {'smtp_server': 'new.smtp.com'}
        response = self.client.put(
            '/api/alerts/config/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['smtp_server'], 'new.smtp.com')
        
        config.refresh_from_db()
        self.assertEqual(config.smtp_server, 'new.smtp.com')

    def test_update_config_with_password(self):
        """Test updating config with new password."""
        config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        config.set_password('old_password')
        config.save()
        
        data = {'smtp_password': 'new_password'}
        response = self.client.put(
            '/api/alerts/config/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.get_password(), 'new_password')

    def test_update_config_invalid_data(self):
        """Test updating config with invalid data."""
        data = {'smtp_port': 70000}  # Invalid port
        response = self.client.put(
            '/api/alerts/config/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_update_config_invalid_threshold(self):
        """Test updating config with invalid threshold."""
        data = {'disk_threshold': 150}  # Invalid threshold
        response = self.client.put(
            '/api/alerts/config/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])


class AlertRecipientViewSetTests(TestCase):
    """Test cases for AlertRecipientViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        self.config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )

    def test_list_recipients_no_config(self):
        """Test listing recipients when no config exists."""
        AlertConfig.objects.all().delete()
        response = self.client.get('/api/alerts/recipients/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 0)

    def test_list_recipients_with_config(self):
        """Test listing recipients with config."""
        AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        
        response = self.client.get('/api/alerts/recipients/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_list_recipients_filters_by_config(self):
        """Test that recipients are filtered by config."""
        # Create recipient for first config
        AlertRecipient.objects.create(
            config=self.config,
            name='User 1',
            email='user1@example.com'
        )
        
        # Create second config and recipient
        config2 = AlertConfig.objects.create(
            smtp_server='smtp2.test.com',
            smtp_username='test2@test.com',
            sender_email='test2@test.com'
        )
        AlertRecipient.objects.create(
            config=config2,
            name='User 2',
            email='user2@example.com'
        )
        
        response = self.client.get('/api/alerts/recipients/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'User 1')

    def test_create_recipient_success(self):
        """Test creating recipient successfully."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'is_active': True
        }
        response = self.client.post(
            '/api/alerts/recipients/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '收件人添加成功')
        self.assertEqual(AlertRecipient.objects.count(), 1)

    def test_create_recipient_no_config(self):
        """Test creating recipient without config."""
        AlertConfig.objects.all().delete()
        
        data = {'name': 'John Doe', 'email': 'john@example.com'}
        response = self.client.post(
            '/api/alerts/recipients/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('请先配置告警邮箱', response.data['message'])

    def test_create_recipient_invalid_email(self):
        """Test creating recipient with invalid email."""
        data = {'name': 'John Doe', 'email': 'invalid_email'}
        response = self.client.post(
            '/api/alerts/recipients/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_create_recipient_missing_name(self):
        """Test creating recipient without name."""
        data = {'email': 'john@example.com'}
        response = self.client.post(
            '/api/alerts/recipients/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_update_recipient(self):
        """Test updating recipient."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='Old Name',
            email='old@example.com'
        )
        
        data = {'name': 'New Name', 'email': 'new@example.com'}
        response = self.client.patch(
            f'/api/alerts/recipients/{recipient.id}/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        recipient.refresh_from_db()
        self.assertEqual(recipient.name, 'New Name')
        self.assertEqual(recipient.email, 'new@example.com')

    def test_update_recipient_invalid_data(self):
        """Test updating recipient with invalid data."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        
        data = {'email': 'invalid_email'}
        response = self.client.patch(
            f'/api/alerts/recipients/{recipient.id}/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_delete_recipient(self):
        """Test deleting recipient."""
        recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='john@example.com'
        )
        
        response = self.client.delete(f'/api/alerts/recipients/{recipient.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(AlertRecipient.objects.count(), 0)

    def test_delete_nonexistent_recipient(self):
        """Test deleting non-existent recipient."""
        response = self.client.delete('/api/alerts/recipients/999/')
        self.assertEqual(response.status_code, 404)


class TestEmailViewTests(TestCase):
    """Test cases for TestEmailView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Create alert config for tests
        self.config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_username='test@test.com',
            sender_email='test@test.com'
        )
        self.config.set_password('password')
        self.config.save()

    @patch('apps.alerts.views.AlertService')
    def test_send_test_email_success(self, mock_service_class):
        """Test sending test email successfully."""
        mock_service = MagicMock()
        mock_service.send_test_email.return_value = True
        mock_service_class.return_value = mock_service
        
        data = {'recipient_email': 'test@example.com'}
        response = self.client.post(
            '/api/alerts/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '测试邮件发送成功')

    @patch('apps.alerts.views.AlertService')
    def test_send_test_email_failure(self, mock_service_class):
        """Test sending test email failure."""
        mock_service = MagicMock()
        mock_service.send_test_email.side_effect = Exception('SMTP Error')
        mock_service_class.return_value = mock_service
        
        data = {'recipient_email': 'test@example.com'}
        response = self.client.post(
            '/api/alerts/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn('SMTP Error', response.data['message'])

    def test_send_test_email_invalid_email(self):
        """Test sending test email with invalid email."""
        data = {'recipient_email': 'invalid_email'}
        response = self.client.post(
            '/api/alerts/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_send_test_email_missing_email(self):
        """Test sending test email without email."""
        data = {}
        response = self.client.post(
            '/api/alerts/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_send_test_email_unauthenticated(self):
        """Test sending test email without authentication."""
        self.client.credentials()
        data = {'recipient_email': 'test@example.com'}
        response = self.client.post(
            '/api/alerts/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)

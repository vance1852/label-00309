"""Tests for alert services."""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.alerts.models import AlertConfig, AlertRecipient
from apps.alerts.services import AlertService
from apps.servers.models import Server
from apps.inspections.models import InspectionRecord


User = get_user_model()


class AlertServiceTests(TestCase):
    """Test cases for AlertService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.service = AlertService()
        
        self.config = AlertConfig.objects.create(
            smtp_server='smtp.test.com',
            smtp_port=587,
            smtp_username='sender@test.com',
            sender_email='sender@test.com',
            sender_name='Test System',
            use_tls=True,
            use_ssl=False,
            is_active=True
        )
        self.config.set_password('smtp_password')
        self.config.save()
        
        self.recipient = AlertRecipient.objects.create(
            config=self.config,
            name='John Doe',
            email='recipient@example.com',
            is_active=True
        )
        
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )

    def test_get_config_returns_active_config(self):
        """Test get_config returns active configuration."""
        config = self.service.get_config()
        self.assertEqual(config, self.config)

    def test_get_config_no_active_config(self):
        """Test get_config returns None when no active config."""
        self.config.is_active = False
        self.config.save()
        
        config = self.service.get_config()
        self.assertIsNone(config)

    def test_get_config_no_config_exists(self):
        """Test get_config returns None when no config exists."""
        AlertConfig.objects.all().delete()
        config = self.service.get_config()
        self.assertIsNone(config)

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class):
        """Test sending email successfully."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        result = self.service.send_email(
            self.config,
            ['recipient@example.com'],
            'Test Subject',
            '<html><body>Test</body></html>'
        )
        
        self.assertTrue(result)
        mock_server.login.assert_called_once_with('sender@test.com', 'smtp_password')
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_email_with_tls(self, mock_smtp_class):
        """Test sending email with TLS."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        self.service.send_email(
            self.config,
            ['recipient@example.com'],
            'Test Subject',
            '<html>Test</html>'
        )
        
        mock_server.starttls.assert_called_once()

    @patch('apps.alerts.services.smtplib.SMTP_SSL')
    def test_send_email_with_ssl(self, mock_smtp_ssl_class):
        """Test sending email with SSL."""
        mock_server = MagicMock()
        mock_smtp_ssl_class.return_value = mock_server
        
        self.config.use_tls = False
        self.config.use_ssl = True
        self.config.save()
        
        self.service.send_email(
            self.config,
            ['recipient@example.com'],
            'Test Subject',
            '<html>Test</html>'
        )
        
        mock_smtp_ssl_class.assert_called_once_with('smtp.test.com', 587)
        mock_server.login.assert_called_once()

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_email_multiple_recipients(self, mock_smtp_class):
        """Test sending email to multiple recipients."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        self.service.send_email(
            self.config,
            recipients,
            'Test Subject',
            '<html>Test</html>'
        )
        
        call_args = mock_server.sendmail.call_args
        self.assertEqual(call_args[0][1], recipients)

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp_class):
        """Test sending email failure."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception('SMTP Error')
        mock_smtp_class.return_value = mock_server
        
        with self.assertRaises(Exception) as context:
            self.service.send_email(
                self.config,
                ['recipient@example.com'],
                'Test Subject',
                '<html>Test</html>'
            )
        
        self.assertIn('邮件发送失败', str(context.exception))

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_test_email_success(self, mock_smtp_class):
        """Test sending test email successfully."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        result = self.service.send_test_email('test@example.com')
        
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()

    def test_send_test_email_no_config(self):
        """Test sending test email without config."""
        AlertConfig.objects.all().delete()
        
        with self.assertRaises(Exception) as context:
            self.service.send_test_email('test@example.com')
        
        self.assertIn('未配置告警邮箱', str(context.exception))

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_alert_success(self, mock_smtp_class):
        """Test sending alert successfully."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={
                'disks': [
                    {
                        'filesystem': '/dev/sda1',
                        'size': '100G',
                        'used': '90G',
                        'available': '10G',
                        'use_percent': 90,
                        'mount_point': '/'
                    }
                ]
            },
            status='warning',
            has_alert=True
        )
        
        result = self.service.send_alert(self.server, record, 'Disk usage exceeds threshold')
        
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()

    def test_send_alert_no_config(self):
        """Test sending alert without config."""
        AlertConfig.objects.all().delete()
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        
        result = self.service.send_alert(self.server, record, 'Error message')
        
        self.assertFalse(result)

    def test_send_alert_no_active_recipients(self):
        """Test sending alert with no active recipients."""
        self.recipient.is_active = False
        self.recipient.save()
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        
        result = self.service.send_alert(self.server, record, 'Error message')
        
        self.assertFalse(result)

    def test_send_alert_no_recipients(self):
        """Test sending alert with no recipients at all."""
        AlertRecipient.objects.all().delete()
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        
        result = self.service.send_alert(self.server, record, 'Error message')
        
        self.assertFalse(result)

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_send_alert_inactive_config(self, mock_smtp_class):
        """Test sending alert with inactive config."""
        self.config.is_active = False
        self.config.save()
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        
        result = self.service.send_alert(self.server, record, 'Error message')
        
        self.assertFalse(result)
        mock_smtp_class.assert_not_called()

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_build_alert_body_contains_server_info(self, mock_smtp_class):
        """Test alert email body contains server information."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={
                'disks': [
                    {
                        'filesystem': '/dev/sda1',
                        'size': '100G',
                        'used': '90G',
                        'available': '10G',
                        'use_percent': 90,
                        'mount_point': '/'
                    }
                ]
            },
            status='warning',
            has_alert=True
        )
        
        result = self.service.send_alert(self.server, record, 'Disk usage exceeds threshold')
        
        # Verify email was sent successfully
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_build_alert_body_with_multiple_disks(self, mock_smtp_class):
        """Test alert email body with multiple disks."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={
                'disks': [
                    {
                        'filesystem': '/dev/sda1',
                        'size': '100G',
                        'used': '90G',
                        'available': '10G',
                        'use_percent': 90,
                        'mount_point': '/'
                    },
                    {
                        'filesystem': '/dev/sdb1',
                        'size': '200G',
                        'used': '180G',
                        'available': '20G',
                        'use_percent': 90,
                        'mount_point': '/data'
                    }
                ]
            },
            status='warning',
            has_alert=True
        )
        
        result = self.service.send_alert(self.server, record, 'Multiple disks exceed threshold')
        
        # Verify email was sent successfully
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()

    @patch('apps.alerts.services.smtplib.SMTP')
    def test_build_alert_body_disk_color_coding(self, mock_smtp_class):
        """Test alert email body has color coding for disk usage."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={
                'disks': [
                    {
                        'filesystem': '/dev/sda1',
                        'size': '100G',
                        'used': '50G',
                        'available': '50G',
                        'use_percent': 50,
                        'mount_point': '/'
                    },
                    {
                        'filesystem': '/dev/sdb1',
                        'size': '200G',
                        'used': '180G',
                        'available': '20G',
                        'use_percent': 90,
                        'mount_point': '/data'
                    }
                ]
            },
            status='warning',
            has_alert=True
        )
        
        result = self.service.send_alert(self.server, record, 'Disk alert')
        
        # Verify email was sent successfully
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()

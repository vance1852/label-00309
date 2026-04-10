import pytest
from unittest.mock import patch, MagicMock
from ..services import AlertService

pytestmark = pytest.mark.django_db

class TestAlertService:
    def test_get_config(self, alert_config):
        service = AlertService()
        config = service.get_config()
        assert config is not None
        assert config.smtp_server == 'smtp.example.com'

    def test_get_config_no_active(self, db):
        service = AlertService()
        config = service.get_config()
        assert config is None

    def test_send_alert_no_config(self, db, server, inspection_record):
        service = AlertService()
        result = service.send_alert(server, inspection_record, 'Test alert')
        assert result is False

    def test_send_alert_no_recipients(self, alert_config, server, inspection_record):
        service = AlertService()
        result = service.send_alert(server, inspection_record, 'Test alert')
        assert result is False

    def test_send_alert_success(self, alert_config, alert_recipient, server, inspection_record, mock_smtp):
        service = AlertService()
        result = service.send_alert(server, inspection_record, 'Test alert: / 90%')
        assert result is True
        mock_smtp['server'].login.assert_called_once()
        mock_smtp['server'].sendmail.assert_called_once()

    def test_send_alert_with_ssl(self, alert_config, alert_recipient, server, inspection_record, mock_smtp):
        alert_config.use_ssl = True
        alert_config.use_tls = False
        alert_config.save()
        
        service = AlertService()
        result = service.send_alert(server, inspection_record, 'Test alert')
        assert result is True

    def test_send_test_email_no_config(self, db):
        service = AlertService()
        with pytest.raises(Exception) as exc:
            service.send_test_email('test@example.com')
        assert '未配置告警邮箱' in str(exc.value)

    def test_send_test_email_success(self, alert_config, mock_smtp):
        service = AlertService()
        result = service.send_test_email('recipient@example.com')
        assert result is True
        mock_smtp['server'].login.assert_called_once()
        mock_smtp['server'].sendmail.assert_called_once()

    def test_send_email_smtp_exception(self, alert_config, alert_recipient, server, inspection_record):
        service = AlertService()
        with patch('smtplib.SMTP') as mock:
            mock.side_effect = Exception('SMTP connection failed')
            with pytest.raises(Exception) as exc:
                service.send_alert(server, inspection_record, 'Test alert')
            assert '邮件发送失败' in str(exc.value)

    def test_send_email_login_exception(self, alert_config, alert_recipient, server, inspection_record):
        service = AlertService()
        with patch('smtplib.SMTP') as mock:
            server_instance = MagicMock()
            mock.return_value = server_instance
            server_instance.login.side_effect = Exception('Login failed')
            
            with pytest.raises(Exception) as exc:
                service.send_alert(server, inspection_record, 'Test alert')
            assert '邮件发送失败' in str(exc.value)

    def test_build_alert_body(self, alert_config, server, inspection_record, user):
        service = AlertService()
        inspection_record.parsed_result = {
            'disks': [
                {'mount_point': '/', 'filesystem': '/dev/sda1', 'size': '100G', 'used': '90G', 'available': '10G', 'use_percent': 90},
                {'mount_point': '/data', 'filesystem': '/dev/sdb1', 'size': '500G', 'used': '200G', 'available': '300G', 'use_percent': 40}
            ]
        }
        body = service._build_alert_body(server, inspection_record, 'High disk usage')
        assert '磁盘告警通知' in body
        assert server.name in body
        assert '/' in body
        assert '/data' in body
        assert '90%' in body

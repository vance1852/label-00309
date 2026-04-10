import pytest
from ..models import AlertConfig, AlertRecipient, get_encryption_key

pytestmark = pytest.mark.django_db

class TestAlertConfigModel:
    def test_alert_config_creation(self, alert_config):
        assert alert_config.smtp_server == 'smtp.example.com'
        assert alert_config.smtp_port == 587
        assert alert_config.is_active is True

    def test_smtp_password_encryption(self, alert_config):
        original_password = 'smtp_password'
        assert alert_config.get_password() == original_password

    def test_alert_config_str_method(self, alert_config):
        assert 'smtp.example.com' in str(alert_config)

class TestAlertRecipientModel:
    def test_alert_recipient_creation(self, alert_recipient):
        assert alert_recipient.name == 'Recipient Name'
        assert alert_recipient.email == 'recipient@example.com'
        assert alert_recipient.is_active is True

    def test_alert_recipient_str_method(self, alert_recipient):
        expected_str = f"{alert_recipient.name} <{alert_recipient.email}>"
        assert str(alert_recipient) == expected_str

    def test_recipient_inactive(self, alert_recipient):
        alert_recipient.is_active = False
        alert_recipient.save()
        assert alert_recipient.is_active is False

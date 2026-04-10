import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db

class TestAlertConfigView:
    def test_get_config_authenticated(self, authenticated_client, alert_config):
        url = reverse('alert-config')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['smtp_server'] == 'smtp.example.com'

    def test_get_config_nonexistent(self, db, authenticated_client):
        url = reverse('alert-config')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'] is None

    def test_get_config_unauthenticated(self, api_client):
        url = reverse('alert-config')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_config(self, authenticated_client, alert_config, user):
        url = reverse('alert-config')
        data = {
            'smtp_server': 'smtp.newserver.com',
            'disk_threshold': 90
        }
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '告警配置更新成功'

    def test_create_config(self, db, authenticated_client, user):
        url = reverse('alert-config')
        data = {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_username': 'user@example.com',
            'smtp_password': 'password',
            'sender_email': 'sender@example.com',
            'disk_threshold': 85
        }
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert '告警配置更新成功' in response.data['message']

    def test_update_config_invalid(self, authenticated_client, alert_config):
        url = reverse('alert-config')
        data = {
            'smtp_port': 'invalid_port'
        }
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

class TestAlertRecipientViewSet:
    def test_list_recipients(self, authenticated_client, alert_recipient):
        url = reverse('recipient-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_list_recipients_no_config(self, db, authenticated_client):
        url = reverse('recipient-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 0

    def test_create_recipient_no_config(self, db, authenticated_client):
        url = reverse('recipient-list')
        data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False
        assert '请先配置告警邮箱' in response.data['message']

    def test_create_recipient_success(self, authenticated_client, alert_config):
        url = reverse('recipient-list')
        data = {
            'name': 'New Recipient',
            'email': 'new@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '收件人添加成功'

    def test_create_recipient_invalid(self, authenticated_client, alert_config):
        url = reverse('recipient-list')
        data = {}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_update_recipient(self, authenticated_client, alert_recipient):
        url = reverse('recipient-detail', kwargs={'pk': alert_recipient.pk})
        data = {
            'name': 'Updated Name'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '收件人更新成功'

    def test_delete_recipient(self, authenticated_client, alert_recipient):
        url = reverse('recipient-detail', kwargs={'pk': alert_recipient.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '收件人删除成功'

class TestEmailView:
    def test_send_test_email_success(self, authenticated_client, alert_config, mock_smtp):
        url = reverse('test-email')
        data = {
            'recipient_email': 'test@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '测试邮件发送成功'

    def test_send_test_email_no_config(self, db, authenticated_client):
        url = reverse('test-email')
        data = {
            'recipient_email': 'test@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_send_test_email_invalid_email(self, authenticated_client, alert_config):
        url = reverse('test-email')
        data = {
            'recipient_email': 'invalid_email'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] == False

    def test_send_test_email_smtp_exception(self, authenticated_client, alert_config):
        url = reverse('test-email')
        data = {
            'recipient_email': 'test@example.com'
        }
        with patch('smtplib.SMTP') as mock:
            mock.side_effect = Exception('SMTP server down')
            response = authenticated_client.post(url, data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] == False
            assert 'SMTP server down' in response.data['message']

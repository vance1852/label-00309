import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.servers.models import Server
from apps.alerts.models import AlertConfig, AlertRecipient
from apps.inspections.models import InspectionRecord
from apps.schedules.models import InspectionSchedule

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def server(db, user):
    server = Server.objects.create(
        name='Test Server',
        ip_address='192.168.1.1',
        port=22,
        ssh_username='root',
        description='Test description',
        is_active=True,
        created_by=user
    )
    server.set_password('testpassword')
    server.save()
    return server

@pytest.fixture
def mock_ssh_client():
    with patch('paramiko.SSHClient') as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        
        stdin = MagicMock()
        stdout = MagicMock()
        stderr = MagicMock()
        
        stdout.read.return_value = b""
        stderr.read.return_value = b""
        
        client_instance.exec_command.return_value = (stdin, stdout, stderr)
        
        yield mock

@pytest.fixture
def mock_ssh_connect_success(mock_ssh_client):
    yield mock_ssh_client

@pytest.fixture
def mock_ssh_auth_failure(mock_ssh_client):
    import paramiko
    mock_ssh_client.return_value.connect.side_effect = paramiko.AuthenticationException()
    yield mock_ssh_client

@pytest.fixture
def mock_ssh_exception(mock_ssh_client):
    import paramiko
    mock_ssh_client.return_value.connect.side_effect = paramiko.SSHException('Connection error')
    yield mock_ssh_client

@pytest.fixture
def mock_smtp():
    with patch('smtplib.SMTP') as mock_smtp, patch('smtplib.SMTP_SSL') as mock_smtp_ssl:
        server_instance = MagicMock()
        mock_smtp.return_value = server_instance
        mock_smtp_ssl.return_value = server_instance
        
        server_instance.login.return_value = None
        server_instance.sendmail.return_value = None
        server_instance.quit.return_value = None
        server_instance.starttls.return_value = None
        
        yield {'smtp': mock_smtp, 'smtp_ssl': mock_smtp_ssl, 'server': server_instance}

@pytest.fixture
def alert_config(db, user):
    config = AlertConfig.objects.create(
        smtp_server='smtp.example.com',
        smtp_port=587,
        smtp_username='test@example.com',
        sender_email='test@example.com',
        sender_name='Test Sender',
        use_tls=True,
        use_ssl=False,
        disk_threshold=80,
        is_active=True,
        updated_by=user
    )
    config.set_password('smtp_password')
    config.save()
    return config

@pytest.fixture
def alert_recipient(db, alert_config):
    return AlertRecipient.objects.create(
        config=alert_config,
        name='Recipient Name',
        email='recipient@example.com',
        is_active=True
    )

@pytest.fixture
def inspection_record(db, server, user):
    return InspectionRecord.objects.create(
        server=server,
        executed_by=user,
        command='df -h',
        raw_output='test output',
        parsed_result={'disks': []},
        status='success',
        has_alert=False,
        alert_message=None,
        is_scheduled=False
    )

@pytest.fixture
def inspection_schedule(db, user):
    return InspectionSchedule.objects.create(
        name='Daily Inspection',
        interval_type='daily',
        interval_value=1,
        inspection_command='df -h',
        is_active=True,
        updated_by=user
    )

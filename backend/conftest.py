"""Pytest configuration file."""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.conf import settings

settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
    'ATOMIC_REQUESTS': True,
}

django.setup()

from django.core.management import call_command

call_command('migrate', '--run-syncdb', verbosity=0)

import pytest


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    pass


@pytest.fixture
def api_client():
    """Return an API client fixture."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_user(db):
    """Return an authenticated user fixture."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, auth_user):
    """Return an authenticated API client fixture."""
    api_client.force_authenticate(user=auth_user)
    return api_client


@pytest.fixture
def test_server(db):
    """Return a test server fixture."""
    from apps.servers.models import Server
    server = Server.objects.create(
        name='Test Server',
        ip_address='192.168.1.1',
        port=22
    )
    server.set_password('testpass')
    server.save()
    return server

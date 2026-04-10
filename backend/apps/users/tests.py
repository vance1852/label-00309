"""Tests for users app."""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import User
from .serializers import LoginSerializer, UserSerializer, PasswordChangeSerializer


class UserModelTests(TestCase):
    """Test User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')


class UserSerializerTests(TestCase):
    """Test user serializers."""

    def test_login_serializer_valid(self):
        """Test login serializer with valid data."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = LoginSerializer(data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(serializer.is_valid())

    def test_login_serializer_invalid_password(self):
        """Test login serializer with invalid password."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = LoginSerializer(data={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertFalse(serializer.is_valid())

    def test_password_change_serializer_valid(self):
        """Test password change serializer valid."""
        serializer = PasswordChangeSerializer(data={
            'old_password': 'oldpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        self.assertTrue(serializer.is_valid())

    def test_password_change_serializer_mismatch(self):
        """Test password change serializer password mismatch."""
        serializer = PasswordChangeSerializer(data={
            'old_password': 'oldpass',
            'new_password': 'newpass123',
            'confirm_password': 'different'
        })
        self.assertFalse(serializer.is_valid())


class UserViewTests(APITestCase):
    """Test user views."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data'])

    def test_login_failure_invalid_credentials(self):
        """Test login failure with invalid credentials."""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_login_failure_missing_data(self):
        """Test login failure with missing data."""
        response = self.client.post('/api/auth/login/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_profile_view_authenticated(self):
        """Test profile view with authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'testuser')

    def test_profile_view_unauthenticated(self):
        """Test profile view without authentication."""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)
        response = self.client.put('/api/auth/password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password."""
        self.client.force_authenticate(user=self.user)
        response = self.client.put('/api/auth/password/', {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])

    def test_password_change_unauthenticated(self):
        """Test password change without authentication."""
        response = self.client.put('/api/auth/password/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_authenticated(self):
        """Test logout with authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/logout/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

"""Unit tests for core module."""
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, APIException
from django.http import Http404
from .response import success_response, error_response
from .exceptions import custom_exception_handler, get_error_message, BusinessException
from .pagination import StandardPagination


class ResponseUtilityTests(TestCase):
    """Tests for response utilities."""

    def test_success_response_default(self):
        """Test success_response with default values."""
        response = success_response()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'success')
        self.assertIsNone(response.data['data'])

    def test_success_response_with_data(self):
        """Test success_response with custom data and message."""
        data = {'key': 'value', 'items': [1, 2, 3]}
        response = success_response(data=data, message='Operation successful', code=201)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['code'], 201)
        self.assertEqual(response.data['message'], 'Operation successful')
        self.assertEqual(response.data['data'], data)

    def test_error_response_default(self):
        """Test error_response with default values."""
        response = error_response()
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['message'], 'error')
        self.assertIsNone(response.data['data'])

    def test_error_response_custom(self):
        """Test error_response with custom parameters."""
        data = {'errors': ['field1 is required']}
        response = error_response(message='Validation failed', code=422, data=data)
        
        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], 422)
        self.assertEqual(response.data['message'], 'Validation failed')
        self.assertEqual(response.data['data'], data)


class ExceptionHandlerTests(TestCase):
    """Tests for custom exception handler."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_error_message_with_detail(self):
        """Test get_error_message when data has detail key."""
        data = {'detail': 'Authentication credentials were not provided'}
        msg = get_error_message(data)
        self.assertEqual(msg, 'Authentication credentials were not provided')

    def test_get_error_message_dict_with_list_value(self):
        """Test get_error_message when dict value is a list."""
        data = {'username': ['This field is required', 'Another error']}
        msg = get_error_message(data)
        self.assertEqual(msg, 'username: This field is required')

    def test_get_error_message_dict_simple(self):
        """Test get_error_message for simple dict."""
        data = {'error': 'Something went wrong'}
        msg = get_error_message(data)
        self.assertEqual(msg, 'error: Something went wrong')

    def test_get_error_message_list(self):
        """Test get_error_message when data is a list."""
        data = ['First error', 'Second error']
        msg = get_error_message(data)
        self.assertEqual(msg, 'First error')

    def test_get_error_message_string(self):
        """Test get_error_message when data is a string."""
        data = 'Simple error message'
        msg = get_error_message(data)
        self.assertEqual(msg, 'Simple error message')

    def test_custom_exception_handler_validation_error(self):
        """Test custom_exception_handler for validation errors."""
        exc = ValidationError({'username': ['This field is required']})
        context = {'request': self.factory.get('/')}
        
        response = custom_exception_handler(exc, context)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('username', response.data['message'])
        self.assertIn('This field is required', response.data['message'])

    def test_custom_exception_handler_not_found(self):
        """Test custom_exception_handler for 404 errors."""
        exc = NotFound('Resource not found')
        context = {'request': self.factory.get('/')}
        
        response = custom_exception_handler(exc, context)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['code'], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Resource not found')

    def test_business_exception_initialization(self):
        """Test BusinessException creation."""
        exc = BusinessException('Custom business error', code=418)
        
        self.assertEqual(exc.message, 'Custom business error')
        self.assertEqual(exc.code, 418)
        self.assertEqual(str(exc), 'Custom business error')

    def test_business_exception_default_code(self):
        """Test BusinessException with default code."""
        exc = BusinessException('Something went wrong')
        
        self.assertEqual(exc.message, 'Something went wrong')
        self.assertEqual(exc.code, 400)


@pytest.mark.django_db
class PaginationTests(TestCase):
    """Tests for custom pagination classes."""

    def setUp(self):
        self.factory = RequestFactory()
        self.pagination = StandardPagination()

    def test_pagination_default_page_size(self):
        """Test default page size."""
        self.assertEqual(self.pagination.page_size, 10)
        self.assertEqual(self.pagination.max_page_size, 100)

    def test_get_page_size_from_query_param(self):
        """Test getting page size from query parameter."""
        request = self.factory.get('/api/data/?page_size=25')
        page_size = self.pagination.get_page_size(request)
        
        self.assertEqual(page_size, 25)

    def test_get_page_size_limited_by_max(self):
        """Test that page size is limited by max_page_size."""
        request = self.factory.get('/api/data/?page_size=200')
        page_size = self.pagination.get_page_size(request)
        
        self.assertEqual(page_size, 100)

    def test_get_paginated_response_format(self):
        """Test the format of paginated response."""
        from django.core.paginator import Paginator
        from django.core.paginator import Page
        
        items = ['item1', 'item2', 'item3', 'item4', 'item5']
        paginator = Paginator(items, 2)
        page = Page(items, 1, paginator)
        page.paginator = paginator
        
        self.pagination.page = page
        request = self.factory.get('/api/data/?page=1&page_size=5')
        self.pagination.request = request
        
        response = self.pagination.get_paginated_response(items)
        
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'success')
        self.assertEqual(response.data['data']['list'], items)
        self.assertEqual(response.data['data']['total'], 5)
        self.assertEqual(response.data['data']['page'], 1)
        self.assertEqual(response.data['data']['page_size'], 5)
        self.assertEqual(response.data['data']['total_pages'], 3)

"""Global exception handling."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF."""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'success': False,
            'code': response.status_code,
            'message': get_error_message(response.data),
            'data': None
        }
        response.data = custom_response
    else:
        logger.exception(f"Unhandled exception: {exc}")
        custom_response = {
            'success': False,
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': '服务器内部错误',
            'data': None
        }
        response = Response(custom_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


def get_error_message(data):
    """Extract error message from response data."""
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        for key, value in data.items():
            if isinstance(value, list):
                return f"{key}: {value[0]}"
            return f"{key}: {value}"
    if isinstance(data, list):
        return str(data[0])
    return str(data)


class BusinessException(Exception):
    """Custom business exception."""
    def __init__(self, message, code=400):
        self.message = message
        self.code = code
        super().__init__(message)

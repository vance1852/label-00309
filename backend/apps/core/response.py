"""Custom response utilities."""
from rest_framework.response import Response


def success_response(data=None, message='success', code=200):
    """Return a success response."""
    return Response({
        'success': True,
        'code': code,
        'message': message,
        'data': data
    })


def error_response(message='error', code=400, data=None):
    """Return an error response."""
    return Response({
        'success': False,
        'code': code,
        'message': message,
        'data': data
    }, status=code)

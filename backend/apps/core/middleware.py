"""Custom middleware."""
import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware to log all requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log request details
        user = getattr(request, 'user', None)
        username = user.username if user and user.is_authenticated else 'anonymous'
        
        logger.info(
            f"[{request.method}] {request.path} - "
            f"User: {username} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response

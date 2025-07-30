from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .utils import validate_token


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    JWT Authentication Middleware
    Equivalent to Go's Authenticate middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip authentication for certain paths
        skip_paths = [
            '/api/health/',
            '/api/health',
            '/admin/',
        ]
        
        # Check if current path should skip authentication
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return JsonResponse(
                {'error': 'Authorization header required'}, 
                status=401
            )
        
        # Split Bearer token
        token_parts = auth_header.split(' ')
        
        if len(token_parts) != 2 or token_parts[0] != 'Bearer':
            return JsonResponse(
                {'error': 'Invalid authorization header'}, 
                status=401
            )
        
        token = token_parts[1]
        
        # Get expected username
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        
        if not username:
            return JsonResponse(
                {'error': 'Username not configured'}, 
                status=500
            )
        
        # Validate token
        if not validate_token(token, username):
            return JsonResponse(
                {'error': 'Invalid token'}, 
                status=401
            )
        
        # Authentication successful, continue with request
        return None
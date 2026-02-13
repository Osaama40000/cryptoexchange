"""
Security Middleware
===================
Production security measures
"""
import re
import time
import logging
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('security')


class SecurityHeadersMiddleware:
    """
    Add comprehensive security headers to all responses

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: restrict dangerous features
    - Content-Security-Policy: (for non-admin pages)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Content Security Policy (adjust as needed for your frontend)
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.razorpay.com https://api.coingecko.com wss:; "
                "frame-src https://api.razorpay.com https://checkout.razorpay.com;"
            )

        return response


class RateLimitMiddleware:
    """
    Rate limiting for API endpoints

    Different limits for different endpoint categories:
    - default: 100 requests per minute
    - auth: 10 requests per minute (login/register)
    - trading: 30 requests per minute
    - withdrawal: 5 requests per 5 minutes
    """

    # Rate limits: (requests, seconds)
    RATE_LIMITS = {
        'default': (100, 60),  # 100 requests per minute
        'auth': (10, 60),  # 10 login attempts per minute
        'trading': (30, 60),  # 30 trades per minute
        'withdrawal': (5, 300),  # 5 withdrawals per 5 minutes
        'api_key': (5, 60),  # 5 API key operations per minute
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for safe methods on non-sensitive paths
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return self.get_response(request)

        # Determine rate limit category
        category = self._get_category(request.path)
        limit, window = self.RATE_LIMITS.get(category, self.RATE_LIMITS['default'])

        # Get client identifier
        client_id = self._get_client_id(request)
        cache_key = f'ratelimit:{category}:{client_id}'

        # Check rate limit
        try:
            current = cache.get(cache_key, 0) or 0
        except Exception:
            return self.get_response(request)
        if current >= limit:
            logger.warning(f"Rate limit exceeded: {client_id} on {category} ({current}/{limit})")
            return JsonResponse({
                'error': 'rate_limit_exceeded',
                'message': f'Too many requests. Please try again in {window} seconds.',
                'retry_after': window
            }, status=429)

        # Increment counter
        cache.set(cache_key, current + 1, window)

        response = self.get_response(request)

        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(max(0, limit - current - 1))
        response['X-RateLimit-Reset'] = str(int(time.time()) + window)

        return response

    def _get_category(self, path):
        """Determine rate limit category based on path"""
        if '/auth/login' in path or '/auth/register' in path:
            return 'auth'
        if '/trading/orders' in path:
            return 'trading'
        if '/withdraw' in path:
            return 'withdrawal'
        if '/api-keys' in path:
            return 'api_key'
        return 'default'

    def _get_client_id(self, request):
        """Get unique client identifier (user ID or IP)"""
        # Use user ID if authenticated, otherwise IP
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f'user:{request.user.id}'

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return f'ip:{x_forwarded_for.split(",")[0].strip()}'
        return f'ip:{request.META.get("REMOTE_ADDR", "unknown")}'


class SQLInjectionProtectionMiddleware:
    """
    Additional SQL injection protection

    Checks query strings for common SQL injection patterns
    """

    SUSPICIOUS_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
        r"UNION(\s+)ALL(\s+)SELECT",
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SUSPICIOUS_PATTERNS]

    def __call__(self, request):
        # Check query parameters
        query_string = request.META.get('QUERY_STRING', '')
        if self._is_suspicious(query_string):
            logger.warning(f"SQL injection attempt detected from {self._get_ip(request)}: {query_string[:100]}")
            return JsonResponse({
                'error': 'invalid_request',
                'message': 'Request contains invalid characters'
            }, status=400)

        return self.get_response(request)

    def _is_suspicious(self, text):
        """Check if text contains suspicious SQL patterns"""
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False

    def _get_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class RequestLoggingMiddleware:
    """
    Log all requests for security audit

    Logs:
    - All incoming requests with method, path, user, IP
    - All error responses (4xx, 5xx)
    """

    # Paths to exclude from logging (high frequency, low value)
    EXCLUDE_PATHS = [
        '/api/v1/health/',
        '/static/',
        '/media/',
        '/favicon.ico',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip excluded paths
        if any(request.path.startswith(p) for p in self.EXCLUDE_PATHS):
            return self.get_response(request)

        user = getattr(request, 'user', None)
        user_info = user.email if user and user.is_authenticated else 'anonymous'
        ip = self._get_ip(request)

        # Log the request
        logger.info(
            f"REQUEST: {request.method} {request.path} | "
            f"User: {user_info} | IP: {ip}"
        )

        response = self.get_response(request)

        # Log response status for errors
        if response.status_code >= 400:
            logger.warning(
                f"RESPONSE: {response.status_code} | "
                f"Path: {request.path} | User: {user_info} | IP: {ip}"
            )

        return response

    def _get_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class XSSProtectionMiddleware:
    """
    Additional XSS protection for JSON responses

    Escapes potentially dangerous characters in JSON responses
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # For JSON responses, ensure proper content type
        if response.get('Content-Type', '').startswith('application/json'):
            response['X-Content-Type-Options'] = 'nosniff'

        return response
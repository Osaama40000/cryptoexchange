"""
Django Development Settings
"""

from .base import *

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# =============================================================================
# CORS - Allow all in development
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# REST FRAMEWORK - Add browsable API
# =============================================================================
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# =============================================================================
# JWT - Longer tokens for development
# =============================================================================
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)

# =============================================================================
# SECURITY - Relaxed for development
# =============================================================================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

print("✅ Development settings loaded")
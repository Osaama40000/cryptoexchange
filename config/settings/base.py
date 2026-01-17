"""
Django Base Settings for CryptoExchange Demo
============================================
"""

import os
from datetime import timedelta
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
load_dotenv()

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# CORE SETTINGS
# =============================================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-this')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
SITE_ID = 1

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================
DJANGO_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.wallets',
    'apps.trading',
    'apps.blockchain',
    'apps.audit',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# =============================================================================
# TEMPLATES
# =============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =============================================================================
# ASGI / WSGI
# =============================================================================
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# =============================================================================
# DATABASE - PostgreSQL
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'cryptoexchange'),
        'USER': os.getenv('DB_USER', 'exchange_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'exchange_dev_password_2024'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 60,
    }
}

# =============================================================================
# REDIS & CACHE
# =============================================================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'cryptoex',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# =============================================================================
# CHANNELS (WebSocket)
# =============================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# =============================================================================
# CUSTOM USER MODEL
# =============================================================================
AUTH_USER_MODEL = 'accounts.User'

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# CORS
# =============================================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# API DOCUMENTATION
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'CryptoExchange Demo API',
    'DESCRIPTION': 'Demo cryptocurrency exchange API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# =============================================================================
# CELERY
# =============================================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# EMAIL
# =============================================================================
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# =============================================================================
# BLOCKCHAIN CONFIGURATION
# =============================================================================
BLOCKCHAIN_CONFIG = {
    'ACTIVE_CHAIN_ID': int(os.getenv('ACTIVE_CHAIN_ID', '11155111')),
    'ACTIVE_RPC_URL': os.getenv('ACTIVE_RPC_URL', ''),
    'MIN_CONFIRMATIONS': int(os.getenv('MIN_CONFIRMATIONS', '12')),
    'WALLETCONNECT_PROJECT_ID': os.getenv('WALLETCONNECT_PROJECT_ID', ''),
    'NETWORKS': {
        1: {
            'name': 'Ethereum Mainnet',
            'rpc_url': os.getenv('ETH_MAINNET_RPC_URL', ''),
            'explorer': 'https://etherscan.io',
            'is_testnet': False,
        },
        11155111: {
            'name': 'Sepolia Testnet',
            'rpc_url': os.getenv('ETH_SEPOLIA_RPC_URL', ''),
            'explorer': 'https://sepolia.etherscan.io',
            'is_testnet': True,
        },
    },
}

# =============================================================================
# EXCHANGE CONFIGURATION
# =============================================================================
EXCHANGE_CONFIG = {
    'DEMO_MODE': os.getenv('DEMO_MODE', 'True').lower() in ('true', '1', 'yes'),
    'DEMO_BANNER_TEXT': os.getenv('DEMO_BANNER_TEXT', '⚠️ DEMO MODE'),
    'DEFAULT_MAKER_FEE': 0.001,
    'DEFAULT_TAKER_FEE': 0.001,
    'WITHDRAWAL_AUTO_APPROVE_LIMIT': float(os.getenv('WITHDRAWAL_AUTO_APPROVE_LIMIT', '100')),
}

# =============================================================================
# SECURITY
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# =============================================================================
# LOGGING
# =============================================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
"""Django settings for reusable Unfold boilerplate.

BabyTime + DoctorAI patterns, hardened:
- PostgreSQL default
- Unfold first in INSTALLED_APPS
- phone + OTP auth with SimpleJWT
- DRF throttling, CORS, Channels
- MinIO S3-compatible media storage
- Docker/Coolify-ready security defaults
"""

from datetime import timedelta
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = env_bool('DEBUG', True)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'unfold-boilerplate-dev-secret-key-change-me'
    else:
        raise ImproperlyConfigured('SECRET_KEY environment variable must be set in production')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1,10.0.2.2,0.0.0.0')
if not DEBUG and ('*' in ALLOWED_HOSTS or not ALLOWED_HOSTS):
    raise ImproperlyConfigured('Production ALLOWED_HOSTS must be explicit and must not include *')

ENABLE_HTTPS_REDIRECT = env_bool('ENABLE_HTTPS_REDIRECT', False)
SECURE_REDIRECT_EXEMPT = [r'^api/health/$']
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')

if not DEBUG and ENABLE_HTTPS_REDIRECT:
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_HSTS_SECONDS = 0
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

INSTALLED_APPS = [
    # Unfold must be before django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',

    'core',
    'messaging',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# PostgreSQL only.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'unfold_boilerplate_db'),
        'USER': os.environ.get('DB_USER', 'unfold_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }
}

AUTH_USER_MODEL = 'core.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
LANGUAGES = [
    ('uz', _("O'zbek tili")),
    ('en', _('English')),
    ('ru', _('Rus tili')),
]
DEFAULT_LANGUAGE = 'uz'
TIME_ZONE = os.environ.get('TZ', 'Asia/Tashkent')
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', str(10 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', str(5 * 1024 * 1024)))

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('DRF_THROTTLE_ANON', '100/hour'),
        'user': os.environ.get('DRF_THROTTLE_USER', '1000/hour'),
        'otp': os.environ.get('DRF_THROTTLE_OTP', '5/minute'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'config.exception_handlers.localized_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_MINUTES', '30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_DAYS', '30'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'UPDATE_LAST_LOGIN': True,
}

_default_csrf_origins = {
    'http://localhost:8000', 'https://localhost:8000',
    'http://127.0.0.1:8000', 'https://127.0.0.1:8000',
    'http://0.0.0.0:8000', 'https://0.0.0.0:8000',
}
CSRF_TRUSTED_ORIGINS = sorted(_default_csrf_origins | set(env_list('CSRF_TRUSTED_ORIGINS')))

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True

REDIS_URL = os.environ.get('REDIS_URL', '')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}
    }

OTP_LENGTH = int(os.environ.get('OTP_LENGTH', '5'))
OTP_DEFAULT_CODE = os.environ.get('OTP_DEFAULT_CODE', '11111')
OTP_EXPIRY_SECONDS = int(os.environ.get('OTP_EXPIRY_SECONDS', '120'))
OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get('OTP_RESEND_COOLDOWN_SECONDS', '60'))
OTP_MAX_DAILY_PER_PHONE = int(os.environ.get('OTP_MAX_DAILY_PER_PHONE', '9999' if DEBUG else '5'))
OTP_MAX_VERIFY_ATTEMPTS = int(os.environ.get('OTP_MAX_VERIFY_ATTEMPTS', '3'))
SMS_BACKEND = os.environ.get('SMS_BACKEND', 'console')

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000').rstrip('/')
USE_MINIO = env_bool('USE_MINIO', False)
FORCE_MINIO_IN_DEBUG = env_bool('FORCE_MINIO_IN_DEBUG', False)
if DEBUG and USE_MINIO and not FORCE_MINIO_IN_DEBUG:
    USE_MINIO = False

if USE_MINIO:
    from botocore.config import Config

    def _normalize_endpoint(value: str) -> str:
        value = (value or '').strip()
        if value.startswith('https://'):
            value = value[len('https://'):]
        elif value.startswith('http://'):
            value = value[len('http://'):]
        return value.rstrip('/')

    MINIO_ENDPOINT = _normalize_endpoint(os.environ.get('MINIO_ENDPOINT', 'localhost:9000'))
    MINIO_INTERNAL_ENDPOINT = _normalize_endpoint(os.environ.get('MINIO_INTERNAL_ENDPOINT', MINIO_ENDPOINT))
    MINIO_ROOT_USER = os.environ.get('MINIO_ROOT_USER', 'minioadmin')
    MINIO_ROOT_PASSWORD = os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin')
    MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'unfold-boilerplate')
    MINIO_USE_HTTPS = env_bool('MINIO_USE_HTTPS', False)
    MINIO_INTERNAL_USE_HTTPS = env_bool('MINIO_INTERNAL_USE_HTTPS', MINIO_USE_HTTPS)
    MINIO_REGION = os.environ.get('MINIO_REGION', 'us-east-1')

    _minio_scheme = 'https' if MINIO_USE_HTTPS else 'http'
    _minio_internal_scheme = 'https' if MINIO_INTERNAL_USE_HTTPS else 'http'

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'access_key': MINIO_ROOT_USER,
                'secret_key': MINIO_ROOT_PASSWORD,
                'bucket_name': MINIO_BUCKET_NAME,
                'endpoint_url': f'{_minio_internal_scheme}://{MINIO_INTERNAL_ENDPOINT}',
                'region_name': MINIO_REGION,
                'file_overwrite': False,
                'default_acl': None,
                'querystring_auth': False,
                'url_protocol': f'{_minio_scheme}:',
                'custom_domain': f'{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}',
                'client_config': Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
    MEDIA_URL = f'{_minio_scheme}://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/'

FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
FIREBASE_CREDENTIALS_JSON = os.environ.get('FIREBASE_CREDENTIALS_JSON', '')
FIREBASE_CREDENTIALS_BASE64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64', '')
FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', '')

UNFOLD = {
    'SITE_TITLE': _('Unfold Boilerplate Admin'),
    'SITE_HEADER': _('Unfold Boilerplate'),
    'SITE_SYMBOL': 'dashboard',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': _('Foydalanuvchilar'),
                'separator': False,
                'items': [
                    {'title': _('Foydalanuvchilar'), 'icon': 'people', 'link': '/admin/core/user/'},
                    {'title': _('OTP kodlar'), 'icon': 'pin', 'link': '/admin/core/otpverification/'},
                    {'title': _('Qurilma tokenlari'), 'icon': 'devices', 'link': '/admin/core/devicetoken/'},

                ],
            },
            {
                'title': _('Xabarlar'),
                'separator': True,
                'items': [
                    {'title': _('Suhbatlar'), 'icon': 'chat', 'link': '/admin/messaging/conversation/'},
                    {'title': _('Xabarlar'), 'icon': 'message', 'link': '/admin/messaging/message/'},
                    {'title': _('Bildirishnomalar'), 'icon': 'notifications', 'link': '/admin/core/notification/'},
                    {'title': _('Bildirishnoma sozlamalari'), 'icon': 'tune', 'link': '/admin/core/notificationsettings/'},

                ],
            },
            {
                'title': _('Sozlamalar'),
                'separator': True,
                'items': [
                    {'title': _('App Config'), 'icon': 'settings', 'link': '/admin/core/appconfig/'},

                ],
            },
        ],
    },
}

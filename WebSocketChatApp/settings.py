import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'insecure-secret-key')

# Toggle builtin username/password auth for development.
USE_DEV_AUTH = os.getenv('USE_DEV_AUTH', 'False').lower() in ('true', '1', 'yes')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host]

LOGIN_URL = '/accounts/login/' if USE_DEV_AUTH else 'login'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.openid_connect',
    'djangosaml2',
    'django_scim',
    'channels',
    'csp',
    'rest_framework',
    'drf_spectacular',
    'ChatApp',
]

MIDDLEWARE = [
    'django_ratelimit.middleware.RatelimitMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

RATELIMIT_USE_REQUEST_HEADER = True

ROOT_URLCONF = 'WebSocketChatApp.urls'
SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'WebSocketChatApp.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'chatapp'),
        'USER': os.getenv('MYSQL_USER', 'chatapp'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'chatapppassword'),
        'HOST': os.getenv('MYSQL_HOST', 'chatapp-db'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'unix_socket': os.getenv('MYSQL_UNIX_SOCKET', '/var/run/mysqld/mysqld.sock'),
        },
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'static_files'

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'ChatApp.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SAML_CONFIG_PATH = os.getenv('SAML_CONFIG_PATH')
SAML_CONFIG = {}
if SAML_CONFIG_PATH and os.path.exists(SAML_CONFIG_PATH):
    import json
    with open(SAML_CONFIG_PATH) as fh:
        SAML_CONFIG = json.load(fh)

SCIM_BEARER_TOKEN = os.getenv('SCIM_BEARER_TOKEN', 'changeme')
ENTERPRISE_LICENSE_KEY = os.getenv('ENTERPRISE_LICENSE_KEY', '')

SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'SERVERS': {
            'default': {
                'CLIENT_ID': os.getenv('OIDC_CLIENT_ID'),
                'CLIENT_SECRET': os.getenv('OIDC_CLIENT_SECRET'),
                'SERVER_URL': os.getenv('OIDC_SERVER_URL', ''),
            }
        }
    }
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'

# Redis and Routing

ASGI_APPLICATION = "WebSocketChatApp.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                os.getenv("REDIS_HOST", "127.0.0.1"),
                int(os.getenv("REDIS_PORT", 6379)),
            )],
        },
    },
}

# Security hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '0' if DEBUG else '3600'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin]

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_REPORT_ONLY = os.getenv('CSP_REPORT_ONLY', 'False').lower() in ('true', '1', 'yes')

# Maximum allowed characters in a chat message
MESSAGE_MAX_LENGTH = int(os.getenv('MESSAGE_MAX_LENGTH', '500'))

# Base64 encoded key used for BYOK encryption of group chats
MESSAGE_ENCRYPTION_KEY = os.getenv('MESSAGE_ENCRYPTION_KEY')

# AWS KMS CMK used to envelope-encrypt tenant keys (Slack EKM pattern)
KMS_KEY_ID = os.getenv('KMS_KEY_ID')

# Import path to a callable used for DLP checks before sending messages
DLP_BEFORE_SEND_HOOK = os.getenv(
    'DLP_BEFORE_SEND_HOOK', 'ChatApp.dlp.default_dlp_callback'
)

# Retention hierarchy defaults
ORG_RETENTION_DAYS = int(os.getenv('ORG_RETENTION_DAYS', '30'))
WORKSPACE_RETENTION_DAYS = int(os.getenv('WORKSPACE_RETENTION_DAYS', str(ORG_RETENTION_DAYS)))

# S3 export settings
EXPUNGE_S3_BUCKET = os.getenv('EXPUNGE_S3_BUCKET')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Default TTL (in seconds) for ephemeral messages
EPHEMERAL_MESSAGE_TTL = int(os.getenv('EPHEMERAL_MESSAGE_TTL', '30'))

# Enforce two-factor authentication during login
TOTP_ENFORCE = os.getenv('TOTP_ENFORCE', 'True') == 'True'

# Kafka broker for audit log streaming
KAFKA_BROKER_URL = os.getenv('KAFKA_BROKER_URL')

# Push notification settings
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY')
APNS_CERT_FILE = os.getenv('APNS_CERT_FILE')
APNS_TOPIC = os.getenv('APNS_TOPIC')
APNS_USE_SANDBOX = os.getenv('APNS_USE_SANDBOX', 'True').lower() in ('true', '1', 'yes')

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://{os.getenv("REDIS_HOST", "127.0.0.1")}:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
from datetime import timedelta
CELERY_BEAT_SCHEDULE = {
    'purge_expired_messages': {
        'task': 'ChatApp.tasks.purge_expired_messages',
        'schedule': timedelta(seconds=int(os.getenv('PURGE_EXPIRED_INTERVAL', '60'))),
    },
}

# Logging

LOGGING_DIR = BASE_DIR / 'logs'
LOG_JSON = os.getenv('LOG_JSON', 'False').lower() in ('true', '1', 'yes')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': str(LOGGING_DIR / 'logging.log'),
            'formatter': 'json' if LOG_JSON else 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if LOG_JSON else 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'ChatApp': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

from .settings import *

DEBUG = True
USE_DEV_AUTH = True

# Use in-memory channel layer to avoid external Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Disable heavyweight enterprise integrations
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None
KAFKA_BROKER_URL = None
ENABLE_DLP = False
USE_KMS = False
TOTP_ENFORCE = False

# Remove external-service configs
SAML_CONFIG_PATH = None
EXPUNGE_S3_BUCKET = None
FCM_SERVER_KEY = None
APNS_CERT_FILE = None

# Relax security for a public demo
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
CSRF_TRUSTED_ORIGINS = []

ALLOWED_HOSTS = ["*"]
WEBSOCKET_ALLOWED_ORIGINS = ["*"]

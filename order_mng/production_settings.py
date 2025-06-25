"""
Production settings for Railway deployment
"""
import os
import dj_database_url
from .settings import *

# SECURITY SETTINGS
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key-for-build')
ALLOWED_HOSTS = [
    '.railway.app',      # Railway domains
    '.herokuapp.com',
    'localhost',
    '127.0.0.1'
]

# DATABASE (Railway PostgreSQL)
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# STATIC FILES (Railway requirement)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# CHANNELS/WEBSOCKET (Redis on Railway)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

# HTTPS Settings for Railway
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
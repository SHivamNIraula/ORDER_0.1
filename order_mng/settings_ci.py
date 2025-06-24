# CI/CD Settings for GitHub Actions
from .settings import *

# Override database for CI
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for tests
    }
}

# Disable Redis/Channels for CI
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Simple static files for CI
STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/static/'

# Disable media files for CI
MEDIA_URL = '/media/'
MEDIA_ROOT = '/tmp/media/'

# Security settings for CI
SECRET_KEY = 'ci-test-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Disable email for CI
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
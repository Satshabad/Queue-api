import os.path

from sentry.conf.server import *

ROOT = os.path.dirname(__file__)

DATABASES = {
    'default': {
        # We use the PostgreSQL database we created earlier
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': "db_sentry",
        'USER': 'pg_sentry',
        'PASSWORD': 'password',
        'HOST': 'localhost',
    }
}

SENTRY_KEY = '0123456789abcde'

# Set this to false to require authentication
SENTRY_PUBLIC = True
SENTRY_ALLOW_REGISTRATION = True

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = 9000

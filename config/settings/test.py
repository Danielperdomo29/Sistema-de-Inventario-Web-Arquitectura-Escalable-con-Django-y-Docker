"""
Configuración para testing.
Usa SQLite en memoria y caché local para tests rápidos sin dependencias externas.
"""

from .base import *

# Testing
DEBUG = True
TESTING = True

# Hosts permitidos para tests
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Database en memoria para tests rápidos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Caché en memoria local (no requiere Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session en caché (local para tests)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Email backend para testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Password hashers más rápidos para testing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Desactivar CSP en tests para evitar problemas
CSP_DEFAULT_SRC = None
CSP_SCRIPT_SRC = None
CSP_STYLE_SRC = None


# Desactivar migraciones en tests para velocidad
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()


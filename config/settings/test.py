"""
Configuración para testing.
"""

from .base import *

# Testing
DEBUG = True
TESTING = True

# Database en memoria para tests rápidos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Email backend para testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Password hashers más rápidos para testing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


# Desactivar migraciones en tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

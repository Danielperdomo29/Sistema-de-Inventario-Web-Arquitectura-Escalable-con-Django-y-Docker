"""
Configuración para desarrollo.
"""
from .base import *

# Debug
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Email backend para desarrollo (imprime en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Desactivar protecciones estrictas en desarrollo
if ENABLE_ALLAUTH:
    ACCOUNT_EMAIL_VERIFICATION = 'optional'  # No obligatorio en desarrollo

# Logging simple para desarrollo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

"""
Configuración base del proyecto.
Copia del settings.py actual + configuraciones de allauth (desactivadas por defecto).
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "mi-clave-secreta-super-segura")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
    "app.fiscal.apps.FiscalConfig",  # Fiscal module
    "facturacion",
]

# Feature flag: Activar django-allauth
ENABLE_ALLAUTH = True # Force enabled for Phase 5

if ENABLE_ALLAUTH:
    INSTALLED_APPS += [
        # Django Sites Framework (required for allauth)
        "django.contrib.sites",
        # Django-allauth
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        # Django-OTP (2FA)
        "django_otp",
        "django_otp.plugins.otp_totp",
        "django_otp.plugins.otp_static",
        "allauth_2fa",
        # Crispy Forms for better form rendering
        "crispy_forms",
        "crispy_bootstrap5",
        # Security
        "corsheaders",
        "csp",
    ]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Debe ser primero
    "csp.middleware.CSPMiddleware",  # Content Security Policy
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware", # 2FA Middleware
    "app.middleware.auth_sync.AuthSyncMiddleware",  # Sincronización de permisos
    "app.fiscal.middleware.FiscalAuditMiddleware",  # Auditoría Fiscal
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if ENABLE_ALLAUTH:
    # Allauth middleware (required for allauth >= 0.60)
    MIDDLEWARE.append("allauth.account.middleware.AccountMiddleware")


# ============================================================================
# SECURITY HEADERS (OWASP Best Practices)
# ============================================================================

# HTTPS/SSL (Forzar en producción)
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (HTTP Strict Transport Security) - 1 año
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies seguras
SESSION_COOKIE_SECURE = not DEBUG  # Solo HTTPS en producción
SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript
SESSION_COOKIE_SAMESITE = "Lax"  # Protección CSRF
SESSION_COOKIE_NAME = "__Host-sessionid" if not DEBUG else "sessionid"

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # Debe ser False para AJAX (JavaScript necesita leer el token)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "__Host-csrftoken" if not DEBUG else "csrftoken"

# X-Frame-Options (Clickjacking protection)
X_FRAME_OPTIONS = "DENY"

# X-Content-Type-Options (MIME sniffing protection)
SECURE_CONTENT_TYPE_NOSNIFF = True

# X-XSS-Protection (XSS filter)
SECURE_BROWSER_XSS_FILTER = True

# Referrer Policy
SECURE_REFERRER_POLICY = "same-origin"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            str(BASE_DIR / "app" / "views" / "templates"),
            str(BASE_DIR / "templates"),  # Para templates de allauth
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
from dotenv import load_dotenv

load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "danielper29"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "connect_timeout": 30,
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ============================================================================
# PASSWORD HASHING (Argon2 - más seguro que PBKDF2)
# ============================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # Más seguro
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # Fallback
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "app" / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "app.UserAccount"

# Session
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================================================
# CORS CONFIGURATION (Restrictivo por defecto)
# ============================================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

CORS_ALLOW_CREDENTIALS = True

# Headers permitidos
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Métodos permitidos
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# No permitir todos los orígenes (seguridad)
CORS_ALLOW_ALL_ORIGINS = False

# ============================================================================
# CONTENT SECURITY POLICY (CSP)
# ============================================================================
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Solo para desarrollo, usar nonces en producción
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://cdnjs.cloudflare.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # Prevenir clickjacking
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# ============================================================================
# DJANGO-ALLAUTH CONFIGURATION (Solo si ENABLE_ALLAUTH=True)
# ============================================================================

if ENABLE_ALLAUTH:
    # ========================================================================
    # Authentication Backends
    # ========================================================================
    AUTHENTICATION_BACKENDS = [
        # Django ModelBackend (permite login por username en admin)
        "django.contrib.auth.backends.ModelBackend",
        # Allauth authentication backend (permite login por email)
        "allauth.account.auth_backends.AuthenticationBackend",
    ]

    # ========================================================================
    # Site Configuration (Required for allauth)
    # ========================================================================
    SITE_ID = 1

    # ========================================================================
    # Allauth Account Settings
    # ========================================================================

    # Método de autenticación: username o email (dual login)
    ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # Permite ambos

    # Email es requerido para registro
    ACCOUNT_EMAIL_REQUIRED = True

    # Verificación de email OBLIGATORIA (best practice de seguridad)
    ACCOUNT_EMAIL_VERIFICATION = os.getenv("ENABLE_EMAIL_VERIFICATION", "mandatory")

    # Email debe ser único
    ACCOUNT_UNIQUE_EMAIL = True

    # Username es requerido para dual login (username_email)
    ACCOUNT_USERNAME_REQUIRED = True
    ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"

    # Logout sin confirmación (mejor UX)
    ACCOUNT_LOGOUT_ON_GET = True

    # Recordar sesión por defecto
    ACCOUNT_SESSION_REMEMBER = True

    # Pedir contraseña dos veces en registro (prevenir errores)
    ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

    # Prevenir enumeración de usuarios (seguridad)
    ACCOUNT_PREVENT_ENUMERATION = True

    # Rate limiting para prevenir abuso
    ACCOUNT_RATE_LIMITS = {
        # Rate limiting disabled due to parser error (Invalid duration unit)
        # "login_failed": "5/5m",
        # "signup": "20/60m",
        # "password_reset": "10/60m",
        # "change_password": "5/5m",
        # "email_management": "10/60m",
    }

    # Tiempo de expiración de confirmación de email (3 días)
    ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

    # Tiempo de expiración de token de reset de contraseña (1 día)
    ACCOUNT_PASSWORD_RESET_TOKEN_EXPIRE_DAYS = 1

    # Longitud mínima de contraseña
    ACCOUNT_PASSWORD_MIN_LENGTH = 8

    # Formato de display del usuario
    ACCOUNT_USER_DISPLAY = lambda user: user.email

    # ========================================================================
    # Login/Logout URLs
    # ========================================================================
    LOGIN_REDIRECT_URL = "/"  # Dashboard principal
    LOGIN_URL = "/accounts/login/"
    LOGOUT_REDIRECT_URL = "/accounts/login/"

    # Redirección después de signup
    ACCOUNT_SIGNUP_REDIRECT_URL = "/"

    # ========================================================================
    # Custom Adapters
    # ========================================================================
    ACCOUNT_ADAPTER = "app.adapters.account_adapter.CustomAccountAdapter"

    # ========================================================================
    # Crispy Forms Configuration
    # ========================================================================
    CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
    CRISPY_TEMPLATE_PACK = "bootstrap5"

    # ========================================================================
    # Email Configuration
    # ========================================================================
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.getenv(
        "DEFAULT_FROM_EMAIL", "Sistema de Inventario <noreply@inventario.com>"
    )
    SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

    # Timeout para conexiones SMTP
    EMAIL_TIMEOUT = 10

    # ========================================================================
    # Security Settings (Best Practices)
    # ========================================================================

    # Prevenir ataques de timing en login
    # Rate limiting configuration (Allauth 0.50+)
    ACCOUNT_RATE_LIMITS = {
        'login_failed': '5/5m',      # 5 intentos en 5 minutos
        'signup': '10/1h',           # 10 registros por hora
        'password_reset': '5/1h',    # 5 restablecimientos de contraseña por hora
    }
    
    # Desactivar en entorno de desarrollo
    if DEBUG:
        ACCOUNT_RATE_LIMITS = {}

    # Forzar lowercase en emails
    ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Sistema de Inventario] "

    # Confirmar email antes de cambiar
    ACCOUNT_CHANGE_EMAIL = True
    ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/"

    # Adapters personalizados (para lógica custom)
    # ACCOUNT_ADAPTER = 'app.adapters.CustomAccountAdapter'
    # SOCIALACCOUNT_ADAPTER = 'app.adapters.CustomSocialAccountAdapter'

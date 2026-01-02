import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
SECRET_KEY = "mi-clave-secreta-super-segura"
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "app", "views", "templates"),
            os.path.join(BASE_DIR, "templates"),
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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Required for auth
    "django.contrib.messages.middleware.MessageMiddleware",  # Required for admin
    "allauth.account.middleware.AccountMiddleware", # Phase 5
]

# Load env vars
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
        },
    }
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
    "app.fiscal", # Módulo Fiscal
    "facturacion",
    # Phase 5: Auth & Security
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "allauth_2fa",
]

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# AllAuth Configuration
SITE_ID = 1
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
LOGIN_REDIRECT_URL = "/" # Dashboard or Redirect View
ACCOUNT_ADAPTER = "allauth_2fa.adapter.OTPAdapter"
# 2FA Settings
ALLAUTH_2FA_ALWAYS_REVEAL_BACKUP_TOKENS = False

AUTH_USER_MODEL = "app.UserAccount"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "app", "static"),
]

# Media files (App uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

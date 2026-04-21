import logging
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from allauth.account.forms import LoginForm, SignupForm

logger = logging.getLogger(__name__)


class SafeBaseFormMixin:
    """
    Mixin que proporciona métodos de saneamiento y validación anti-inyección SQL.
    """

    # Patrones sospechosos que indican intentos de inyección SQL o comandos de sistema
    SQL_INJECTION_PATTERNS = [
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",  # Tautologías SQL
        r"(\bSELECT\b.*\bFROM\b)",  # Sentencias SELECT
        r"(\bUNION\b.*\bSELECT\b)",  # UNION SELECT
        r"(--|\#)",  # Comentarios SQL
        r"(\bDROP\b|\bCREATE\b|\bALTER\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b)",  # DDL/DML explícito
        r"(;\s*(\bSELECT\b|\bDROP\b))",  # Múltiples sentencias
        r"(/\*.*\*/)",  # Comentarios en bloque
        r"(\\x[0-9a-fA-F]{2})",  # Bytes hexadecimales
        r"(\\u[0-9a-fA-F]{4})",  # Unicode escape
        r"(\bEXEC\b|\bEXECUTE\b|\bXP_CMDSHELL\b)",  # Procedimientos de sistema
        r"(\bFunction\(.*\)\(\))",  # Payload JavaScript puro u ofuscado
        r"((?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=))",  # Base64 crudo
    ]
    # Compilación de patrones con flags IGNORECASE
    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]

    def clean_field(self, field_name):
        """Sanea y valida un campo específico contra patrones de inyección."""
        value = self.cleaned_data.get(field_name, "")
        if not isinstance(value, str):
            return value

        # Saneamiento básico: eliminar caracteres de control y espacios múltiples
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
        sanitized = " ".join(sanitized.split())  # Normaliza espacios

        # Verificar patrones de inyección y ofuscación (Hex/B64/JS)
        for pattern in self.COMPILED_PATTERNS:
            if pattern.search(sanitized):

                # Reporte a la consola/archivo WORM
                logger.warning(
                    f"[SIEM FLAG] Posible intento de inyección / ofuscación payload detectado en campo '{field_name}'",
                    extra={"ip": getattr(self, "client_ip", "unknown"), "value_preview": sanitized[:50]},
                )

                # REPORTAR A REDIS (Bloqueo IP Hopping Activo) en caso de que tengamos el Request obj en el form
                from app.middleware.device_fingerprint import DeviceFingerprintMiddleware

                if hasattr(self, "request"):
                    DeviceFingerprintMiddleware.record_sql_injection_attempt(self.request)
                elif hasattr(self, "initial") and "request" in self.initial:
                    DeviceFingerprintMiddleware.record_sql_injection_attempt(self.initial["request"])

                raise ValidationError(
                    _(
                        "Entrada no válida. El sistema ha registrado esta solicitud bajo la política de seguridad estricta."
                    )
                )

        return sanitized

    def clean_email(self):
        """Validación estricta de formato de email."""
        email = self.cleaned_data.get("email")
        if not email:
            return email

        # Saneamiento
        email = self.clean_field("email")

        # Validación de email según RFC 5322 simplificada
        email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        if not email_regex.match(email):
            raise ValidationError(_("Introduce una dirección de correo electrónico válida."))

        return email.lower()


class SafeLoginForm(SafeBaseFormMixin, LoginForm):
    """
    Formulario de inicio de sesión con protección contra inyecciones SQL.
    """

    def clean(self):
        cleaned_data = super().clean()
        # Aplicar saneamiento a login (puede ser username o email)
        if "login" in cleaned_data:
            self.cleaned_data["login"] = self.clean_field("login")
        return cleaned_data

    def clean_login(self):
        login = self.cleaned_data["login"]
        return self.clean_field("login")

    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) > 128:
            raise ValidationError(_("La contraseña es demasiado larga."))
        return password


class SafeSignupForm(SafeBaseFormMixin, SignupForm):
    """
    Formulario de registro con protección contra inyecciones SQL.
    """

    def clean(self):
        cleaned_data = super().clean()
        # Saneamiento de campos de texto adicionales
        for field in ["username", "email", "first_name", "last_name"]:
            if field in cleaned_data:
                cleaned_data[field] = self.clean_field(field)
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data["username"]
        return self.clean_field("username")

    def clean_email(self):
        return super().clean_email()  # Ya hereda el método clean_email del mixin

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) > 128:
            raise ValidationError(_("La contraseña es demasiado larga."))
        return password

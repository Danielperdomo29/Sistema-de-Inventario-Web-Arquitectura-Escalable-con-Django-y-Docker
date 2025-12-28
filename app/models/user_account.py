from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserAccount(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Usa la tabla estándar 'auth_user' de Django.

    Campos extendidos para django-allauth (Fase 3 - Migración Incremental):
    - Mantiene compatibilidad con sistema actual
    - Agrega campos para verificación de email
    - Feature flag por usuario para migración gradual
    """

    # ========================================================================
    # CAMPOS EXISTENTES (Mantener compatibilidad)
    # ========================================================================
    rol_id = models.IntegerField(default=2, help_text="1: Admin, 2: Cliente/Usuario")

    # ========================================================================
    # NUEVOS CAMPOS PARA ALLAUTH (Fase 3)
    # ========================================================================

    # Verificación de email
    email_verified = models.BooleanField(
        default=False, help_text="Indica si el email ha sido verificado (allauth)"
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora de verificación del email"
    )

    # Información de contacto adicional
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="El número de teléfono debe tener entre 9 y 15 dígitos."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        help_text="Número de teléfono del usuario",
    )

    # Feature flag: Migración gradual de usuarios
    use_allauth = models.BooleanField(
        default=False, help_text="Usuario migrado al nuevo sistema de autenticación con allauth"
    )

    # Campos para facturación electrónica (DIAN)
    identificacion = models.CharField(
        max_length=20, blank=True, null=True, help_text="Número de identificación (CC, NIT, etc.)"
    )
    tipo_identificacion = models.CharField(
        max_length=3,  # Aumentado a 3 para acomodar 'NIT', 'TI', etc.
        choices=[
            ("CC", "Cédula de Ciudadanía"),
            ("CE", "Cédula de Extranjería"),
            ("NIT", "NIT"),
            ("PP", "Pasaporte"),
            ("TI", "Tarjeta de Identidad"),
        ],
        default="CC",
        blank=True,
        null=True,
    )

    # Configuración de notificaciones
    receive_email_notifications = models.BooleanField(
        default=True, help_text="Recibir notificaciones por email"
    )

    # Metadata
    last_password_change = models.DateTimeField(
        blank=True, null=True, help_text="Última vez que cambió la contraseña"
    )

    class Meta:
        db_table = "auth_user"
        verbose_name = "Usuario del Sistema"
        verbose_name_plural = "Usuarios del Sistema"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["use_allauth"]),
        ]

    def __str__(self):
        return self.username or self.email

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.get_full_name() or self.username

    @property
    def rol(self):
        """Mapeo simple de roles para compatibilidad"""
        roles = {1: "Administrador", 2: "Usuario"}
        return roles.get(self.rol_id, "Usuario")

    @property
    def is_email_verified(self):
        """Compatibilidad con allauth - verifica si el email está verificado"""
        return self.email_verified

    def mark_email_verified(self):
        """Marca el email como verificado"""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=["email_verified", "email_verified_at"])

    def migrate_to_allauth(self, auto_verify_email=True):
        """
        Migra el usuario al nuevo sistema de allauth.

        Args:
            auto_verify_email: Si True, marca el email como verificado automáticamente
        """
        self.use_allauth = True
        if auto_verify_email and self.email and not self.email_verified:
            self.mark_email_verified()
        self.save(update_fields=["use_allauth"])
        return True

from django.db import models
from django.contrib.auth.models import AbstractUser

class UserAccount(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Usa la tabla estándar 'auth_user' de Django.
    """
    
    # Mapeo de campos requeridos por el sistema antiguo
    rol_id = models.IntegerField(default=2, help_text="1: Admin, 2: Cliente/Usuario")
    
    class Meta:
        db_table = 'auth_user'  # Corregido de 'auth_users' a 'auth_user' para estándar Django
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'Usuarios del Sistema'

    def __str__(self):
        return self.username

    @property
    def nombre_completo(self):
        return self.get_full_name() or self.username

    @property
    def rol(self):
        # Mapeo simple de roles para compatibilidad
        roles = {1: "Administrador", 2: "Usuario"}
        return roles.get(self.rol_id, "Usuario")

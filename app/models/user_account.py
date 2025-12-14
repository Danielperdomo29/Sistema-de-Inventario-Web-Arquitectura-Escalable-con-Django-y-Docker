from django.db import models
from django.contrib.auth.models import AbstractUser

class UserAccount(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Reemplaza la tabla 'usuarios' antigua.
    """
    # Campos adicionales si son necesarios, pero AbstractUser ya tiene:
    # username, first_name, last_name, email, password, is_staff, is_active, date_joined
    
    # Mapeo de campos requeridos por el sistema antiguo
    # nombre_completo se puede obtener de get_full_name()
    # rol_id era usado antes. Podríamos agregar un campo rol o usar Groups de Django.
    
    # Para mantener compatibilidad simple, agregamos rol_id como entero por ahora,
    # o mejor, un campo de elección o clave foránea si tuviéramos tabla de roles.
    # El sistema anterior tenía tabla 'roles'.
    
    rol_id = models.IntegerField(default=2, help_text="1: Admin, 2: Cliente/Usuario")
    
    # is_active viene de AbstractUser.
    
    class Meta:
        db_table = 'auth_users'  # Nombre solicitado por el usuario
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'Usuarios del Sistema'

    def __str__(self):
        return self.username

    @property
    def nombre_completo(self):
        return self.get_full_name() or self.username

    @property
    def rol(self):
        try:
            from app.models.role import Role
            r = Role.get_by_id(self.rol_id)
            return r['nombre'] if r else "Usuario"
        except Exception:
            return "Usuario"

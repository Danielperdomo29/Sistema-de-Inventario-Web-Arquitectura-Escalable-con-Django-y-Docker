from django.db import models
from core.mixins import CRUDMixin


class Role(CRUDMixin, models.Model):
    """Modelo de Rol"""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    # Configuración del mixin CRUD
    crud_fields = ['id', 'nombre', 'descripcion', 'created_at']
    crud_order_by = 'nombre'
    crud_uses_soft_delete = False  # Hard delete

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre

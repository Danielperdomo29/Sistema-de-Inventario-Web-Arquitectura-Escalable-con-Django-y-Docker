from django.db import models
from core.mixins import SoftDeleteMixin


class Category(SoftDeleteMixin, models.Model):
    """Modelo de Categoría"""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    # Configuración del mixin CRUD
    crud_fields = ['id', 'nombre', 'descripcion']
    crud_order_by = 'nombre'

    class Meta:
        db_table = "categorias"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

from django.db import models
from core.mixins import SoftDeleteMixin


class Warehouse(SoftDeleteMixin, models.Model):
    """Modelo de Almacén"""

    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    capacidad = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    # Configuración del mixin CRUD
    crud_fields = ['id', 'nombre', 'ubicacion', 'capacidad']
    crud_order_by = 'nombre'

    class Meta:
        db_table = "almacenes"
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre

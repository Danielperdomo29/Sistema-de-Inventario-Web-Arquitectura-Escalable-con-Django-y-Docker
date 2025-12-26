from django.db import models


class Warehouse(models.Model):
    """Modelo de Almacén"""

    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    capacidad = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "almacenes"
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre

    @staticmethod
    def get_all():
        """Obtiene todos los almacenes activos"""
        return list(
            Warehouse.objects.filter(activo=True)
            .values("id", "nombre", "ubicacion", "capacidad")
            .order_by("nombre")
        )

    @staticmethod
    def get_by_id(warehouse_id):
        """Obtiene un almacén por su ID"""
        try:
            return (
                Warehouse.objects.filter(id=warehouse_id, activo=True)
                .values("id", "nombre", "ubicacion", "capacidad")
                .first()
            )
        except Exception:
            return None

    @staticmethod
    def count():
        """Cuenta el total de almacenes activos"""
        return Warehouse.objects.filter(activo=True).count()

    @staticmethod
    def create(data):
        """Crea un nuevo almacén"""
        wh = Warehouse.objects.create(
            nombre=data["nombre"],
            ubicacion=data.get("ubicacion", ""),
            capacidad=data.get("capacidad", 0),
            activo=data.get("activo", True),
        )
        return wh.id

    @staticmethod
    def update(warehouse_id, data):
        """Actualiza un almacén existente"""
        return Warehouse.objects.filter(id=warehouse_id).update(
            nombre=data["nombre"],
            ubicacion=data.get("ubicacion", ""),
            capacidad=data.get("capacidad", 0),
            activo=data.get("activo", True),
        )

    @staticmethod
    def delete(warehouse_id):
        """Elimina un almacén (soft delete cambiando activo a 0)"""
        return Warehouse.objects.filter(id=warehouse_id).update(activo=False)

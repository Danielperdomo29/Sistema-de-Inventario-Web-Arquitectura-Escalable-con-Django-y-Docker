from django.db import models
from django.db.models import Sum
from django.utils import timezone

from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user_account import UserAccount


class Purchase(models.Model):
    """Modelo de Compra"""

    numero_factura = models.CharField(max_length=50)
    proveedor = models.ForeignKey(Supplier, on_delete=models.PROTECT, db_column="proveedor_id")
    usuario = models.ForeignKey(UserAccount, on_delete=models.PROTECT, db_column="usuario_id")
    fecha = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, default="pendiente")
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "compras"
        verbose_name = "Compra"
        verbose_name_plural = "Compras"

    @staticmethod
    def get_all(limit=None):
        """Obtener todas las compras con información del proveedor y usuario"""
        purchases = Purchase.objects.select_related("proveedor", "usuario").order_by(
            "-fecha", "-id"
        )
        if limit:
            purchases = purchases[:limit]

        data = []
        for p in purchases:
            data.append(
                {
                    "id": p.id,
                    "numero_factura": p.numero_factura,
                    "fecha": p.fecha,
                    "total": p.total,
                    "estado": p.estado,
                    "proveedor_nombre": p.proveedor.nombre,
                    "usuario_nombre": p.usuario.username,
                }
            )
        return data

    @staticmethod
    def get_by_id(purchase_id):
        """Obtener una compra por ID con información del proveedor y usuario"""
        try:
            p = Purchase.objects.select_related("proveedor", "usuario").get(id=purchase_id)
            return {
                "id": p.id,
                "numero_factura": p.numero_factura,
                "proveedor_id": p.proveedor_id,
                "fecha": p.fecha,
                "total": p.total,
                "estado": p.estado,
                "notas": p.notas,
                "proveedor_nombre": p.proveedor.nombre,
                "usuario_nombre": p.usuario.username,
            }
        except Purchase.DoesNotExist:
            return None

    @staticmethod
    def count():
        """Contar total de compras"""
        return Purchase.objects.count()

    @staticmethod
    def total_compras_mes():
        """Calcula el total de compras del mes actual"""
        now = timezone.now()
        total = Purchase.objects.filter(fecha__year=now.year, fecha__month=now.month).aggregate(
            Sum("total")
        )["total__sum"]
        return total if total else 0

    @staticmethod
    def create(data, details):
        """Crear una nueva compra con sus detalles"""
        from django.db import transaction

        try:
            with transaction.atomic():
                purchase = Purchase.objects.create(
                    numero_factura=data["numero_factura"],
                    proveedor_id=data["proveedor_id"],
                    usuario_id=data["usuario_id"],
                    fecha=data["fecha"],
                    total=data["total"],
                    estado=data.get("estado", "pendiente"),
                    notas=data.get("notas", ""),
                )

                if details:
                    for detail in details:
                        PurchaseDetail.objects.create(
                            compra=purchase,
                            producto_id=detail["producto_id"],
                            cantidad=detail["cantidad"],
                            precio_unitario=detail["precio_unitario"],
                            subtotal=detail["subtotal"],
                        )
                return purchase.id
        except Exception:
            return None

    @staticmethod
    def update(purchase_id, data):
        """Actualizar una compra"""
        return Purchase.objects.filter(id=purchase_id).update(
            numero_factura=data["numero_factura"],
            proveedor_id=data["proveedor_id"],
            fecha=data["fecha"],
            total=data["total"],
            estado=data["estado"],
            notas=data.get("notas", ""),
        )

    @staticmethod
    def delete(purchase_id):
        """Eliminar una compra y sus detalles"""
        # Cascade should handle details
        return Purchase.objects.filter(id=purchase_id).delete()

    @staticmethod
    def get_details(purchase_id):
        """Obtener los detalles de una compra"""
        details = (
            PurchaseDetail.objects.filter(compra_id=purchase_id)
            .select_related("producto")
            .order_by("id")
        )
        data = []
        for d in details:
            data.append(
                {
                    "id": d.id,
                    "compra_id": d.compra_id,
                    "producto_id": d.producto_id,
                    "cantidad": d.cantidad,
                    "precio_unitario": d.precio_unitario,
                    "subtotal": d.subtotal,
                    "producto_nombre": d.producto.nombre,
                }
            )
        return data

    @staticmethod
    def update_details(purchase_id, details):
        """Actualizar los detalles de una compra"""
        from django.db import transaction

        with transaction.atomic():
            PurchaseDetail.objects.filter(compra_id=purchase_id).delete()

            if details:
                for detail in details:
                    PurchaseDetail.objects.create(
                        compra_id=purchase_id,
                        producto_id=detail["producto_id"],
                        cantidad=detail["cantidad"],
                        precio_unitario=detail["precio_unitario"],
                        subtotal=detail["subtotal"],
                    )
        return True


class PurchaseDetail(models.Model):
    """Modelo de Detalle de Compra"""

    compra = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, db_column="compra_id", related_name="detalles"
    )
    producto = models.ForeignKey(Product, on_delete=models.PROTECT, db_column="producto_id")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_compras"
        verbose_name = "Detalle de Compra"

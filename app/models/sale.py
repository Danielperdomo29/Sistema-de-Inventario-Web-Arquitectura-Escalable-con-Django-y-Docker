from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from app.models.client import Client
from app.models.product import Product
from app.models.user_account import UserAccount


class Sale(models.Model):
    """Modelo de Venta"""

    numero_factura = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(Client, on_delete=models.PROTECT, db_column="cliente_id")
    usuario = models.ForeignKey(UserAccount, on_delete=models.PROTECT, db_column="usuario_id")
    fecha = models.DateTimeField()

    # Campos de totales e impuestos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Subtotal sin IVA")
    iva_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Total de IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2)

    estado = models.CharField(max_length=20, default="completada")
    tipo_pago = models.CharField(max_length=20, default="efectivo")
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ventas"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        indexes = [
            models.Index(fields=["fecha"], name="idx_sale_fecha"),
            models.Index(fields=["cliente"], name="idx_sale_cliente"),
            models.Index(fields=["usuario"], name="idx_sale_usuario"),
            models.Index(fields=["estado"], name="idx_sale_estado"),
            models.Index(fields=["-fecha", "estado"], name="idx_sale_fecha_estado"),
        ]

    def calculate_totals(self):
        """Calcula subtotal, IVA y total desde los detalles."""
        from decimal import Decimal

        details = self.detalles.all()
        if not details.exists():
            self.subtotal = Decimal("0")
            self.iva_total = Decimal("0")
            self.total = Decimal("0")
            return

        subtotal_sin_iva = Decimal("0")
        iva_total = Decimal("0")

        for detail in details:
            if detail.subtotal_sin_iva and detail.iva_valor:
                subtotal_sin_iva += detail.subtotal_sin_iva
                iva_total += detail.iva_valor
            else:
                # Legacy: calcular desde subtotal y tasa
                tasa = detail.iva_tasa or Decimal("19.00")
                detail.subtotal_sin_iva = detail.precio_unitario * detail.cantidad
                detail.iva_valor = detail.subtotal_sin_iva * (tasa / Decimal("100"))
                detail.subtotal = detail.subtotal_sin_iva + detail.iva_valor
                detail.save()

                subtotal_sin_iva += detail.subtotal_sin_iva
                iva_total += detail.iva_valor

        self.subtotal = subtotal_sin_iva
        self.iva_total = iva_total
        self.total = subtotal_sin_iva + iva_total

    @staticmethod
    def get_all(limit=None):
        """Obtiene todas las ventas con información del cliente"""
        sales = Sale.objects.select_related("cliente", "usuario", "factura_electronica").order_by("-fecha", "-id")
        if limit:
            sales = sales[:limit]

        data = []
        for s in sales:
            data.append(
                {
                    "id": s.id,
                    "numero_factura": s.numero_factura,
                    "fecha": s.fecha,
                    "subtotal": s.subtotal or 0,
                    "iva": s.iva_total or 0,
                    "total": s.total,
                    "estado": s.estado,
                    "tipo_pago": s.tipo_pago,
                    "cliente_nombre": s.cliente.nombre,
                    "cliente_documento": s.cliente.documento,
                    "vendedor": s.usuario.username,
                    "factura_dian": getattr(s, "factura_electronica", None),
                }
            )
        return data

    @staticmethod
    def get_by_id(sale_id):
        """Obtiene una venta por su ID"""
        try:
            s = Sale.objects.select_related("cliente", "usuario", "factura_electronica").get(id=sale_id)
            return {
                "id": s.id,
                "numero_factura": s.numero_factura,
                "cliente_id": s.cliente_id,
                "fecha": s.fecha,
                "total": s.total,
                "estado": s.estado,
                "tipo_pago": s.tipo_pago,
                "notas": s.notas,
                "cliente_nombre": s.cliente.nombre,
                "cliente_documento": s.cliente.documento,
                "cliente_telefono": s.cliente.telefono,
                "vendedor": s.usuario.username,
                "factura_dian": getattr(s, "factura_electronica", None),
            }
        except Sale.DoesNotExist:
            return None

    @staticmethod
    def count():
        """Cuenta el total de ventas"""
        return Sale.objects.count()

    @staticmethod
    def total_ventas_mes():
        """Calcula el total de ventas del mes actual"""
        now = timezone.localtime(timezone.now())
        total = Sale.objects.filter(
            fecha__year=now.year,
            fecha__month=now.month,
            estado="completada",  # Use value from legacy query? 'completada' was hardcoded
        ).aggregate(Sum("total"))["total__sum"]
        return total if total else 0

    @staticmethod
    def get_details(sale_id):
        """Obtiene los detalles de una venta"""
        details = SaleDetail.objects.filter(venta_id=sale_id).select_related("producto")
        data = []
        for d in details:
            data.append(
                {
                    "id": d.id,
                    "venta_id": d.venta_id,
                    "producto_id": d.producto_id,
                    "cantidad": d.cantidad,
                    "precio_unitario": d.precio_unitario,
                    "subtotal": d.subtotal,
                    "subtotal_sin_iva": d.subtotal_sin_iva,
                    "iva_valor": d.iva_valor,
                    "iva_tasa": d.iva_tasa,
                    "producto_nombre": d.producto.nombre,
                    "producto_codigo": d.producto.codigo,
                }
            )
        return data

    @staticmethod
    def create(data, details):
        """Crea una nueva venta con sus detalles"""
        from django.db import transaction

        try:
            with transaction.atomic():
                venta = Sale.objects.create(
                    numero_factura=data["numero_factura"],
                    cliente_id=data["cliente_id"],
                    usuario_id=data["usuario_id"],
                    fecha=data["fecha"],
                    total=data["total"],
                    estado=data.get("estado", "completada"),
                    tipo_pago=data.get("tipo_pago", "efectivo"),
                    notas=data.get("notas", ""),
                )

                for detail in details:
                    SaleDetail.objects.create(
                        venta=venta,
                        producto_id=detail["producto_id"],
                        cantidad=detail["cantidad"],
                        precio_unitario=detail.get("precio_unitario_base"),
                        descuento_tasa=detail.get("descuento_pct", 0.00),
                        descuento_valor=detail.get("valor_descuento", 0.00),
                        iva_tasa=detail.get("iva_tasa", 19.00),
                        iva_valor=detail.get("iva_valor"),
                        subtotal_sin_iva=detail.get("subtotal_base"),
                        subtotal=detail["subtotal"],
                    )
                return venta.id
        except Exception as e:
            # Log error?
            raise e

    @staticmethod
    def update(sale_id, data, details):
        """Actualiza una venta existente"""
        from django.db import transaction

        with transaction.atomic():
            Sale.objects.filter(id=sale_id).update(
                numero_factura=data["numero_factura"],
                cliente_id=data["cliente_id"],
                fecha=data["fecha"],
                total=data["total"],
                estado=data.get("estado", "completada"),
                tipo_pago=data.get("tipo_pago", "efectivo"),
                notas=data.get("notas", ""),
            )

            # Eliminar detalles anteriores
            SaleDetail.objects.filter(venta_id=sale_id).delete()

            # Insertar nuevos detalles
            for detail in details:
                SaleDetail.objects.create(
                    venta_id=sale_id,
                    producto_id=detail["producto_id"],
                    cantidad=detail["cantidad"],
                    precio_unitario=detail.get("precio_unitario_base"),
                    descuento_tasa=detail.get("descuento_pct", 0.00),
                    descuento_valor=detail.get("valor_descuento", 0.00),
                    iva_tasa=detail.get("iva_tasa", 19.00),
                    iva_valor=detail.get("iva_valor"),
                    subtotal_sin_iva=detail.get("subtotal_base"),
                    subtotal=detail["subtotal"],
                )
        return True

    @staticmethod
    def delete(sale_id):
        """Elimina una venta y sus detalles"""
        # Cascade delete should handle details if configured, but let's be explicit or rely on Django
        # Django defaults to CASCADE for ForeignKey unless specified otherwise.
        # But SaleDetail FK definition below needs to be checked.
        return Sale.objects.filter(id=sale_id).delete()


class SaleDetail(models.Model):
    """Modelo de Detalle de Venta"""

    venta = models.ForeignKey(Sale, on_delete=models.CASCADE, db_column="venta_id", related_name="detalles")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT, db_column="producto_id")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio unitario SIN IVA")

    # Trazabilidad Tributaria (Actualizado FASE 1)
    iva_tasa = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, help_text="Tasa de IVA (%)")
    subtotal_sin_iva = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, help_text="Base Gravable x Cantidad"
    )
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Valor del IVA")
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Total de la línea (Subtotal sin IVA + IVA Valor)"
    )

    # Descuentos (Nuevo FASE 3)
    descuento_tasa = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    descuento_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        # Aseguramos el redondeo estricto antes de guardar (Requerimiento DIAN)
        if self.precio_unitario and self.cantidad:
            # 1. Subtotal Bruto
            bruto = (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # 2. Descuento
            tasa_desc = self.descuento_tasa or Decimal("0.00")
            self.descuento_valor = (bruto * (tasa_desc / Decimal("100"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # 3. Base Gravable (Subtotal sin IVA)
            self.subtotal_sin_iva = bruto - self.descuento_valor

            # 4. IVA (Sobre la base descontada)
            tasa_iva = self.iva_tasa or Decimal("0.00")
            self.iva_valor = (self.subtotal_sin_iva * (tasa_iva / Decimal("100"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # 5. Total Línea
            self.subtotal = self.subtotal_sin_iva + self.iva_valor

        super().save(*args, **kwargs)

    class Meta:
        db_table = "detalle_ventas"
        verbose_name = "Detalle de Venta"

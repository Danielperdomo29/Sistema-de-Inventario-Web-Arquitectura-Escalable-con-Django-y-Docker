"""
Modelo de Historial de Stock
Registra todos los movimientos de inventario para auditoría y análisis.
"""
from django.db import models
from app.models.product import Product
from app.models.user_account import UserAccount


class HistorialStock(models.Model):
    """Registro inmutable de movimientos de inventario"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('venta', 'Venta'),
        ('compra', 'Compra'),
        ('ajuste', 'Ajuste Manual'),
        ('devolucion', 'Devolución'),
        ('merma', 'Merma/Pérdida'),
    ]
    
    producto = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='historial_movimientos',
        db_column='producto_id'
    )
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        db_index=True
    )
    cantidad = models.IntegerField(
        help_text="Cantidad del movimiento (positivo o negativo)"
    )
    stock_anterior = models.IntegerField(
        help_text="Stock antes del movimiento"
    )
    stock_nuevo = models.IntegerField(
        help_text="Stock después del movimiento"
    )
    usuario = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name='movimientos_stock',
        db_column='usuario_id',
        null=True,
        blank=True
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales del movimiento (venta_id, compra_id, etc.)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'historial_stock'
        verbose_name = 'Historial de Stock'
        verbose_name_plural = 'Historial de Stock'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['producto', '-created_at'], name='idx_hist_prod_fecha'),
            models.Index(fields=['tipo_movimiento', '-created_at'], name='idx_hist_tipo_fecha'),
            models.Index(fields=['-created_at'], name='idx_hist_fecha'),
        ]
    
    def __str__(self):
        return f"{self.tipo_movimiento.upper()} - {self.producto.nombre} ({self.cantidad} unidades)"
    
    @property
    def diferencia(self):
        """Calcula la diferencia de stock"""
        return self.stock_nuevo - self.stock_anterior

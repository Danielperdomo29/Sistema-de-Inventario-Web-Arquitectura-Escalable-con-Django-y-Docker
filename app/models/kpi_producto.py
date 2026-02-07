"""
Modelo KPIProducto para almacenar métricas agregadas diarias de productos.
Evita recalcular constantemente métricas complejas.

Principios de diseño:
- Alta disponibilidad: Índices optimizados para consultas rápidas
- Integridad: Validaciones y unique_together para evitar duplicados
- Confidencialidad: Solo datos agregados, sin información sensible de clientes
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import Dict, Any


class KPIProducto(models.Model):
    """
    Tabla agregada de KPIs por producto (snapshot diario).
    Se actualiza automáticamente mediante tarea Celery programada.
    """
    
    producto = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='kpis',
        help_text="Producto al que pertenecen estos KPIs"
    )
    fecha = models.DateField(
        default=timezone.now,
        help_text="Fecha del snapshot de KPIs"
    )
    
    # Métricas de ventas
    unidades_vendidas = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total de unidades vendidas en la fecha"
    )
    ganancia_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Ganancia total generada (precio_venta - precio_compra) * cantidad"
    )
    margen_promedio = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Margen de ganancia promedio en porcentaje (0-100%)"
    )
    
    # Métricas de inventario
    rotacion_dias = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Días promedio de rotación del inventario"
    )
    velocidad_venta = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Unidades vendidas por día (promedio últimos 30 días)"
    )
    
    # Clasificación ABC (Análisis de Pareto)
    RANKING_CHOICES = [
        ('A', 'Clase A - 20% productos que generan 80% ganancias'),
        ('B', 'Clase B - 30% productos siguientes'),
        ('C', 'Clase C - 50% productos restantes'),
    ]
    ranking_abc = models.CharField(
        max_length=1, 
        choices=RANKING_CHOICES, 
        null=True, 
        blank=True,
        help_text="Clasificación ABC según análisis de Pareto"
    )
    
    # Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del registro"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización del registro"
    )
    
    class Meta:
        db_table = 'kpi_productos'
        unique_together = [['producto', 'fecha']]
        indexes = [
            models.Index(fields=['producto', 'fecha'], name='idx_kpi_producto_fecha'),
            models.Index(fields=['fecha', 'ranking_abc'], name='idx_kpi_fecha_abc'),
            models.Index(fields=['-unidades_vendidas'], name='idx_kpi_top_vendidos'),
            models.Index(fields=['-ganancia_total'], name='idx_kpi_top_ganancias'),
            models.Index(fields=['rotacion_dias'], name='idx_kpi_rotacion'),
        ]
        ordering = ['-fecha', '-unidades_vendidas']
        verbose_name = 'KPI de Producto'
        verbose_name_plural = 'KPIs de Productos'
    
    def __str__(self):
        return f"KPI {self.producto.nombre} - {self.fecha}"
    
    def __repr__(self):
        return f"<KPIProducto: {self.producto.codigo} | {self.fecha} | {self.unidades_vendidas} unidades>"
    
    @classmethod
    def calcular_y_guardar_kpi_diario(cls, fecha=None) -> Dict[str, Any]:
        """
        Tarea programada para calcular KPIs diarios de todos los productos activos.
        
        Args:
            fecha: Fecha para calcular KPIs (default: hoy)
        
        Returns:
            Dict con estadísticas de la operación:
            {
                'fecha': date,
                'productos_procesados': int,
                'kpis_creados': int,
                'kpis_actualizados': int,
                'errores': List[str]
            }
        """
        from app.models import Product
        from django.db import transaction
        
        if fecha is None:
            fecha = timezone.now().date()
        
        productos_procesados = 0
        kpis_creados = 0
        kpis_actualizados = 0
        errores = []
        
        productos_activos = Product.objects.filter(activo=True)
        
        for producto in productos_activos:
            try:
                with transaction.atomic():
                    # Calcular métricas del día
                    unidades = cls._calcular_unidades_vendidas(producto, fecha)
                    ganancia = cls._calcular_ganancia_total(producto, fecha)
                    margen = cls._calcular_margen_promedio(producto)
                    rotacion = cls._calcular_rotacion_dias(producto)
                    velocidad = cls._calcular_velocidad_venta(producto)
                    ranking = cls._calcular_ranking_abc(producto)
                    
                    # Crear o actualizar KPI
                    kpi, created = cls.objects.update_or_create(
                        producto=producto,
                        fecha=fecha,
                        defaults={
                            'unidades_vendidas': unidades,
                            'ganancia_total': ganancia,
                            'margen_promedio': margen,
                            'rotacion_dias': rotacion,
                            'velocidad_venta': velocidad,
                            'ranking_abc': ranking,
                        }
                    )
                    
                    productos_procesados += 1
                    if created:
                        kpis_creados += 1
                    else:
                        kpis_actualizados += 1
                        
            except Exception as e:
                errores.append(f"Error en producto {producto.codigo}: {str(e)}")
        
        return {
            'fecha': fecha,
            'productos_procesados': productos_procesados,
            'kpis_creados': kpis_creados,
            'kpis_actualizados': kpis_actualizados,
            'errores': errores
        }
    
    @staticmethod
    def _calcular_unidades_vendidas(producto, fecha) -> int:
        """Calcula unidades vendidas en una fecha específica"""
        from app.models import SaleDetail
        from django.db.models import Sum
        
        total = SaleDetail.objects.filter(
            producto=producto,
            venta__fecha__date=fecha,
            venta__activo=True
        ).aggregate(total=Sum('cantidad'))['total']
        
        return total or 0
    
    @staticmethod
    def _calcular_ganancia_total(producto, fecha) -> Decimal:
        """Calcula ganancia total en una fecha específica"""
        from app.models import SaleDetail
        from django.db.models import Sum, F
        
        ganancia = SaleDetail.objects.filter(
            producto=producto,
            venta__fecha__date=fecha,
            venta__activo=True
        ).aggregate(
            total=Sum(F('cantidad') * (F('precio_unitario') - F('producto__precio_compra')))
        )['total']
        
        return ganancia or Decimal('0.00')
    
    @staticmethod
    def _calcular_margen_promedio(producto) -> Decimal:
        """Calcula margen de ganancia promedio del producto"""
        if producto.precio_venta > 0:
            margen = ((producto.precio_venta - producto.precio_compra) / producto.precio_venta) * 100
            return Decimal(str(round(margen, 2)))
        return Decimal('0.00')
    
    @staticmethod
    def _calcular_rotacion_dias(producto) -> int:
        """Calcula días promedio de rotación del inventario"""
        from app.models import SaleDetail
        from django.db.models import Sum
        from datetime import timedelta
        
        # Últimos 30 días
        fecha_inicio = timezone.now() - timedelta(days=30)
        
        ventas_30d = SaleDetail.objects.filter(
            producto=producto,
            venta__fecha__gte=fecha_inicio,
            venta__activo=True
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        if ventas_30d > 0 and producto.stock_actual > 0:
            ventas_diarias = ventas_30d / 30.0
            rotacion = int(producto.stock_actual / ventas_diarias)
            return rotacion
        
        return None
    
    @staticmethod
    def _calcular_velocidad_venta(producto) -> Decimal:
        """Calcula velocidad de venta (unidades/día últimos 30 días)"""
        from app.models import SaleDetail
        from django.db.models import Sum
        from datetime import timedelta
        
        fecha_inicio = timezone.now() - timedelta(days=30)
        
        ventas_30d = SaleDetail.objects.filter(
            producto=producto,
            venta__fecha__gte=fecha_inicio,
            venta__activo=True
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        velocidad = Decimal(str(ventas_30d / 30.0))
        return round(velocidad, 2)
    
    @staticmethod
    def _calcular_ranking_abc(producto) -> str:
        """
        Calcula clasificación ABC del producto según análisis de Pareto.
        Requiere calcular para todos los productos, por lo que se hace en batch.
        """
        # Este método se implementará en el servicio KPIService
        # para calcular el ranking de todos los productos a la vez
        return None

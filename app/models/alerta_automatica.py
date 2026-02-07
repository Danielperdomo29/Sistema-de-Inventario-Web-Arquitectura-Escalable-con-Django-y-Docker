"""
Modelo de Alertas Automáticas
Sistema de notificaciones inteligentes para gestión de inventario.
"""
from django.db import models
from django.utils import timezone
from app.models.product import Product


class AlertaAutomatica(models.Model):
    """Alertas automáticas del sistema de inventario"""
    
    TIPO_ALERTA_CHOICES = [
        ('STOCK_CRITICO', 'Stock Crítico (Sin Stock)'),
        ('STOCK_BAJO', 'Stock Bajo'),
        ('PRODUCTO_LENTO', 'Producto de Baja Rotación'),
        ('VENCIMIENTO_PROXIMO', 'Vencimiento Próximo'),
        ('MARGEN_BAJO', 'Margen de Ganancia Bajo'),
        ('ANOMALIA_PRECIO', 'Anomalía en Precio'),
    ]
    
    NIVEL_CHOICES = [
        ('ROJO', 'Urgente'),
        ('AMARILLO', 'Atención'),
        ('VERDE', 'Informativo'),
    ]
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('REVISADA', 'Revisada'),
        ('RESUELTA', 'Resuelta'),
        ('IGNORADA', 'Ignorada'),
    ]
    
    tipo_alerta = models.CharField(
        max_length=30,
        choices=TIPO_ALERTA_CHOICES,
        db_index=True
    )
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES,
        default='AMARILLO',
        db_index=True
    )
    producto = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='alertas',
        db_column='producto_id',
        null=True,
        blank=True,
        help_text="Producto relacionado (opcional para alertas globales)"
    )
    mensaje = models.TextField(
        help_text="Descripción de la alerta"
    )
    accion_sugerida = models.TextField(
        blank=True,
        help_text="Recomendación de acción (puede ser generada por IA)"
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        db_index=True
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'alertas_automaticas'
        verbose_name = 'Alerta Automática'
        verbose_name_plural = 'Alertas Automáticas'
        ordering = ['-nivel', '-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'nivel', '-fecha_creacion'], name='idx_alert_estado_nivel'),
            models.Index(fields=['producto', 'tipo_alerta'], name='idx_alert_prod_tipo'),
            models.Index(fields=['tipo_alerta', 'estado'], name='idx_alert_tipo_estado'),
        ]
        # Evitar duplicados de alertas pendientes para el mismo producto y tipo
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'tipo_alerta', 'estado'],
                condition=models.Q(estado='PENDIENTE'),
                name='unique_pending_alert_per_product'
            )
        ]
    
    def __str__(self):
        producto_nombre = self.producto.nombre if self.producto else "General"
        return f"[{self.nivel}] {self.tipo_alerta} - {producto_nombre}"
    
    def resolver(self):
        """Marca la alerta como resuelta"""
        self.estado = 'RESUELTA'
        self.fecha_resolucion = timezone.now()
        self.save(update_fields=['estado', 'fecha_resolucion'])
    
    def revisar(self):
        """Marca la alerta como revisada"""
        self.estado = 'REVISADA'
        self.save(update_fields=['estado'])
    
    def ignorar(self):
        """Marca la alerta como ignorada"""
        self.estado = 'IGNORADA'
        self.fecha_resolucion = timezone.now()
        self.save(update_fields=['estado', 'fecha_resolucion'])
    
    @property
    def dias_pendiente(self):
        """Calcula cuántos días lleva pendiente la alerta"""
        if self.estado == 'PENDIENTE':
            return (timezone.now() - self.fecha_creacion).days
        return None
    
    @property
    def prioridad(self):
        """Retorna prioridad numérica (1=más urgente)"""
        prioridades = {
            'ROJO': 1,
            'AMARILLO': 2,
            'VERDE': 3
        }
        return prioridades.get(self.nivel, 99)

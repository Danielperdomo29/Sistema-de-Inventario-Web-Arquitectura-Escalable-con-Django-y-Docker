"""
Modelo PeriodoContable - Fase B
Control de períodos contables con cierre y hash de integridad
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
import hashlib
import json
from datetime import datetime, date

User = get_user_model()


class PeriodoContable(models.Model):
    """
    Período Contable para control de cierres mensuales/anuales
    
    Características:
    - Cierre con hash de integridad del período
    - Imposibilidad de modificar períodos cerrados
    - Trazabilidad de cierres
    - Validación de secuencia temporal
    """
    
    # === IDENTIFICACIÓN ===
    año = models.PositiveIntegerField(
        validators=[
            MinValueValidator(2020),
            MaxValueValidator(2100)
        ],
        help_text="Año del período"
    )
    
    mes = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ],
        help_text="Mes del período (1-12)"
    )
    
    # === FECHAS ===
    fecha_inicio = models.DateField(
        help_text="Fecha de inicio del período"
    )
    
    fecha_fin = models.DateField(
        help_text="Fecha de fin del período"
    )
    
    # === ESTADO ===
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
        ('BLOQUEADO', 'Bloqueado'),  # Para períodos en auditoría
    ]
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='ABIERTO',
        db_index=True,
        help_text="Estado del período"
    )
    
    # === CIERRE ===
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora del cierre"
    )
    
    usuario_cierre = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='periodos_cerrados',
        help_text="Usuario que cerró el período"
    )
    
    hash_cierre = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 de todos los asientos del período"
    )
    
    # === ESTADÍSTICAS DEL PERÍODO ===
    total_asientos = models.PositiveIntegerField(
        default=0,
        help_text="Total de asientos en el período"
    )
    
    total_debitos = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        help_text="Suma total de débitos del período"
    )
    
    total_creditos = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        help_text="Suma total de créditos del período"
    )
    
    # === OBSERVACIONES ===
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones del cierre"
    )
    
    # === TIMESTAMPS ===
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contabilidad_periodo'
        verbose_name = 'Período Contable'
        verbose_name_plural = 'Períodos Contables'
        ordering = ['-año', '-mes']
        unique_together = [('año', 'mes')]
        indexes = [
            models.Index(fields=['año', 'mes']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
        permissions = [
            ('cerrar_periodo_contable', 'Puede cerrar períodos contables'),
            ('reabrir_periodo_contable', 'Puede reabrir períodos cerrados'),
        ]
    
    def __str__(self):
        meses = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        mes_nombre = meses[self.mes - 1]
        return f"{mes_nombre} {self.año} - {self.get_estado_display()}"
    
    def calcular_hash_periodo(self):
        """
        Calcula el hash SHA-256 de todos los asientos del período
        Incluye número, fecha, tipo y hash de cada asiento
        """
        from .asiento_contable import AsientoContable
        
        asientos = AsientoContable.objects.filter(
            periodo_contable=self,
            estado='ACTIVO'
        ).order_by('numero_asiento').values(
            'numero_asiento',
            'fecha_contable',
            'tipo_asiento',
            'hash_integridad',
            'total_debito',
            'total_credito'
        )
        
        datos_periodo = {
            'año': self.año,
            'mes': self.mes,
            'asientos': [
                {
                    'numero': a['numero_asiento'],
                    'fecha': a['fecha_contable'].isoformat(),
                    'tipo': a['tipo_asiento'],
                    'hash': a['hash_integridad'],
                    'debito': str(a['total_debito']),
                    'credito': str(a['total_credito'])
                }
                for a in asientos
            ]
        }
        
        datos_json = json.dumps(datos_periodo, sort_keys=True)
        return hashlib.sha256(datos_json.encode('utf-8')).hexdigest()
    
    def calcular_estadisticas(self):
        """
        Calcula las estadísticas del período
        """
        from .asiento_contable import AsientoContable
        from django.db.models import Sum, Count
        
        stats = AsientoContable.objects.filter(
            periodo_contable=self,
            estado='ACTIVO'
        ).aggregate(
            total=Count('id'),
            sum_debitos=Sum('total_debito'),
            sum_creditos=Sum('total_credito')
        )
        
        self.total_asientos = stats['total'] or 0
        self.total_debitos = stats['sum_debitos'] or 0
        self.total_creditos = stats['sum_creditos'] or 0
    
    def cerrar(self, usuario, observaciones=''):
        """
        Cierra el período contable
        - Calcula estadísticas
        - Genera hash de integridad
        - Marca como cerrado
        - Registra auditoría
        """
        if self.estado == 'CERRADO':
            raise ValueError("El período ya está cerrado")
        
        # Verificar que todos los asientos estén cuadrados
        from .asiento_contable import AsientoContable
        from decimal import Decimal
        
        asientos_descuadrados = AsientoContable.objects.filter(
            periodo_contable=self,
            estado='ACTIVO'
        ).exclude(
            diferencia__lte=Decimal('0.01'),
            diferencia__gte=Decimal('-0.01')
        ).count()
        
        if asientos_descuadrados > 0:
            raise ValueError(
                f"No se puede cerrar el período. "
                f"Hay {asientos_descuadrados} asientos descuadrados."
            )
        
        # Calcular estadísticas
        self.calcular_estadisticas()
        
        # Generar hash del período
        self.hash_cierre = self.calcular_hash_periodo()
        
        # Marcar como cerrado
        self.estado = 'CERRADO'
        self.fecha_cierre = timezone.now()
        self.usuario_cierre = usuario
        self.observaciones = observaciones
        
        self.save()
        
        # Registrar en auditoría
        from .log_auditoria_contable import LogAuditoriaContable
        LogAuditoriaContable.registrar(
            tipo_evento='CIERRE_PERIODO',
            usuario=usuario,
            detalles={
                'periodo': str(self),
                'total_asientos': self.total_asientos,
                'hash_cierre': self.hash_cierre
            }
        )
    
    def reabrir(self, usuario, motivo):
        """
        Reabre un período cerrado
        Requiere permisos especiales
        """
        if self.estado != 'CERRADO':
            raise ValueError("El período no está cerrado")
        
        if not motivo or len(motivo) < 20:
            raise ValueError("El motivo de reapertura debe tener al menos 20 caracteres")
        
        # Marcar como abierto
        self.estado = 'ABIERTO'
        self.observaciones += f"\n\nREABIERTO: {motivo}"
        
        self.save()
        
        # Registrar en auditoría
        from .log_auditoria_contable import LogAuditoriaContable
        LogAuditoriaContable.registrar(
            tipo_evento='REAPERTURA_PERIODO',
            usuario=usuario,
            detalles={
                'periodo': str(self),
                'motivo': motivo,
                'hash_anterior': self.hash_cierre
            }
        )

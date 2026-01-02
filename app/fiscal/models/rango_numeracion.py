"""
Modelo para gestión de Rangos de Numeración autorizados por la DIAN.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal


class RangoNumeracion(models.Model):
    """
    Rango de numeración autorizado por la DIAN para facturación electrónica.
    
    Gestiona los consecutivos de facturación según resolución DIAN,
    controlando rangos, vigencias y estado de uso.
    """
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('agotado', 'Agotado'),
        ('vencido', 'Vencido'),
        ('inactivo', 'Inactivo'),
    ]
    
    # Relación con configuración fiscal
    fiscal_config = models.ForeignKey(
        'fiscal.FiscalConfig',
        on_delete=models.PROTECT,
        related_name='rangos_numeracion',
        verbose_name=_("Configuración Fiscal")
    )
    
    # Datos de la Resolución DIAN
    numero_resolucion = models.CharField(
        _("Número de Resolución"),
        max_length=50,
        help_text="Número de resolución otorgado por la DIAN"
    )
    
    fecha_resolucion = models.DateField(
        _("Fecha de Resolución"),
        help_text="Fecha de emisión de la resolución"
    )
    
    fecha_inicio_vigencia = models.DateField(
        _("Fecha Inicio Vigencia"),
        help_text="Fecha desde la cual se puede usar este rango"
    )
    
    fecha_fin_vigencia = models.DateField(
        _("Fecha Fin Vigencia"),
        help_text="Fecha hasta la cual es válido este rango"
    )
    
    # Configuración del Rango
    prefijo = models.CharField(
        _("Prefijo"),
        max_length=10,
        help_text="Prefijo de facturación (ej: SETP, FE, FACT)"
    )
    
    rango_desde = models.BigIntegerField(
        _("Rango Desde"),
        validators=[MinValueValidator(1)],
        help_text="Número inicial del rango autorizado"
    )
    
    rango_hasta = models.BigIntegerField(
        _("Rango Hasta"),
        validators=[MinValueValidator(1)],
        help_text="Número final del rango autorizado"
    )
    
    consecutivo_actual = models.BigIntegerField(
        _("Consecutivo Actual"),
        validators=[MinValueValidator(1)],
        help_text="Próximo número a asignar"
    )
    
    # Clave Técnica (para cálculo de CUFE)
    clave_tecnica = models.CharField(
        _("Clave Técnica"),
        max_length=255,
        help_text="Clave técnica proporcionada por la DIAN para este rango"
    )
    
    # Estado y Control
    estado = models.CharField(
        _("Estado"),
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activo'
    )
    
    is_default = models.BooleanField(
        _("Rango por Defecto"),
        default=False,
        help_text="Si está activo, se usará este rango automáticamente"
    )
    
    # Alertas
    porcentaje_alerta = models.DecimalField(
        _("Porcentaje de Alerta"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0')), MinValueValidator(Decimal('100'))],
        help_text="Porcentaje de uso para enviar alerta de agotamiento"
    )
    
    alerta_enviada = models.BooleanField(
        _("Alerta Enviada"),
        default=False,
        help_text="Indica si ya se envió la alerta de agotamiento"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    notas = models.TextField(
        _("Notas"),
        blank=True,
        help_text="Observaciones adicionales sobre este rango"
    )
    
    class Meta:
        db_table = 'fiscal_rango_numeracion'
        verbose_name = _("Rango de Numeración")
        verbose_name_plural = _("Rangos de Numeración")
        ordering = ['-is_default', '-fecha_inicio_vigencia']
        indexes = [
            models.Index(fields=['estado', 'is_default']),
            models.Index(fields=['prefijo', 'estado']),
        ]
        # TODO: Re-enable constraints when Django version compatibility is resolved
        # constraints = [
        #     models.CheckConstraint(
        #         check=models.Q(rango_hasta__gte=models.F('rango_desde')),
        #         name='rango_hasta_mayor_igual_rango_desde'
        #     ),
        #     models.CheckConstraint(
        #         check=models.Q(consecutivo_actual__gte=models.F('rango_desde')),
        #         name='consecutivo_dentro_rango_minimo'
        #     ),
        # ]
    
    def __str__(self):
        return f"{self.prefijo} ({self.rango_desde}-{self.rango_hasta}) - {self.get_estado_display()}"
    
    def clean(self):
        """Validaciones a nivel de modelo."""
        super().clean()
        
        # Validar que consecutivo_actual esté dentro del rango
        if self.consecutivo_actual:
            if self.consecutivo_actual < self.rango_desde:
                raise ValidationError({
                    'consecutivo_actual': _("El consecutivo debe ser mayor o igual al inicio del rango")
                })
            
            if self.consecutivo_actual > self.rango_hasta:
                raise ValidationError({
                    'consecutivo_actual': _("El consecutivo ha excedido el rango autorizado")
                })
        
        # Validar fechas
        if self.fecha_fin_vigencia and self.fecha_inicio_vigencia:
            if self.fecha_fin_vigencia < self.fecha_inicio_vigencia:
                raise ValidationError({
                    'fecha_fin_vigencia': _("La fecha de fin debe ser posterior a la fecha de inicio")
                })
        
        # Solo puede haber un rango por defecto activo por configuración fiscal
        if self.is_default and self.estado == 'activo':
            otros_default = RangoNumeracion.objects.filter(
                fiscal_config=self.fiscal_config,
                is_default=True,
                estado='activo'
            ).exclude(pk=self.pk)
            
            if otros_default.exists():
                raise ValidationError({
                    'is_default': _("Ya existe otro rango activo marcado como predeterminado")
                })
    
    def save(self, *args, **kwargs):
        """Override save para inicializar consecutivo y actualizar estado."""
        # Inicializar consecutivo_actual si es nuevo registro
        if not self.pk and not self.consecutivo_actual:
            self.consecutivo_actual = self.rango_desde
        
        # Actualizar estado automáticamente
        self._actualizar_estado()
        
        super().save(*args, **kwargs)
    
    def _actualizar_estado(self):
        """Actualiza el estado del rango basado en uso y vigencia."""
        hoy = timezone.now().date()
        
        # Verificar vigencia
        if hoy < self.fecha_inicio_vigencia:
            self.estado = 'inactivo'
            return
        
        if hoy > self.fecha_fin_vigencia:
            self.estado = 'vencido'
            return
        
        # Verificar agotamiento
        if self.consecutivo_actual > self.rango_hasta:
            self.estado = 'agotado'
            return
        
        # Si no está vencido ni agotado, y está en vigencia
        if self.estado in ['vencido', 'agotado']:
            self.estado = 'activo'
    
    @property
    def numeros_disponibles(self) -> int:
        """Calcula cuántos números quedan disponibles en el rango."""
        return max(0, self.rango_hasta - self.consecutivo_actual + 1)
    
    @property
    def numeros_usados(self) -> int:
        """Calcula cuántos números se han usado del rango."""
        return self.consecutivo_actual - self.rango_desde
    
    @property
    def porcentaje_uso(self) -> Decimal:
        """Calcula el porcentaje de uso del rango."""
        total = self.rango_hasta - self.rango_desde + 1
        if total == 0:
            return Decimal('0')
        usado = self.numeros_usados
        return Decimal(usado) / Decimal(total) * Decimal('100')
    
    @property
    def requiere_alerta(self) -> bool:
        """Determina si se debe enviar alerta de agotamiento."""
        return (
            self.porcentaje_uso >= self.porcentaje_alerta and
            not self.alerta_enviada and
            self.estado == 'activo'
        )
    
    def formato_numero(self, numero: int) -> str:
        """
        Formatea un número de factura con el prefijo.
        
        Args:
            numero: Número consecutivo
            
        Returns:
            String con formato: PREFIJO + número con padding
        """
        # Calcular padding basado en el rango máximo
        max_digitos = len(str(self.rango_hasta))
        return f"{self.prefijo}{str(numero).zfill(max_digitos)}"
    
    def esta_vigente(self) -> bool:
        """Verifica si el rango está vigente en la fecha actual."""
        hoy = timezone.now().date()
        return self.fecha_inicio_vigencia <= hoy <= self.fecha_fin_vigencia
    
    def puede_asignar(self) -> bool:
        """Verifica si el rango puede asignar números actualmente."""
        return (
            self.estado == 'activo' and
            self.esta_vigente() and
            self.consecutivo_actual <= self.rango_hasta
        )

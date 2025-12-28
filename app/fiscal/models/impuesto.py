"""
Modelo Impuesto - Configuración de impuestos.

Maneja configuración de impuestos (IVA, Retenciones) con cálculos automáticos.
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError


class Impuesto(models.Model):
    """
    Configuración de impuestos para facturación.
    
    Soporta diferentes tipos de impuestos colombianos:
    - IVA (Impuesto al Valor Agregado)
    - RETEFUENTE (Retención en la Fuente)
    - RETEIVA (Retención de IVA)
    - RETEICA (Retención de ICA)
    
    Attributes:
        codigo: Código único del impuesto
        nombre: Nombre descriptivo
        tipo: Tipo de impuesto
        porcentaje: Porcentaje a aplicar
        base_minima: Base mínima para aplicar el impuesto
        cuenta_por_pagar: Cuenta contable para registrar el impuesto
        cuenta_por_cobrar: Cuenta contable para retenciones
        aplica_compras: Si aplica en compras
        aplica_ventas: Si aplica en ventas
        activo: Si el impuesto está activo
    
    Examples:
        >>> impuesto = Impuesto.objects.create(
        ...     codigo='IVA19',
        ...     nombre='IVA 19%',
        ...     tipo='IVA',
        ...     porcentaje=Decimal('19.00'),
        ...     cuenta_por_pagar=cuenta,
        ...     aplica_ventas=True
        ... )
        >>> impuesto.calcular(Decimal('1000.00'))
        Decimal('190.00')
    """
    
    # Choices
    TIPO_CHOICES = [
        ('IVA', 'IVA'),
        ('RETEFUENTE', 'Retención en la Fuente'),
        ('RETEIVA', 'Retención de IVA'),
        ('RETEICA', 'Retención de ICA'),
    ]
    
    # Campos
    codigo = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text='Código único del impuesto'
    )
    
    nombre = models.CharField(
        max_length=100,
        help_text='Nombre descriptivo del impuesto'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        help_text='Tipo de impuesto'
    )
    
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Porcentaje del impuesto (ej: 19.00 para 19%)'
    )
    
    base_minima = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Base mínima para aplicar el impuesto'
    )
    
    # Cuentas Contables
    cuenta_por_pagar = models.ForeignKey(
        'CuentaContable',
        on_delete=models.PROTECT,
        related_name='impuestos_por_pagar',
        help_text='Cuenta contable para el impuesto por pagar'
    )
    
    cuenta_por_cobrar = models.ForeignKey(
        'CuentaContable',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='impuestos_por_cobrar',
        help_text='Cuenta contable para el impuesto por cobrar (retenciones)'
    )
    
    # Aplicabilidad
    aplica_compras = models.BooleanField(
        default=False,
        help_text='Indica si el impuesto aplica en compras'
    )
    
    aplica_ventas = models.BooleanField(
        default=False,
        help_text='Indica si el impuesto aplica en ventas'
    )
    
    # Control
    activo = models.BooleanField(
        default=True,
        help_text='Indica si el impuesto está activo'
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha de última actualización'
    )
    
    class Meta:
        db_table = 'impuesto'
        verbose_name = 'Impuesto'
        verbose_name_plural = 'Impuestos'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['tipo']),
        ]
    
    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Valida:
        - Porcentaje debe estar entre 0 y 100
        - Base mínima debe ser >= 0
        
        Raises:
            ValidationError: Si alguna validación falla
        """
        errors = {}
        
        # Validar porcentaje
        if self.porcentaje < 0 or self.porcentaje > 100:
            errors['porcentaje'] = 'Porcentaje debe estar entre 0 y 100'
        
        # Validar base mínima
        if self.base_minima < 0:
            errors['base_minima'] = 'Base mínima debe ser mayor o igual a 0'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calcular(self, base):
        """
        Calcula el valor del impuesto sobre una base.
        
        Args:
            base: Base sobre la cual calcular el impuesto
        
        Returns:
            Decimal: Valor del impuesto calculado, redondeado a 2 decimales
        
        Examples:
            >>> impuesto.calcular(Decimal('1000.00'))
            Decimal('190.00')
        """
        # Validar base mínima
        if base < self.base_minima:
            return Decimal('0.00')
        
        # Calcular impuesto
        valor = (base * self.porcentaje / 100).quantize(Decimal('0.01'))
        
        return valor
    
    def es_aplicable(self, tipo_transaccion):
        """
        Verifica si el impuesto es aplicable a un tipo de transacción.
        
        Args:
            tipo_transaccion: 'venta' o 'compra'
        
        Returns:
            bool: True si el impuesto aplica
        
        Examples:
            >>> impuesto.es_aplicable('venta')
            True
        """
        if tipo_transaccion.lower() == 'venta':
            return self.aplica_ventas
        elif tipo_transaccion.lower() == 'compra':
            return self.aplica_compras
        return False
    
    def __str__(self):
        """Representación en string del impuesto"""
        return f"{self.codigo} - {self.nombre}"

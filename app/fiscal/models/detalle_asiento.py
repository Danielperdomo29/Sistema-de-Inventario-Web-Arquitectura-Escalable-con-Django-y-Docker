"""
Modelo DetalleAsiento - Fase B
Detalles de asientos contables con hash por línea
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
import hashlib
import json

User = get_user_model()


class DetalleAsiento(models.Model):
    """
    Detalle de Asiento Contable con hash individual por línea
    
    Características de seguridad:
    - Hash SHA-256 por cada línea
    - Trazabilidad de modificaciones
    - Validación de cuenta PUC
    - Control de centro de costos
    """
    
    # === RELACIONES ===
    asiento = models.ForeignKey(
        'fiscal.AsientoContable',
        on_delete=models.PROTECT,
        related_name='detalles',
        help_text="Asiento contable al que pertenece"
    )
    
    cuenta_contable = models.ForeignKey(
        'fiscal.CuentaContable',
        on_delete=models.PROTECT,
        related_name='movimientos',
        help_text="Cuenta contable del PUC"
    )
    
    # === ORDEN ===
    orden = models.PositiveSmallIntegerField(
        default=0,
        help_text="Orden de la línea en el asiento"
    )
    
    # === MONTOS ===
    debito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monto del débito"
    )
    
    credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monto del crédito"
    )
    
    # === DESCRIPCIÓN ===
    descripcion_detalle = models.CharField(
        max_length=500,
        help_text="Descripción específica de esta línea"
    )
    
    # === CENTRO DE COSTOS (Opcional) ===
    centro_costo = models.CharField(
        max_length=20,
        blank=True,
        help_text="Centro de costos (si aplica)"
    )
    
    # === TERCERO (Opcional) ===
    tercero_nit = models.CharField(
        max_length=20,
        blank=True,
        help_text="NIT del tercero específico de esta línea"
    )
    
    tercero_nombre = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre del tercero"
    )
    
    # === SEGURIDAD ===
    hash_linea = models.CharField(
        max_length=64,
        editable=False,
        db_index=True,
        help_text="SHA-256 de esta línea específica"
    )
    
    # === AUDITORÍA DE MODIFICACIONES ===
    usuario_modificacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='detalles_modificados',
        help_text="Último usuario que modificó esta línea"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        help_text="Última modificación"
    )
    
    # === TIMESTAMPS ===
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'contabilidad_detalle_asiento'
        verbose_name = 'Detalle de Asiento'
        verbose_name_plural = 'Detalles de Asientos'
        ordering = ['asiento', 'orden']
        indexes = [
            models.Index(fields=['asiento', 'orden']),
            models.Index(fields=['cuenta_contable', 'asiento']),
            models.Index(fields=['hash_linea']),
        ]
        unique_together = [
            ('asiento', 'orden')
        ]
    
    def __str__(self):
        return f"Detalle #{self.orden} - {self.cuenta_contable.codigo} - D:{self.debito} C:{self.credito}"
    
    def calcular_hash(self):
        """
        Calcula el hash SHA-256 de esta línea específica
        """
        datos_linea = {
            'asiento_numero': self.asiento.numero_asiento if self.asiento else 0,
            'cuenta': self.cuenta_contable.codigo,
            'orden': self.orden,
            'debito': str(self.debito),
            'credito': str(self.credito),
            'descripcion': self.descripcion_detalle,
            'centro_costo': self.centro_costo or '',
            'tercero_nit': self.tercero_nit or ''
        }
        
        datos_json = json.dumps(datos_linea, sort_keys=True)
        return hashlib.sha256(datos_json.encode('utf-8')).hexdigest()
    
    def verificar_integridad(self):
        """
        Verifica que el hash almacenado coincida con el hash calculado
        """
        hash_calculado = self.calcular_hash()
        es_valido = self.hash_linea == hash_calculado
        return es_valido, self.hash_linea, hash_calculado
    
    def es_valido(self):
        """
        Valida que la línea sea correcta:
        - Debe tener débito O crédito (no ambos)
        - Debe tener al menos uno mayor a 0
        - La cuenta debe ser de movimiento (no agrupadora)
        """
        errores = []
        
        # Validar que tenga débito O crédito
        if self.debito > 0 and self.credito > 0:
            errores.append("Una línea no puede tener débito Y crédito simultáneamente")
        
        # Validar que tenga al menos uno
        if self.debito == 0 and self.credito == 0:
            errores.append("La línea debe tener débito o crédito mayor a 0")
        
        # Validar que la cuenta sea de movimiento
        if self.cuenta_contable and not self.cuenta_contable.acepta_movimiento:
            errores.append(f"La cuenta {self.cuenta_contable.codigo} no permite movimiento")
        
        # Validar descripción
        if not self.descripcion_detalle or len(self.descripcion_detalle) < 5:
            errores.append("La descripción debe tener al menos 5 caracteres")
        
        return len(errores) == 0, errores
    
    def save(self, *args, **kwargs):
        """
        Override save para:
        1. Validar la línea
        2. Generar hash de integridad
        3. Actualizar totales del asiento padre
        """
        # Validar línea
        es_valido, errores = self.es_valido()
        if not es_valido:
            raise ValueError(f"Detalle inválido: {', '.join(errores)}")
        
        # Generar hash
        self.hash_linea = self.calcular_hash()
        
        super().save(*args, **kwargs)
        
        # Actualizar totales del asiento padre
        if self.asiento:
            self.asiento.actualizar_totales()
    
    def delete(self, *args, **kwargs):
        """
        Override delete para actualizar totales del asiento padre
        """
        asiento = self.asiento
        super().delete(*args, **kwargs)
        
        # Actualizar totales del asiento padre
        if asiento:
            asiento.actualizar_totales()

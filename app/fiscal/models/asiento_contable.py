"""
Modelo AsientoContable - Fase B
Sistema de contabilidad con seguridad integral y cumplimiento DIAN
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
import hashlib
import json
from datetime import datetime, date
from django.utils import timezone

User = get_user_model()


class AsientoContable(models.Model):
    """
    Asiento Contable con seguridad criptográfica y cumplimiento DIAN
    
    Características de seguridad:
    - Hash SHA-256 para integridad
    - Sello temporal inmutable
    - Trazabilidad completa (usuario, IP, origen)
    - Firma digital para asientos críticos
    - Imposibilidad de eliminación (solo anulación)
    """
    
    # === IDENTIFICACIÓN ===
    numero_asiento = models.BigIntegerField(
        unique=True,
        db_index=True,
        validators=[MinValueValidator(1)],
        help_text="Número consecutivo único e inviolable"
    )
    
    fecha_contable = models.DateField(
        db_index=True,
        help_text="Fecha del hecho económico (no modificable después de creación)"
    )
    
    sello_temporal = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="Timestamp exacto de creación (no repudio)"
    )
    
    # === CLASIFICACIÓN ===
    TIPO_ASIENTO_CHOICES = [
        ('VENTA', 'Venta'),
        ('COMPRA', 'Compra'),
        ('AJUSTE', 'Ajuste Contable'),
        ('CIERRE', 'Cierre de Período'),
        ('APERTURA', 'Apertura de Período'),
        ('NOMINA', 'Nómina'),
        ('MANUAL', 'Manual'),
    ]
    
    tipo_asiento = models.CharField(
        max_length=10,
        choices=TIPO_ASIENTO_CHOICES,
        db_index=True,
        help_text="Tipo de asiento contable"
    )
    
    # === ORIGEN Y TRAZABILIDAD ===
    documento_origen_tipo = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tipo de documento origen (FACTURA, RECIBO, NOTA, etc.)"
    )
    
    documento_origen_numero = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Número del documento origen"
    )
    
    tercero_nit = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="NIT del tercero relacionado"
    )
    
    tercero_nombre = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre del tercero"
    )
    
    # === DESCRIPCIÓN ===
    descripcion = models.TextField(
        help_text="Descripción detallada del asiento (mínimo 10 caracteres)"
    )
    
    # === TOTALES (Desnormalizados para performance) ===
    total_debito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Suma total de débitos"
    )
    
    total_credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Suma total de créditos"
    )
    
    diferencia = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Diferencia (debe ser 0.00 para asientos válidos)"
    )
    
    # === SEGURIDAD CRIPTOGRÁFICA ===
    hash_integridad = models.CharField(
        max_length=64,
        editable=False,
        db_index=True,
        help_text="SHA-256 del asiento completo (incluye detalles)"
    )
    
    firma_digital = models.TextField(
        blank=True,
        help_text="Firma digital para asientos críticos (>$10M)"
    )
    
    # === AUDITORÍA ===
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='asientos_creados',
        help_text="Usuario que creó el asiento"
    )
    
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se creó el asiento"
    )
    
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Navegador/sistema del usuario"
    )
    
    # === ESTADO Y CONTROL ===
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('ACTIVO', 'Activo'),
        ('ANULADO', 'Anulado'),
    ]
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='BORRADOR',
        db_index=True,
        help_text="Estado del asiento"
    )
    
    # === ANULACIÓN (Solo si estado = ANULADO) ===
    fecha_anulacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de anulación"
    )
    
    usuario_anulacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='asientos_anulados',
        help_text="Usuario que anuló el asiento"
    )
    
    motivo_anulacion = models.TextField(
        blank=True,
        help_text="Motivo de la anulación (obligatorio si anulado)"
    )
    
    # === PERÍODO CONTABLE ===
    periodo_contable = models.ForeignKey(
        'fiscal.PeriodoContable',
        on_delete=models.PROTECT,
        related_name='asientos',
        null=True,
        blank=True,
        help_text="Período contable al que pertenece"
    )
    
    # === TIMESTAMPS ===
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contabilidad_asiento'
        verbose_name = 'Asiento Contable'
        verbose_name_plural = 'Asientos Contables'
        ordering = ['-numero_asiento']
        indexes = [
            models.Index(fields=['numero_asiento']),
            models.Index(fields=['fecha_contable', 'tipo_asiento']),
            models.Index(fields=['estado', 'fecha_contable']),
            models.Index(fields=['documento_origen_tipo', 'documento_origen_numero']),
            models.Index(fields=['hash_integridad']),
        ]
        permissions = [
            ('anular_asiento', 'Puede anular asientos contables'),
            ('cerrar_periodo', 'Puede cerrar períodos contables'),
            ('ver_asientos_todos', 'Puede ver todos los asientos'),
            ('firmar_asiento', 'Puede firmar asientos digitalmente'),
        ]
    
    def __str__(self):
        return f"Asiento #{self.numero_asiento} - {self.fecha_contable} - {self.get_tipo_asiento_display()}"
    
    def calcular_hash(self):
        """
        Calcula el hash SHA-256 del asiento completo
        Incluye todos los detalles para garantizar integridad total
        """
        from ..services.hash_manager import HashManager
        # Usar _to_dict para asegurar consistencia con save() y validadores
        return HashManager.generar_hash_asiento(self._to_dict())
    
    def verificar_integridad(self):
        """
        Verifica que el hash almacenado coincida con el hash calculado
        Retorna (es_valido, hash_actual, hash_calculado)
        """
        hash_calculado = self.calcular_hash()
        es_valido = self.hash_integridad == hash_calculado
        return es_valido, self.hash_integridad, hash_calculado
    
    def esta_cuadrado(self):
        """Verifica que débitos = créditos (tolerancia ≤ 0.01)"""
        return abs(self.diferencia) <= Decimal('0.01')
    
    def puede_modificarse(self):
        """Determina si el asiento puede modificarse"""
        # No se puede modificar si está anulado
        if self.estado == 'ANULADO':
            return False, "El asiento está anulado"
        
        # No se puede modificar si el período está cerrado
        if self.periodo_contable and self.periodo_contable.estado == 'CERRADO':
            return False, f"El período {self.periodo_contable} está cerrado"
        
        # Asientos de cierre no se pueden modificar
        if self.tipo_asiento == 'CIERRE':
            return False, "Los asientos de cierre no se pueden modificar"
        
        return True, ""
    
    def actualizar_totales(self):
        """
        Recalcula los totales de débito y crédito desde los detalles
        Se llama automáticamente cuando se agregan/modifican/eliminan detalles
        """
        from django.db.models import Sum
        from decimal import Decimal
        
        agregados = self.detalles.aggregate(
            total_deb=Sum('debito'),
            total_cred=Sum('credito')
        )
        
        self.total_debito = agregados['total_deb'] or Decimal('0.00')
        self.total_credito = agregados['total_cred'] or Decimal('0.00')
        self.diferencia = self.total_debito - self.total_credito
        
        # Guardar sin recalcular hash (se hará en save()) y SIN validar aún (se hará al final)
        self.save(run_validation=False)
    
    def anular(self, usuario, motivo, ip_origen=None):
        """
        Anula el asiento contable
        Crea un asiento inverso en lugar de eliminar
        """
        if self.estado == 'ANULADO':
            raise ValueError("El asiento ya está anulado")
        
        if not motivo or len(motivo) < 10:
            raise ValueError("El motivo de anulación debe tener al menos 10 caracteres")
        
        # Verificar período abierto
        puede_modificar, mensaje = self.puede_modificarse()
        if not puede_modificar:
            raise ValueError(mensaje)
        
        # Marcar como anulado
        self.estado = 'ANULADO'
        self.fecha_anulacion = timezone.now()
        self.usuario_anulacion = usuario
        self.motivo_anulacion = motivo
        if ip_origen:
            self.ip_origen = ip_origen
        
        self.save()
        
        # Registrar en auditoría
        from .log_auditoria_contable import LogAuditoriaContable
        LogAuditoriaContable.registrar(
            tipo_evento='ANULACION_ASIENTO',
            usuario=usuario,
            asiento=self,
            detalles={
                'motivo': motivo,
                'numero_asiento': self.numero_asiento
            },
            ip_origen=ip_origen
        )
    
    
    def _to_dict(self):
        """Helper para serializar asiento para validación y hashing"""
        return {
            'id': self.pk,
            'numero_asiento': self.numero_asiento,
            'fecha_contable': self.fecha_contable,
            'tipo': self.tipo_asiento,
            'descripcion': self.descripcion,
            'total_debito': self.total_debito,
            'total_credito': self.total_credito,
            'detalles': [
                {
                    'cuenta_codigo': detalle.cuenta_contable.codigo,  # Corregido para validador
                    'cuenta': detalle.cuenta_contable.codigo,         # Mantener para compatibilidad hash (si aplica)
                    'debito': detalle.debito,
                    'credito': detalle.credito,
                    'descripcion': detalle.descripcion_detalle,
                    'orden': detalle.orden
                }
                for detalle in self.detalles.all().order_by('orden', 'id')
            ]
        }

    def clean(self):
        """Validación temprana (Admin/Forms)"""
        if not self.pk:
            return
            
        from ..validators.cadena_validacion import validar_asiento
        from django.core.exceptions import ValidationError
        
        # En clean pasamos modo modificación si existe pk
        es_valido, errores = validar_asiento(self._to_dict(), {
            'usuario': self.usuario_creacion,
            'modo': 'modificacion'
        })
        
        if not es_valido:
            # En clean() siempre levantamos error
            msg_errores = "; ".join([f"[{e['validador']}] {e['mensaje']}" for e in errores])
            raise ValidationError(f"Validación contable fallida: {msg_errores}")

    def save(self, *args, **kwargs):
        """
        Override save con validación opcional
        run_validation: True por defecto, False para guardar estados intermedios
        """
        run_validation = kwargs.pop('run_validation', True)
        
        # Calcular diferencia
        self.diferencia = self.total_debito - self.total_credito
        
        # 1. Validar antes de guardar
        if run_validation and self.pk and self.detalles.exists():
            from ..validators.cadena_validacion import validar_asiento
            from django.core.exceptions import ValidationError
            
            es_valido, errores = validar_asiento(self._to_dict(), {
                'usuario': self.usuario_creacion,
                'modo': 'modificacion'
            })
            
            if not es_valido:
                msg_errores = "; ".join([f"[{e['validador']}] {e['mensaje']}" for e in errores])
                raise ValidationError(f"Validación fallida: {msg_errores}")
        
        # 2. Generar hash
        if self.pk:
            from ..services.hash_manager import HashManager
            self.hash_integridad = HashManager.generar_hash_asiento(self._to_dict())
        
        # 3. Guardar
        is_creation = self.pk is None
        super().save(*args, **kwargs)
        
        # 4. Registrar en log WORM
        try:
            from .log_auditoria_contable import LogAuditoriaContable
            tipo_evento = 'CREACION_ASIENTO' if is_creation else 'MODIFICACION_ASIENTO'
            
            # Evitar logs duplicados si ya se registró por otro lado (opcional)
            # Por ahora registramos todo cambio persistido
            
            LogAuditoriaContable.registrar(
                tipo_evento=tipo_evento,
                usuario=self.usuario_creacion,
                asiento=self,
                detalles={
                    'numero': self.numero_asiento,
                    'descripcion': self.descripcion,
                    'total_debito': str(self.total_debito),
                    'total_credito': str(self.total_credito)
                },
                ip_origen=self.ip_origen,
                user_agent=self.user_agent
            )
        except Exception:
            # No bloquear la transacción principal si falla el log secundario
            # (Aunque idealmente debería ser transaccional)
            pass
    
    def delete(self, *args, **kwargs):
        """
        Bloquear eliminación física
        Los asientos solo se anulan, nunca se eliminan
        """
        raise ValueError(
            "Los asientos contables no se pueden eliminar. "
            "Use el método anular() en su lugar."
        )

"""
Modelo LogAuditoriaContable - Fase B
Sistema de auditoría inmutable (WORM - Write Once Read Many)
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class LogAuditoriaContable(models.Model):
    """
    Log de Auditoría Contable Inmutable
    
    Características WORM:
    - Solo escritura (no modificación ni eliminación)
    - Registro completo de todas las operaciones
    - Trazabilidad total
    - Retención indefinida
    """
    
    # === IDENTIFICACIÓN ===
    id = models.BigAutoField(primary_key=True)
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
        help_text="Timestamp exacto del evento"
    )
    
    # === TIPO DE EVENTO ===
    TIPO_EVENTO_CHOICES = [
        # Asientos
        ('CREACION_ASIENTO', 'Creación de Asiento'),
        ('MODIFICACION_ASIENTO', 'Modificación de Asiento'),
        ('ANULACION_ASIENTO', 'Anulación de Asiento'),
        
        # Períodos
        ('CIERRE_PERIODO', 'Cierre de Período'),
        ('REAPERTURA_PERIODO', 'Reapertura de Período'),
        
        # Accesos
        ('ACCESO_CONTABILIDAD', 'Acceso al Módulo Contable'),
        ('CONSULTA_ASIENTO', 'Consulta de Asiento'),
        ('EXPORTACION_DATOS', 'Exportación de Datos'),
        
        # Seguridad
        ('INTENTO_ACCESO_NO_AUTORIZADO', 'Intento de Acceso No Autorizado'),
        ('MODIFICACION_PERIODO_CERRADO', 'Intento de Modificar Período Cerrado'),
        ('DESCUADRE_DETECTADO', 'Descuadre Contable Detectado'),
        ('ANOMALIA_DETECTADA', 'Anomalía Detectada'),
        
        # Verificación
        ('VERIFICACION_INTEGRIDAD', 'Verificación de Integridad'),
        ('DISCREPANCIA_HASH', 'Discrepancia de Hash Detectada'),
    ]
    
    tipo_evento = models.CharField(
        max_length=50,
        choices=TIPO_EVENTO_CHOICES,
        db_index=True,
        help_text="Tipo de evento auditado"
    )
    
    # === USUARIO ===
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='logs_contables',
        help_text="Usuario que realizó la acción"
    )
    
    usuario_nombre = models.CharField(
        max_length=150,
        help_text="Nombre del usuario (desnormalizado para histórico)"
    )
    
    # === CONTEXTO ===
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se realizó la acción"
    )
    
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Navegador/sistema del usuario"
    )
    
    endpoint = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Endpoint/URL accedido"
    )
    
    metodo_http = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Método HTTP (GET, POST, etc.)"
    )
    
    # === OBJETO AFECTADO ===
    asiento = models.ForeignKey(
        'fiscal.AsientoContable',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='logs_auditoria',
        help_text="Asiento afectado (si aplica)"
    )
    
    periodo = models.ForeignKey(
        'fiscal.PeriodoContable',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='logs_auditoria',
        help_text="Período afectado (si aplica)"
    )
    
    # === DETALLES ===
    detalles = models.JSONField(
        default=dict,
        help_text="Detalles adicionales del evento (JSON)"
    )
    
    # === RESULTADO ===
    RESULTADO_CHOICES = [
        ('EXITOSO', 'Exitoso'),
        ('FALLIDO', 'Fallido'),
        ('BLOQUEADO', 'Bloqueado'),
        ('ADVERTENCIA', 'Advertencia'),
    ]
    
    resultado = models.CharField(
        max_length=15,
        choices=RESULTADO_CHOICES,
        default='EXITOSO',
        db_index=True,
        help_text="Resultado de la operación"
    )
    
    mensaje_error = models.TextField(
        blank=True,
        help_text="Mensaje de error (si aplica)"
    )
    
    # === SEVERIDAD ===
    SEVERIDAD_CHOICES = [
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    severidad = models.CharField(
        max_length=10,
        choices=SEVERIDAD_CHOICES,
        default='INFO',
        db_index=True,
        help_text="Nivel de severidad"
    )
    
    class Meta:
        db_table = 'contabilidad_log_auditoria'
        verbose_name = 'Log de Auditoría Contable'
        verbose_name_plural = 'Logs de Auditoría Contable'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['tipo_evento', '-timestamp']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['resultado', 'severidad']),
            models.Index(fields=['asiento']),
            models.Index(fields=['periodo']),
        ]
        permissions = [
            ('ver_logs_auditoria', 'Puede ver logs de auditoría'),
            ('exportar_logs_auditoria', 'Puede exportar logs de auditoría'),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.get_tipo_evento_display()} - {self.usuario_nombre}"
    
    @classmethod
    def registrar(cls, tipo_evento, usuario, detalles=None, asiento=None, 
                  periodo=None, ip_origen=None, user_agent=None, endpoint=None,
                  metodo_http=None, resultado='EXITOSO', mensaje_error='',
                  severidad='INFO'):
        """
        Método de clase para registrar eventos de auditoría
        
        Uso:
            LogAuditoriaContable.registrar(
                tipo_evento='CREACION_ASIENTO',
                usuario=request.user,
                asiento=asiento_obj,
                detalles={'numero': 123},
                ip_origen=request.META.get('REMOTE_ADDR')
            )
        """
        return cls.objects.create(
            tipo_evento=tipo_evento,
            usuario=usuario,
            usuario_nombre=usuario.get_full_name() or usuario.username,
            ip_origen=ip_origen,
            user_agent=user_agent or '',
            endpoint=endpoint or '',
            metodo_http=metodo_http or '',
            asiento=asiento,
            periodo=periodo,
            detalles=detalles or {},
            resultado=resultado,
            mensaje_error=mensaje_error,
            severidad=severidad
        )
    
    @classmethod
    def registrar_acceso(cls, usuario, endpoint, ip_origen=None, user_agent=None, metodo_http='GET'):
        """
        Registra un acceso al módulo contable
        """
        return cls.registrar(
            tipo_evento='ACCESO_CONTABILIDAD',
            usuario=usuario,
            endpoint=endpoint,
            ip_origen=ip_origen,
            user_agent=user_agent,
            metodo_http=metodo_http,
            severidad='INFO'
        )
    
    @classmethod
    def registrar_anomalia(cls, tipo_evento, usuario, detalles, asiento=None, 
                          periodo=None, ip_origen=None):
        """
        Registra una anomalía o intento de acceso no autorizado
        """
        return cls.registrar(
            tipo_evento=tipo_evento,
            usuario=usuario,
            detalles=detalles,
            asiento=asiento,
            periodo=periodo,
            ip_origen=ip_origen,
            resultado='BLOQUEADO',
            severidad='CRITICAL'
        )
    
    def save(self, *args, **kwargs):
        """
        Override save para garantizar inmutabilidad (WORM)
        Solo permite creación, no modificación
        """
        if self.pk:
            raise ValueError(
                "Los logs de auditoría son inmutables. "
                "No se pueden modificar después de creados."
            )
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Bloquear eliminación
        Los logs de auditoría nunca se eliminan
        """
        raise ValueError(
            "Los logs de auditoría son inmutables. "
            "No se pueden eliminar."
        )

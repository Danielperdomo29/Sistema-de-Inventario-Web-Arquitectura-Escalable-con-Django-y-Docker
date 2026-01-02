from django.db import models
from django.utils.translation import gettext_lazy as _
from app.models.sale import Sale

class FacturaElectronica(models.Model):
    """
    Modelo para gestionar la Facturación Electrónica (DIAN)
    Vincula una Venta (Sale) con su representación fiscal digital.
    """
    
    ESTADOS_DIAN = [
        ('PENDIENTE', 'Pendiente de Envío'),
        ('GENERADO', 'XML Generado'),
        ('FIRMADO', 'XML Firmado'),
        ('ENVIADO', 'Enviado a DIAN'),
        ('ACEPTADO', 'Aceptado por DIAN'),
        ('RECHAZADO', 'Rechazado por DIAN'),
        ('ERROR', 'Error Técnico'),
    ]
    
    AMBIENTES = [
        (1, 'Producción'),
        (2, 'Pruebas'),
    ]
    
    # Vinculación con negocio
    venta = models.OneToOneField(
        Sale, 
        on_delete=models.PROTECT,
        related_name='factura_electronica',
        verbose_name=_('Venta asociada')
    )
    
    # Número de Factura
    numero_factura = models.CharField(
        max_length=50,
        unique=True,
        null=True,  # Temporarily nullable for migration
        blank=True,
        verbose_name=_('Número de Factura'),
        help_text="Número completo de factura (Prefijo + Consecutivo)"
    )
    
    prefijo = models.CharField(
        max_length=10,
        null=True,  # Temporarily nullable for migration
        blank=True,
        verbose_name=_('Prefijo'),
        help_text="Prefijo del rango de numeración"
    )
    
    # Identificadores Fiscales
    cufe = models.CharField(
        max_length=96, 
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('Código Único de Factura Electrónica')
    )
    
    qrcode = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Datos QR')
    )
    
    # Archivos
    archivo_xml = models.FileField(
        upload_to='fiscal/xml/firmados/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('XML Firmado')
    )
    
    archivo_pdf = models.FileField(
        upload_to='fiscal/pdf/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('PDF Representación Gráfica')
    )
    
    xml_firmado = models.FileField(
        upload_to='fiscal/xml/firmados/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('XML Firmado (Legacy)')
    )
    
    xml_respuesta_dian = models.FileField(
        upload_to='fiscal/xml/respuestas/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('ApplicationResponse DIAN')
    )
    
    # Estado y Control
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('generada', 'Generada'),
            ('firmada', 'Firmada'),
            ('enviada', 'Enviada a DIAN'),
            ('aceptada', 'Aceptada'),
            ('rechazada', 'Rechazada'),
        ],
        default='pendiente',
        db_index=True,
        verbose_name=_('Estado')
    )
    
    estado_dian = models.CharField(
        max_length=20,
        choices=ESTADOS_DIAN,
        default='PENDIENTE',
        db_index=True,
        verbose_name=_('Estado DIAN (Detallado)')
    )
    
    ambiente = models.IntegerField(
        choices=AMBIENTES,
        default=2, # Default a Pruebas
        verbose_name=_('Ambiente de Habilitación')
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Actualización')
    )
    
    fecha_emision = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('Fecha Emisión (Firma)')
    )
    
    fecha_envio = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('Fecha Envío DIAN')
    )
    
    intentos_envio = models.PositiveIntegerField(default=0)
    
    mensaje_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'fiscal_factura_electronica'
        verbose_name = 'Factura Electrónica'
        verbose_name_plural = 'Facturas Electrónicas'
        permissions = [
            ('emitir_factura_electronica', 'Puede emitir facturas electrónicas'),
            ('consultar_estado_dian', 'Puede consultar estado en DIAN'),
        ]

    def __str__(self):
        return f"FE-{self.venta.id} ({self.get_estado_dian_display()})"

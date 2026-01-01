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
    xml_firmado = models.FileField(
        upload_to='fiscal/xml/firmados/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('XML Firmado')
    )
    
    xml_respuesta_dian = models.FileField(
        upload_to='fiscal/xml/respuestas/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('ApplicationResponse DIAN')
    )
    
    # Estado y Control
    estado_dian = models.CharField(
        max_length=20,
        choices=ESTADOS_DIAN,
        default='PENDIENTE',
        db_index=True
    )
    
    ambiente = models.IntegerField(
        choices=AMBIENTES,
        default=2, # Default a Pruebas
        verbose_name=_('Ambiente de Habilitación')
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

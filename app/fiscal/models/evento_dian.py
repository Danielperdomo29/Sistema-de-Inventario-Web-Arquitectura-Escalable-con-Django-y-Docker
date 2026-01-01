from django.db import models
from django.utils.translation import gettext_lazy as _

class EventoDian(models.Model):
    """
    Log de eventos y respuestas de la DIAN asociados a una Factura Electrónica.
    Permite trazabilidad completa del ciclo de vida del documento.
    """
    
    factura = models.ForeignKey(
        'fiscal.FacturaElectronica',
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name=_('Factura Electrónica')
    )
    
    codigo_evento = models.CharField(
        max_length=10,
        verbose_name=_('Código de Respuesta')
    )
    # Ej: '02' (Recibido), '04' (Rechazado)
    
    descripcion = models.TextField(
        verbose_name=_('Descripción del Evento')
    )
    
    xml_evento = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('XML del Evento (ApplicationResponse)')
    )
    
    fecha_evento = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha del Evento')
    )
    
    es_error = models.BooleanField(
        default=False,
        verbose_name=_('Es Error')
    )
    
    detalles = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Detalles Adicionales')
    )
    
    class Meta:
        db_table = 'fiscal_evento_dian'
        verbose_name = 'Evento DIAN'
        verbose_name_plural = 'Eventos DIAN'
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"{self.codigo_evento} - {self.fecha_evento}"

from django.db import models
from app.models.sale import Sale

class FacturaDIAN(models.Model):
    """Modelo para Factura Electrónica DIAN"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('generada', 'Generada'),
        ('enviada', 'Enviada'),
        ('rechazada', 'Rechazada'),
    ]

    venta = models.OneToOneField(Sale, on_delete=models.PROTECT, related_name='factura_dian')
    numero_factura = models.CharField(max_length=50, unique=True, help_text="Número oficial de facturación (Prefijo + Consecutivo)")
    cufe = models.CharField(max_length=150, blank=True, null=True, help_text="Código Único de Facturación Electrónica")
    
    # Archivos generados
    archivo_xml = models.FileField(upload_to='dian/xml/', blank=True, null=True)
    archivo_pdf = models.FileField(upload_to='dian/pdf/', blank=True, null=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facturas_dian'
        verbose_name = 'Factura DIAN'
        verbose_name_plural = 'Facturas DIAN'

    def __str__(self):
        return f"{self.numero_factura} ({self.estado})"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from app.models.sale import Sale
from app.fiscal.models import FacturaElectronica, EventoDian
from app.fiscal.core.factura_xml_generator import GeneradorXMLDIAN
from app.fiscal.core.cufe import GeneradorCUFE
from app.fiscal.core.firma_digital import FirmadorDIAN
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Sale)
def generar_factura_electronica_automatica(sender, instance, created, **kwargs):
    if instance.estado != 'completada':
        return

    # Evitar duplicados
    if hasattr(instance, 'factura_electronica'):
        return

    try:
        # 1. Crear estructura base de Factura
        factura = FacturaElectronica.objects.create(
            venta=instance,
            estado_dian='PENDIENTE',
            ambiente=2 # Pruebas por defecto
        )

        # 2. Calcular CUFE
        generador_cufe = GeneradorCUFE()
        cufe = generador_cufe.calcular_cufe(
            nit_emisor='900123456', # Debe venir de PerfilFiscal
            fecha_emision=instance.fecha.date().isoformat(),
            numero_factura=instance.numero_factura,
            valor_total=str(instance.total),
            iva=str(getattr(instance, 'total_iva', 0)), # Ajustar si Sale tiene IVA desagregado
            total_impuestos=str(getattr(instance, 'total_impuestos', 0))
        )
        
        # 3. Generar XML
        generador_xml = GeneradorXMLDIAN()
        # Asignar CUFE temporalmente al objeto factura (sin guardar aun) para que vaya en el XML
        factura.cufe = cufe 
        xml_content = generador_xml.generar_xml_factura(factura)

        # 4. Firmar XML
        firmador = FirmadorDIAN()
        xml_firmado = firmador.firmar_xml(xml_content)

        # 5. Guardar todo
        import django.core.files.base
        from django.core.files.base import ContentFile
        
        filename = f"fe_{instance.numero_factura}.xml"
        factura.xml_firmado.save(filename, ContentFile(xml_firmado.encode('utf-8')), save=False)
        
        factura.cufe = cufe
        factura.fecha_emision = timezone.now()
        factura.estado_dian = 'GENERADO' # Listo para enviar
        factura.save()
        
        logger.info(f"Factura Electrónica generada para Venta {instance.id}")

    except Exception as e:
        logger.error(f"Error generando Factura Electrónica para Venta {instance.id}: {str(e)}")
        import traceback
        traceback.print_exc()

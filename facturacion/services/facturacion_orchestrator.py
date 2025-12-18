from django.db import transaction
from django.core.files.base import ContentFile
from .numeracion_service import NumeracionService
from .xml_generator import XMLGeneratorService
from .pdf_generator import PDFGeneratorService
from facturacion.models import FacturaDIAN
from app.models.sale import Sale

class FacturacionOrchestrator:
    @staticmethod
    def generar_documentos(sale_id):
        """
        Orquesta la generación de factura electrónica:
        1. Valida venta
        2. Genera numeración
        3. Genera XML
        4. Genera PDF
        5. Guarda todo en FacturaDIAN
        """
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            raise ValueError("Venta no encontrada")

        if hasattr(sale, 'factura_dian'):
             raise ValueError(f"La venta {sale.numero_factura} ya tiene factura electrónica generada.")

        with transaction.atomic():
            # 1. Numeración
            numero_factura = NumeracionService.get_next_number()
            
            # 2. Crear instancia (Placeholder)
            factura = FacturaDIAN.objects.create(
                venta=sale,
                numero_factura=numero_factura,
                estado='pendiente'
            )
            
            # 3. Calcular Impuestos y Datos DIAN
            from .tax_calculator import TaxCalculatorService
            invoice_data = TaxCalculatorService.calculate_sale_totals(sale)
            
            # 4. Generar XML
            xml_service = XMLGeneratorService(invoice_data)
            xml_content = xml_service.generate(numero_factura)
            
            # Ensure directory exists (Defensive)
            import os
            from django.conf import settings
            xml_dir = os.path.join(settings.MEDIA_ROOT, 'dian', 'xml')
            os.makedirs(xml_dir, exist_ok=True)
            
            factura.archivo_xml.save(f'{numero_factura}.xml', ContentFile(xml_content), save=False)
            
            # 5. Generar PDF
            pdf_service = PDFGeneratorService(invoice_data)
            pdf_content = pdf_service.generate(numero_factura)
            
            # Ensure directory exists (Defensive)
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'dian', 'pdf')
            os.makedirs(pdf_dir, exist_ok=True)
            
            factura.archivo_pdf.save(f'{numero_factura}.pdf', ContentFile(pdf_content), save=False)
            
            # 5. Finalizar
            factura.estado = 'generada'
            factura.save()
            
            return factura

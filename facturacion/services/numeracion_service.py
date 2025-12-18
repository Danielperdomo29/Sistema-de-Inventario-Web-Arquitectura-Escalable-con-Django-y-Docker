from app.models.sale import Sale
from facturacion.models import FacturaDIAN
from django.db.models import Max

class NumeracionService:
    @staticmethod
    def get_next_number():
        """Genera el siguiente número de factura consecutivo"""
        # Prefijo de facturación electrónica
        PREFIX = "SETP" 
        
        # Obtener el último número generado
        last_invoice = FacturaDIAN.objects.all().order_by('-id').first()
        
        if not last_invoice:
            return f"{PREFIX}1"
        
        # Extraer número actual (asumiendo formato PREFIX+NUM)
        try:
            current_num = int(last_invoice.numero_factura.replace(PREFIX, ""))
            next_num = current_num + 1
        except ValueError:
            # Fallback por si el formato cambia
            next_num = FacturaDIAN.objects.count() + 1
            
        return f"{PREFIX}{next_num}"

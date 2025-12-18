from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .services.facturacion_orchestrator import FacturacionOrchestrator

@login_required # Security: Only authenticated users
def generar_factura_dian(request, sale_id):
    """
    Vista controlada para generar la factura DIAN.
    """
    try:
        factura = FacturacionOrchestrator.generar_documentos(sale_id)
        messages.success(request, f"Factura {factura.numero_factura} generada correctamente.")
    except Exception as e:
        messages.error(request, f"Error generando factura: {str(e)}")
    
    # Redireccionar al detalle de la venta
    return redirect('sales_view', sale_id=sale_id)

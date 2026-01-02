#!/usr/bin/env python
"""Test invoice generation for sale ID 4"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from app.models.sale import Sale
from app.fiscal.models import FiscalConfig, RangoNumeracion, FacturaElectronica
from app.fiscal.services.invoice_service import InvoiceGenerationService

def test_sale_4():
    print("Testing invoice generation for Sale ID=4")
    print("=" * 50)
    
    # Check sale exists
    try:
        sale = Sale.objects.get(id=4)
        print(f"Sale found: ID={sale.id}")
        print(f"  - numero_factura: {sale.numero_factura}")
        print(f"  - cliente: {sale.cliente}")
        print(f"  - total: {sale.total}")
        print(f"  - detalles count: {sale.detalles.count()}")
    except Sale.DoesNotExist:
        print("ERROR: Sale ID=4 not found!")
        return
    
    # Check if already has factura
    try:
        fe = FacturaElectronica.objects.filter(venta_id=4).first()
        if fe:
            print(f"\nFactura already exists: {fe.numero_factura}")
            print(f"  - CUFE: {fe.cufe[:32] if fe.cufe else 'None'}...")
            print(f"  - PDF: {fe.archivo_pdf.name if fe.archivo_pdf else 'None'}")
            return
    except Exception as e:
        print(f"Error checking factura: {e}")
    
    # Check fiscal config
    config = FiscalConfig.objects.filter(is_active=True).first()
    if not config:
        print("ERROR: No active FiscalConfig!")
        return
    print(f"\nFiscalConfig: ID={config.id}")
    
    # Check rango
    rango = RangoNumeracion.objects.filter(
        fiscal_config=config, 
        estado='activo', 
        is_default=True
    ).first()
    if not rango:
        print("ERROR: No active RangoNumeracion!")
        return
    print(f"RangoNumeracion: ID={rango.id}, prefijo={rango.prefijo}")
    
    # Try to generate invoice
    print("\nGenerating invoice...")
    try:
        factura, xml = InvoiceGenerationService.generar_factura_electronica(sale)
        print(f"SUCCESS! Factura: {factura.numero_factura}")
        print(f"  - CUFE: {factura.cufe[:32]}...")
        print(f"  - PDF: {factura.archivo_pdf.name if factura.archivo_pdf else 'None'}")
    except Exception as e:
        print(f"ERROR generating invoice: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    test_sale_4()

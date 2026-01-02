#!/usr/bin/env python
"""
Debug script to test invoice generation step by step
"""
import os
import sys
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from app.models.sale import Sale
from app.fiscal.models import FiscalConfig, RangoNumeracion, FacturaElectronica

def test_invoice_generation():
    print("=" * 60)
    print("DEBUG: Testing Invoice Generation")
    print("=" * 60)
    
    # Step 1: Check FiscalConfig
    print("\n[1] Checking FiscalConfig...")
    config = FiscalConfig.objects.filter(is_active=True).first()
    if not config:
        print("   ❌ No active FiscalConfig found!")
        return
    print(f"   ✓ FiscalConfig ID={config.id}, NIT={config.nit_emisor}")
    
    # Step 2: Check RangoNumeracion
    print("\n[2] Checking RangoNumeracion...")
    from app.fiscal.services.numeracion_service import NumeracionService
    try:
        numero, rango = NumeracionService.obtener_siguiente_numero(config.id)
        print(f"   ✓ Next number: {numero}")
        print(f"   ✓ Rango ID={rango.id}, prefix={rango.prefijo}")
    except Exception as e:
        print(f"   ❌ Error getting number: {e}")
        traceback.print_exc()
        return
    
    # Step 3: Get a sale
    print("\n[3] Checking Sales...")
    sale = Sale.objects.filter(estado='completada').first()
    if not sale:
        sale = Sale.objects.first()
    if not sale:
        print("   ❌ No sales found!")
        return
    print(f"   ✓ Sale ID={sale.id}, numero={sale.numero_factura}")
    print(f"   ✓ Cliente: {sale.cliente.nombre if sale.cliente else 'None'}")
    print(f"   ✓ Total: ${sale.total}")
    print(f"   ✓ Detalles: {sale.detalles.count()} items")
    
    # Check if already has factura
    if hasattr(sale, 'factura_electronica'):
        existing = getattr(sale, 'factura_electronica', None)
        if existing:
            print(f"   ⚠️ Sale already has factura: {existing.numero_factura}")
    
    # Step 4: Test CUFE generation
    print("\n[4] Testing CUFE generation...")
    try:
        from app.fiscal.services.invoice_service import InvoiceGenerationService
        from app.fiscal.core.dian.formatters import DIANFormatter
        from django.utils import timezone
        from decimal import Decimal
        
        # Prepare CUFE data
        ahora = timezone.now()
        fecha_str, hora_str = DIANFormatter.formatear_datetime_completo(ahora)
        
        subtotal = sale.subtotal or Decimal('0')
        total_iva = sale.iva_total or Decimal('0')
        total = sale.total or Decimal('0')
        
        print(f"   Subtotal: ${subtotal}")
        print(f"   IVA: ${total_iva}")
        print(f"   Total: ${total}")
        
        if not subtotal:
            print("   ⚠️ Subtotal is 0, calculating from details...")
            items = sale.detalles.all()
            for item in items:
                print(f"      - {item.producto.nombre}: {item.cantidad} x ${item.precio_unitario}")
        
    except Exception as e:
        print(f"   ❌ Error in CUFE prep: {e}")
        traceback.print_exc()
    
    # Step 5: Test UBL Mapping
    print("\n[5] Testing UBL Mapping...")
    try:
        from app.fiscal.core.dian.ubl_mapper import UBLMapper
        
        ubl_data = UBLMapper.map_sale_to_ubl_data(
            sale=sale,
            fiscal_config=config,
            numero_factura=numero,
            cufe="test_cufe_placeholder"
        )
        print(f"   ✓ UBL data mapped successfully")
        print(f"   Keys: {list(ubl_data.keys())}")
        
        if 'items' in ubl_data:
            print(f"   Items: {len(ubl_data['items'])} productos")
        if 'totales' in ubl_data:
            print(f"   Totales: {ubl_data['totales']}")
            
    except Exception as e:
        print(f"   ❌ Error in UBL mapping: {e}")
        traceback.print_exc()
    
    # Step 6: Test PDF Generation
    print("\n[6] Testing PDF Generation...")
    try:
        from app.fiscal.services.pdf_generator import InvoicePDFGenerator
        
        pdf_gen = InvoicePDFGenerator(ubl_data, config)
        pdf_buffer = pdf_gen.generar_pdf()
        
        print(f"   ✓ PDF generated: {len(pdf_buffer.getvalue())} bytes")
        
        # Save test PDF
        test_path = os.path.join(os.path.dirname(__file__), 'test_invoice.pdf')
        with open(test_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"   ✓ Saved to: {test_path}")
        
    except Exception as e:
        print(f"   ❌ Error generating PDF: {e}")
        traceback.print_exc()
    
    # Step 7: Test full invoice generation (if no existing factura)
    print("\n[7] Testing Full Invoice Generation...")
    try:
        from app.fiscal.services.invoice_service import InvoiceGenerationService
        
        # Find a sale without factura
        sales_without_factura = Sale.objects.exclude(
            id__in=FacturaElectronica.objects.values_list('venta_id', flat=True)
        )
        
        test_sale = sales_without_factura.first()
        if not test_sale:
            print("   ⚠️ All sales already have facturas. Cannot test full generation.")
            print("   Create a new sale to test.")
            return
        
        print(f"   Testing with Sale ID={test_sale.id}")
        
        factura, xml_string = InvoiceGenerationService.generar_factura_electronica(test_sale)
        
        print(f"   ✓ Factura created: {factura.numero_factura}")
        print(f"   ✓ CUFE: {factura.cufe[:32]}...")
        print(f"   ✓ XML: {len(xml_string)} bytes")
        if factura.archivo_pdf:
            print(f"   ✓ PDF: {factura.archivo_pdf.name}")
        else:
            print("   ⚠️ PDF not saved")
        
    except Exception as e:
        print(f"   ❌ Error in full generation: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    test_invoice_generation()

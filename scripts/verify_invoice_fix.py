#!/usr/bin/env python
"""
Script to verify the Sale.get_by_id fix for factura_electronica
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django - using settings from init_django which sets things up correctly
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from app.models.sale import Sale
from app.fiscal.models import FacturaElectronica

def verify_fix():
    print("=" * 50)
    print("Verificando fix de factura_electronica")
    print("=" * 50)
    
    # 1. Check if there are any sales
    sale = Sale.objects.first()
    if not sale:
        print("No hay ventas en la base de datos.")
        return
    
    print(f"\n1. Sale encontrada: ID={sale.id}")
    
    # 2. Check if the sale has factura_electronica via ORM
    has_factura = hasattr(sale, 'factura_electronica')
    print(f"2. Sale tiene atributo 'factura_electronica': {has_factura}")
    
    if has_factura:
        factura = getattr(sale, 'factura_electronica', None)
        if factura:
            print(f"   - Factura encontrada: {factura.numero_factura}")
            print(f"   - CUFE: {factura.cufe[:32]}..." if factura.cufe else "   - CUFE: None")
            print(f"   - PDF: {factura.archivo_pdf.name if factura.archivo_pdf else 'None'}")
    
    # 3. Test get_by_id method
    print("\n3. Probando Sale.get_by_id()...")
    sale_data = Sale.get_by_id(sale.id)
    
    if 'factura_dian' in sale_data:
        print("   - 'factura_dian' key exists in result: OK")
        factura_val = sale_data.get('factura_dian')
        print(f"   - Value: {type(factura_val).__name__ if factura_val else 'None'}")
        if factura_val:
            print(f"   - Numero: {factura_val.numero_factura}")
    else:
        print("   - 'factura_dian' key NOT in result: ERROR")
    
    # 4. Check total invoices
    total_invoices = FacturaElectronica.objects.count()
    print(f"\n4. Total FacturaElectronica en DB: {total_invoices}")
    
    print("\n" + "=" * 50)
    print("Verificacion completada!")
    print("=" * 50)

if __name__ == '__main__':
    verify_fix()

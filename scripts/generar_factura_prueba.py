#!/usr/bin/env python3
"""
Script para generar factura de prueba y validar manualmente
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Agregar ruta del proyecto (ajustar según tu estructura real)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") # Ajustar settings
import django
django.setup()

def generar_factura_prueba():
    """Generar una factura de prueba con los componentes implementados"""
    from app.fiscal.core.factura_xml_generator import GeneradorXMLDIAN
    from app.fiscal.core.cufe import GeneradorCUFE
    from app.fiscal.core.firma_digital import FirmadorDIAN
    
    # Mock de objetos (ya que requeriría crear Venta real en BD)
    class ProductoMock:
        nombre = "Producto Prueba"
        
    class DetalleMock:
        cantidad = 1.0
        subtotal = 100000.00
        precio_unitario = 100000.00
        producto = ProductoMock()
        
    class VentaMock:
        id = 9999
        numero = 'SETP9900000001' # No usado directamente en generador actual pero sí en lógica
        numero_factura = 'SETP9900000001'
        fecha = datetime.now()
        subtotal = 100000.00
        total = 119000.00
        resolucion_facturacion = '18760000001'
        detalles = type('Manager', (object,), {'all': staticmethod(lambda: [DetalleMock()])})()
        # Mocking Empresa/Cliente relations (simplificado)
        empresa = None 
        cliente = None

    class FacturaMock:
        cufe = None
        venta = VentaMock()
        
    
    print("=" * 60)
    print("GENERADOR DE FACTURA DE PRUEBA DIAN (MOCK)")
    print("=" * 60)
    
    try:
        factura_mock = FacturaMock()
        venta_mock = factura_mock.venta
        
        # 1. Calcular CUFE
        print("\n1. [KEY] Calculando CUFE...")
        generador_cufe = GeneradorCUFE()
        cufe = generador_cufe.calcular_cufe(
            nit_emisor='900123456',
            fecha_emision=venta_mock.fecha.date().isoformat(),
            numero_factura=venta_mock.numero_factura,
            valor_total=str(venta_mock.total),
            iva='19000.00',
            total_impuestos='19000.00'
        )
        factura_mock.cufe = cufe
        print(f"   [OK] CUFE generado: {cufe}")
        
        # 2. Generar XML
        print("\n2. [XML] Generando XML...")
        generador_xml = GeneradorXMLDIAN()
        xml_str = generador_xml.generar_xml_factura(factura_mock)
        
        # Guardar XML sin firmar
        temp_dir = tempfile.gettempdir()
        xml_path = os.path.join(temp_dir, 'factura_prueba.xml')
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
            
        print(f"   [OK] XML generado: {xml_path}")
        print(f"   [SIZE] Tamano: {len(xml_str)} bytes")
        
        # 3. Firmar XML
        print("\n3. [SIG] Firmando XML...")
        firmador = FirmadorDIAN()
        xml_firmado = firmador.firmar_xml(xml_str)
        print(f"   [OK] XML Firmado (Simulado)")

        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"XML guardado en: {xml_path}")
        print("Puede subir este archivo al validador de la DIAN.")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generar_factura_prueba()

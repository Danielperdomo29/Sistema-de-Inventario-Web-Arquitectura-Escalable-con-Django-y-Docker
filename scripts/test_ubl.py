import os
import sys
import django
from decimal import Decimal
from datetime import datetime, date

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.fiscal.models.fiscal_config import FiscalConfig
from app.fiscal.core.dian.crypto_manager import FiscalCryptoManager
from app.fiscal.core.dian.ubl_generator import UBLGeneratorService

def test_ubl_generation():
    print("=== Prueba de Generación UBL 2.1 ===\n")
    
    # 1. Obtener configuración
    config = FiscalConfig.objects.first()
    if not config:
        print("[!] ERROR: No hay configuración fiscal. Ejecuta 'python scripts/generate_test_cert.py' primero.")
        return
    
    print(f"[OK] Usando configuración: {config.razon_social}")
    print(f"     Prefijo: {config.prefijo}, Resolución: {config.numero_resolucion}\n")
    
    # 2. Preparar datos de factura de prueba
    factura_data = {
        'numero_factura': f'{config.prefijo}99000001',
        'fecha_emision': date.today(),
        'hora_emision': '14:30:00-05:00',
        'cliente': {
            'nit': '900123456',
            'razon_social': 'Cliente Ejemplo S.A.S',
            'direccion': 'Calle 100 # 20-30',
            'ciudad': 'Bogotá',
            'email': 'cliente@ejemplo.com',
        },
        'items': [
            {
                'descripcion': 'Producto de Prueba 1',
                'cantidad': 2,
                'precio_unitario': Decimal('50000.00'),
                'valor_total': Decimal('100000.00'),
            },
            {
                'descripcion': 'Producto de Prueba 2',
                'cantidad': 1,
                'precio_unitario': Decimal('30000.00'),
                'valor_total': Decimal('30000.00'),
            },
        ],
        'subtotal': Decimal('130000.00'),
        'total_iva': Decimal('24700.00'),  # 19% sobre 130000
        'total_consumo': Decimal('0.00'),
        'total_ica': Decimal('0.00'),
        'total_factura': Decimal('154700.00'),
        'nit_emisor': config.nit_emisor,
        'nit_adquirente': '900123456',
    }
    
    # 3. Generar CUFE
    print("Generando CUFE...")
    crypto = FiscalCryptoManager(config.certificado_archivo.path, config.get_password())
    cufe = crypto.generar_cufe(factura_data, config.clave_tecnica, ambiente=str(config.ambiente))
    factura_data['cufe'] = cufe
    print(f"[OK] CUFE: {cufe[:64]}...\n")
    
    # 4. Generar XML UBL 2.1
    print("Generando XML UBL 2.1...")
    generator = UBLGeneratorService(config)
    xml_content = generator.generar_xml(factura_data)
    
    # 5. Guardar XML en archivo
    output_dir = os.path.join('media', 'fiscal', 'xml', 'test')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{factura_data["numero_factura"]}.xml')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"[OK] XML generado exitosamente")
    print(f"     Archivo: {output_path}")
    print(f"     Tamaño: {len(xml_content)} bytes")
    
    # 6. Mostrar preview
    print("\n--- Preview XML (primeras 50 líneas) ---")
    lines = xml_content.split('\n')
    for line in lines[:50]:
        print(line)
    
    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} líneas adicionales)")
    
    print("\n[OK] Prueba completada. Revisa el archivo XML generado.")

if __name__ == '__main__':
    test_ubl_generation()

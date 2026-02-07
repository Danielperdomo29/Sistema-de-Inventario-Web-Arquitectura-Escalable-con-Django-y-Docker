"""
Test rápido de OCR con imagen
"""
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, r'C:\dev\Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from app.services.ocr_service import receipt_extractor
import tempfile
import shutil

print("=" * 60)
print("TEST DE OCR CON IMAGEN")
print("=" * 60)

# Solicitar ruta de la imagen
ruta_imagen = input("\nIngresa la ruta completa de la imagen de prueba: ")

if not os.path.exists(ruta_imagen):
    print(f"❌ ERROR: Archivo no existe: {ruta_imagen}")
    sys.exit(1)

print(f"\n✅ Archivo encontrado: {ruta_imagen}")
print(f"📏 Tamaño: {os.path.getsize(ruta_imagen) / 1024:.1f} KB")

print("\n" + "=" * 60)
print("INICIANDO EXTRACCIÓN...")
print("=" * 60 + "\n")

try:
    result = receipt_extractor.extract_all_fields(ruta_imagen)
    
    print("\n" + "=" * 60)
    print("RESULTADO:")
    print("=" * 60)
    print(f"✅ Éxito: {result['success']}")
    print(f"💰 Total: {result.get('total', 'NO ENCONTRADO')}")
    print(f"🎯 Confianza: {result.get('confidence', 0) * 100:.1f}%")
    print(f"📄 Número Factura: {result.get('invoice_number', 'NO ENCONTRADO')}")
    print(f"📅 Fecha: {result.get('date', 'NO ENCONTRADA')}")
    print(f"🏢 Proveedor: {result.get('supplier_name', 'NO ENCONTRADO')}")
    
    if not result['success']:
        print(f"\n❌ Error: {result.get('error', 'Desconocido')}")
    
    print("\n" + "=" * 60)
    print("TEXTO EXTRAÍDO (primeros 500 caracteres):")
    print("=" * 60)
    print(result.get('extracted_text', '')[:500])
    print("...")
    
except Exception as e:
    print(f"\n❌ ERROR FATAL: {type(e).__name__}: {str(e)}")
    import traceback
    print("\nStack trace:")
    traceback.print_exc()

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)

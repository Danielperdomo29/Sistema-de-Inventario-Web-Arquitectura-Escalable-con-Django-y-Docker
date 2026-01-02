import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.fiscal.models.fiscal_config import FiscalConfig
from app.fiscal.core.dian.crypto_manager import FiscalCryptoManager

def test_crypto():
    print("=== Iniciando Prueba de Crypto Manager ===")
    
    # 1. Buscar Configuración
    try:
        config = FiscalConfig.objects.first()
        if not config or not config.certificado_archivo:
            print("[!] ERROR: No se encontró configuración fiscal o certificado cargado.")
            print("    Por favor ve a /fiscal/configuracion/ y carga un archivo .p12")
            return
            
        print(f"[OK] Configuración encontrada: {config.razon_social}")
        print(f"[OK] Archivo certificado: {config.certificado_archivo.path}")
    except Exception as e:
        print(f"[!] Error accediendo a DB: {e}")
        return

    # 2. Desencriptar Contraseña
    password = config.get_password()
    if not password:
         print("[!] ERROR: No se pudo verificar la contraseña del certificado. Asegúrate de haberla guardado correctamente.")
         # Fallback temporal para pruebas locales si falló la desencriptación (opcional)
         return

    # 3. Inicializar Manager (Carga de Certificado)
    try:
        print("Intentando cargar certificado .p12...")
        crypto = FiscalCryptoManager(config.certificado_archivo.path, password)
        print("[OK] Certificado cargado exitosamente.")
        print(f"     Emisor: {crypto.cert.issuer}")
        print(f"     Sujeto: {crypto.cert.subject}")
    except Exception as e:
        print(f"[!] ERROR CARGANDO CERTIFICADO: {str(e)}")
        print("    Verifique que la contraseña sea correcta y el archivo sea un .p12 válido.")
        return

    # 4. Probar Generación de CUFE
    print("\nProbando Generación de CUFE (Mock Data)...")
    mock_data = {
        'numero_factura': 'SETP99000001',
        'fecha_emision': '2024-01-24',
        'hora_emision': '12:00:00-05:00',
        'total_factura': Decimal('119000.00'),
        'total_iva': Decimal('19000.00'),
        'total_consumo': Decimal('0.00'),
        'total_ica': Decimal('0.00'),
        'nit_emisor': config.nit_emisor,
        'nit_adquirente': '222222222222',
    }
    clave_tecnica = "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c" # Ejemplo DIAN
    
    try:
        cufe = crypto.generar_cufe(mock_data, clave_tecnica, ambiente='2')
        print(f"[OK] CUFE Generado: {cufe}")
        print(f"     Longitud: {len(cufe)} caracteres (SHA-384)")
    except Exception as e:
        print(f"[!] Error generando CUFE: {e}")

if __name__ == '__main__':
    test_crypto()

import os
import sys
import django
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import pkcs12

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from app.fiscal.models.fiscal_config import FiscalConfig

def generate_self_signed_cert():
    print("=== Generando Certificado de Prueba (Self-Signed) ===")

    # 1. Configurar Rutas
    cert_dir = os.path.join(settings.MEDIA_ROOT, 'fiscal', 'certs')
    os.makedirs(cert_dir, exist_ok=True)
    p12_filename = 'certificado_prueba.p12'
    p12_path = os.path.join(cert_dir, p12_filename)

    # 2. Generar Llave Privada
    print("Generando llave RSA (2048 bits)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 3. Datos del Certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"CO"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Bogota"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Bogota"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Empresa de Prueba S.A.S"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"empresa-prueba.com"),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, u"900123456"), # NIT ficticio
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        # Válido por 1 año
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256())

    print("Certificado X.509 generado.")

    # 4. Empaquetar en PKCS#12 (.p12)
    password = b"pruebas123" # Contraseña dummy
    p12_data = pkcs12.serialize_key_and_certificates(
        name=b"test-key",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )

    with open(p12_path, "wb") as f:
        f.write(p12_data)
    
    print(f"Archivo .p12 guardado en: {p12_path}")

    # 5. Guardar en Base de Datos (FiscalConfig)
    print("Actualizando Configuración Fiscal en BD...")
    config, created = FiscalConfig.objects.get_or_create(
        defaults={
            'nit_emisor': '890900943', # Alkonprar NIT Base
            'dv_emisor': '1',
            'razon_social': 'ALKONPRAR S.A.',
            'ambiente': 2, # Pruebas
            # Resolución Test
            'numero_resolucion': '18760000001',
            'fecha_resolucion': datetime.now().date(),
            'prefijo': 'SETP',
            'rango_desde': 99000000,
            'rango_hasta': 99500000,
            'clave_tecnica': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c'
        }
    )

    if not created:
         # Update existing
         config.nit_emisor = '890900943'
         config.dv_emisor = '1'
         config.razon_social = 'ALKONPRAR S.A.'
         config.numero_resolucion = '18760000001'
         config.fecha_resolucion = datetime.now().date()
         config.prefijo = 'SETP'
         config.clave_tecnica = 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c'
         config.save()
    
    # Simular guardado de archivo (FileField)
    # Django FileField espera un path relativo a MEDIA_ROOT
    relative_path = os.path.join('fiscal', 'certs', p12_filename)
    config.certificado_archivo.name = relative_path
    
    # Encriptar y guardar contraseña
    config.set_password("pruebas123")
    config.save()
    
    print(f"[OK] Configuración actualizada para: {config.razon_social}")
    print("     Contraseña configurada: pruebas123")
    print("\nYa puedes ejecutar 'python scripts/test_crypto.py' sin errores.")

if __name__ == "__main__":
    generate_self_signed_cert()

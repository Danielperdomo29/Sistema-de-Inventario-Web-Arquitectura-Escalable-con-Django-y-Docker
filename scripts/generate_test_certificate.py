#!/usr/bin/env python
"""
Script para generar certificados autofirmados PKCS#12 (.p12) para desarrollo.

IMPORTANTE: Este certificado es SOLO para pruebas locales.
Para producción, debe usar el certificado oficial emitido por la DIAN.

Uso:
    python scripts/generate_test_certificate.py

El certificado se guardará en: media/fiscal/certs/test_certificate.p12
Contraseña por defecto: "test_password_123"
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    PrivateFormat,
    pkcs12
)


def generate_self_signed_certificate(
    common_name: str = "Test DIAN Certificate",
    organization: str = "Test Organization",
    country: str = "CO",
    validity_days: int = 365,
    key_size: int = 2048,
    password: str = "test_password_123"
) -> tuple:
    """
    Genera un certificado autofirmado PKCS#12 para pruebas.
    
    Args:
        common_name: Nombre común del certificado
        organization: Nombre de la organización
        country: Código de país (CO para Colombia)
        validity_days: Días de validez del certificado
        key_size: Tamaño de la clave RSA (2048 o 4096)
        password: Contraseña para proteger el archivo .p12
        
    Returns:
        Tuple (private_key, certificate, p12_data)
    """
    print("🔐 Generando certificado autofirmado para desarrollo...")
    print(f"   Organización: {organization}")
    print(f"   Common Name: {common_name}")
    print(f"   Validez: {validity_days} días")
    print(f"   Tamaño Clave: {key_size} bits")
    
    # 1. Generar par de claves RSA
    print("\n⚙️  Generando par de claves RSA...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    
    # 2. Crear sujeto del certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bogota"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Bogota"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # 3. Generar certificado X.509
    print("📜 Generando certificado X.509...")
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=True,  # Non-repudiation
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )
    
    # 4. Crear archivo PKCS#12
    print("📦 Empaquetando en formato PKCS#12 (.p12)...")
    p12_data = pkcs12.serialize_key_and_certificates(
        name=b"Test DIAN Certificate",
        key=private_key,
        cert=certificate,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(password.encode('utf-8'))
    )
    
    return private_key, certificate, p12_data


def save_certificate(p12_data: bytes, output_path: Path, password: str):
    """
    Guarda el certificado en disco.
    
    Args:
        p12_data: Datos del certificado PKCS#12
        output_path: Ruta donde guardar el archivo
        password: Contraseña del certificado
    """
    # Crear directorio si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo
    with open(output_path, 'wb') as f:
        f.write(p12_data)
    
    print(f"\n✅ Certificado generado exitosamente:")
    print(f"   📁 Ubicación: {output_path}")
    print(f"   🔑 Contraseña: {password}")
    print(f"   📏 Tamaño: {len(p12_data)} bytes")
    
    # Instrucciones de uso
    print("\n📋 Instrucciones de uso:")
    print("   1. En el admin de Django, ve a 'Configuraciones Fiscales'")
    print("   2. Sube el archivo .p12 en el campo 'Certificado Archivo'")
    print(f"   3. Ingresa la contraseña: {password}")
    print("   4. Selecciona 'Habilitación (Pruebas)' como ambiente")
    print("\n⚠️  IMPORTANTE:")
    print("   - Este certificado es SOLO para desarrollo local")
    print("   - NO usar en producción")
    print("   - Para producción, usar certificado oficial de la DIAN")


def main():
    """Función principal del script."""
    print("=" * 70)
    print("  Generador de Certificados de Prueba para Facturación Electrónica")
    print("=" * 70)
    
    # Determinar la ruta base del proyecto
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Configurar rutas
    media_dir = project_root / "media" / "fiscal" / "certs"
    output_file = media_dir / "test_certificate.p12"
    
    # Parámetros del certificado
    cert_config = {
        'common_name': 'Test DIAN Development Certificate',
        'organization': 'Sistema Inventario - Desarrollo',
        'country': 'CO',
        'validity_days': 365,
        'key_size': 2048,
        'password': 'test_password_123'
    }
    
    try:
        # Generar certificado
        private_key, certificate, p12_data = generate_self_signed_certificate(**cert_config)
        
        # Guardar en disco
        save_certificate(p12_data, output_file, cert_config['password'])
        
        # Información adicional del certificado
        print("\n📊 Información del certificado:")
        print(f"   Serial Number: {certificate.serial_number}")
        print(f"   Válido desde: {certificate.not_valid_before}")
        print(f"   Válido hasta: {certificate.not_valid_after}")
        print(f"   Subject: {certificate.subject.rfc4514_string()}")
        
        print("\n" + "=" * 70)
        print("✨ ¡Proceso completado exitosamente!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error al generar certificado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

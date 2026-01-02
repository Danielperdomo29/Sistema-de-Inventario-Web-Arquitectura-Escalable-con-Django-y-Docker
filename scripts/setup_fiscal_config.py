#!/usr/bin/env python
"""
Script to create initial FiscalConfig and RangoNumeracion for local development.
This is required for the invoice generation to work.
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from app.fiscal.models import FiscalConfig, RangoNumeracion

def create_fiscal_config():
    """Create a test fiscal configuration for local development."""
    
    # Check if already exists
    if FiscalConfig.objects.filter(is_active=True).exists():
        config = FiscalConfig.objects.filter(is_active=True).first()
        print(f"✓ FiscalConfig already exists: ID={config.id}")
        return config
    
    print("Creating FiscalConfig for local development...")
    
    # Create config - using minimal required fields
    # Check what fields exist
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE fiscal_config")
        columns = [row[0] for row in cursor.fetchall()]
    
    print(f"  Available columns: {columns}")
    
    # Build config data based on available columns
    config_data = {
        'is_active': True,
        'ambiente': 2,  # 2 = Pruebas
    }
    
    # Add optional fields if they exist
    if 'nit_emisor' in columns:
        config_data['nit_emisor'] = '900123456'
    if 'razon_social' in columns:
        config_data['razon_social'] = 'Empresa de Prueba S.A.S.'
    if 'nombre_comercial' in columns:
        config_data['nombre_comercial'] = 'Empresa Prueba'
    if 'direccion' in columns:
        config_data['direccion'] = 'Calle 100 #10-10'
    if 'ciudad' in columns:
        config_data['ciudad'] = 'Bogotá'
    if 'departamento' in columns:
        config_data['departamento'] = 'Cundinamarca'
    if 'pais_codigo' in columns:
        config_data['pais_codigo'] = 'CO'
    if 'telefono' in columns:
        config_data['telefono'] = '3001234567'
    if 'email' in columns:
        config_data['email'] = 'facturacion@empresa.test'
    if 'regimen' in columns:
        config_data['regimen'] = 'SIMPLE'
    if 'tipo_persona' in columns:
        config_data['tipo_persona'] = 'JURIDICA'
    if 'tipo_contribuyente' in columns:
        config_data['tipo_contribuyente'] = 'RESPONSABLE_IVA'
    
    config = FiscalConfig.objects.create(**config_data)
    print(f"✓ FiscalConfig created: ID={config.id}")
    
    return config


def create_rango_numeracion(fiscal_config):
    """Create a test numbering range for local development."""
    
    # Check if already exists
    if RangoNumeracion.objects.filter(fiscal_config=fiscal_config, is_active=True).exists():
        rango = RangoNumeracion.objects.filter(fiscal_config=fiscal_config, is_active=True).first()
        print(f"✓ RangoNumeracion already exists: ID={rango.id}, prefix={rango.prefijo}")
        return rango
    
    print("Creating RangoNumeracion for local development...")
    
    # Check what fields exist
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE fiscal_rango_numeracion")
        columns = [row[0] for row in cursor.fetchall()]
    
    print(f"  Available columns: {columns}")
    
    # Build rango data based on available columns
    rango_data = {
        'fiscal_config': fiscal_config,
        'prefijo': 'SETP',
        'numero_inicio': 1,
        'numero_fin': 99999999,
        'numero_actual': 1,
        'is_active': True,
    }
    
    # Add optional fields if they exist
    if 'resolucion_numero' in columns:
        rango_data['resolucion_numero'] = '18764000001234'
    if 'resolucion_fecha' in columns:
        rango_data['resolucion_fecha'] = date.today() - timedelta(days=30)
    if 'fecha_inicio' in columns:
        rango_data['fecha_inicio'] = date.today()
    if 'fecha_fin' in columns:
        rango_data['fecha_fin'] = date.today() + timedelta(days=365)
    if 'clave_tecnica' in columns:
        # Generate a test technical key (64 chars hex)
        rango_data['clave_tecnica'] = 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c684a4c33b1f4e4f9a4b5c6d7'
    
    rango = RangoNumeracion.objects.create(**rango_data)
    print(f"✓ RangoNumeracion created: ID={rango.id}, prefix={rango.prefijo}")
    
    return rango


def main():
    print("=" * 60)
    print("Setting up Fiscal Configuration for Local Development")
    print("=" * 60)
    print()
    
    try:
        # Create FiscalConfig
        config = create_fiscal_config()
        
        # Create RangoNumeracion
        rango = create_rango_numeracion(config)
        
        print()
        print("=" * 60)
        print("✅ Fiscal configuration setup complete!")
        print()
        print("Summary:")
        print(f"  FiscalConfig ID: {config.id}")
        print(f"  RangoNumeracion ID: {rango.id}")
        print(f"  Prefix: {rango.prefijo}")
        print(f"  Range: {rango.numero_inicio} - {rango.numero_fin}")
        print(f"  Current: {rango.numero_actual}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

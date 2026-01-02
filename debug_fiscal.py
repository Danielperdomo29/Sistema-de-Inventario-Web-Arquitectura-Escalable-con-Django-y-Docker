import os
import django
import sys

# Setup Django environment
sys.path.append('c:\\dev\\Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.fiscal.models import FiscalConfig
from datetime import date

def fix_fiscal_config():
    config = FiscalConfig.objects.first()
    if not config:
        print("No active configuration found. Creating one...")
        config = FiscalConfig.objects.create(
            propietario="Perdomo Industries S.A.S",
            nit_emisor="900123456",
            dv_emisor="1",
            telefono_emisor="3001234567",
            correo_emisor="facturacion@perdomo.com",
            direccion_emisor="Calle 123 # 45-67",
            ciudad_emisor="Bogotá",
            departamento_emisor="Cundinamarca",
            pais_emisor="CO",
            razon_social="Perdomo Industries S.A.S",
            numero_resolucion="18760000001",
            fecha_resolucion=date(2024, 1, 1),
            fecha_fin_resolucion=date(2026, 1, 1),
            prefijo="SETP",
            rango_desde=99000000,
            rango_hasta=99500000,
            clave_tecnica="fc8eac422eba16e22ffd8c6f94b3f40a6e38162c",
            ambiente=2 # Pruebas
        )
    else:
        print(f"Found config: {config.numero_resolucion}")
        if not config.fecha_resolucion:
            print("Fixing missing resolution date...")
            config.fecha_resolucion = date(2024, 1, 1)
            config.save()
            print("Fixed fecha_resolucion")
        
    print(f"Current Fecha Resolución: {config.fecha_resolucion}")

if __name__ == "__main__":
    fix_fiscal_config()

import os
import sys
import django
from django.utils import timezone

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_system.settings")
django.setup()

from app.fiscal.models.fiscal_config import FiscalConfig

def fix_fecha_resolucion():
    print("Iniciando corrección de fecha_resolucion...")
    configs = FiscalConfig.objects.filter(fecha_resolucion__isnull=True)
    count = configs.count()
    
    if count == 0:
        print("No se encontraron configuraciones con fecha_resolucion nula.")
        return

    print(f"Encontradas {count} configuraciones con fecha nula. Actualizando...")
    
    # Establecer fecha de hoy como default
    today = timezone.now().date()
    updated = configs.update(fecha_resolucion=today)
    
    print(f"Se actualizaron {updated} registros con fecha: {today}")

if __name__ == "__main__":
    fix_fecha_resolucion()

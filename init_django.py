"""
Script de inicialización para configurar PyMySQL correctamente.
Resuelve problemas de compatibilidad con Django.
"""
import sys
import os

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configurar PyMySQL ANTES de importar Django
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    pymysql.version_info = (1, 4, 6, 'final', 0)
    print("✓ PyMySQL configurado correctamente")
except ImportError as e:
    print(f"✗ Error importando PyMySQL: {e}")
    print("  Ejecuta: pip install pymysql")
    sys.exit(1)

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Variables de entorno cargadas")
except ImportError:
    print("✗ python-dotenv no instalado")
    print("  Ejecuta: pip install python-dotenv")
    sys.exit(1)

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Verificar que Django esté instalado
try:
    import django
    print(f"✓ Django {django.get_version()} detectado")
except ImportError:
    print("✗ Django no instalado")
    print("  Ejecuta: pip install Django")
    sys.exit(1)

# Setup Django
try:
    django.setup()
    print("✓ Django inicializado correctamente")
except Exception as e:
    print(f"✗ Error inicializando Django: {e}")
    sys.exit(1)

# Verificar conexión a base de datos
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Conexión a base de datos exitosa")
except Exception as e:
    print(f"✗ Error conectando a base de datos: {e}")
    print("  Verifica tu configuración en .env")
    sys.exit(1)

# Verificar modelo de usuario
try:
    from app.models.user_account import UserAccount
    print(f"✓ Modelo UserAccount cargado correctamente")
    print(f"  Tabla DB: {UserAccount._meta.db_table}")
    print(f"  Campos: {len(UserAccount._meta.get_fields())} campos")
except Exception as e:
    print(f"✗ Error cargando modelo UserAccount: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("SISTEMA LISTO PARA CREAR MIGRACIONES")
print("="*60)
print("\nEjecuta:")
print("  python manage.py makemigrations app")
print("  python manage.py migrate")

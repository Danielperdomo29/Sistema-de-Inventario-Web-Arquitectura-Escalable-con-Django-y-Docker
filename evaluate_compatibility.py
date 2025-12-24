"""
Script de evaluación de compatibilidad para migración a django-allauth
Verifica el estado actual del sistema antes de realizar cambios
"""
import subprocess
import sys
import os

def run_command(command, shell=True):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def check_current_system():
    """Verifica el estado actual del sistema"""
    print("=" * 80)
    print("EVALUACIÓN DE COMPATIBILIDAD - SISTEMA DE INVENTARIO")
    print("=" * 80)
    print()
    
    checks = [
        ("1. Django Version", "python -c \"import django; print(f'Django {django.__version__}')\""),
        ("2. Python Version", "python --version"),
        ("3. Current Database", "python -c \"from config.settings import DATABASES; print(DATABASES['default']['ENGINE'])\""),
        ("4. User Model", "python -c \"from config.settings import AUTH_USER_MODEL; print(f'User Model: {AUTH_USER_MODEL}')\""),
        ("5. Installed Apps", "python -c \"from config.settings import INSTALLED_APPS; print('\\n'.join(INSTALLED_APPS))\""),
    ]
    
    for check_name, command in checks:
        print(f"\n{check_name}:")
        print("-" * 80)
        result = run_command(command)
        print(result[:500] if result else "No output")
    
    # Verificar archivos críticos
    print("\n\n6. Archivos Críticos:")
    print("-" * 80)
    critical_files = [
        "config/settings.py",
        "app/models/user_account.py",
        "app/controllers/auth_controller.py",
        "requirements.txt",
        ".docker/docker-compose.yml",
    ]
    
    for file_path in critical_files:
        full_path = os.path.join(os.getcwd(), file_path)
        exists = "✓ Existe" if os.path.exists(full_path) else "✗ No existe"
        print(f"  {exists}: {file_path}")
    
    # Verificar modelos de usuario
    print("\n\n7. Análisis del Modelo de Usuario:")
    print("-" * 80)
    try:
        from app.models.user_account import UserAccount
        print(f"  Modelo actual: UserAccount")
        print(f"  Tabla DB: {UserAccount._meta.db_table}")
        print(f"  Campos:")
        for field in UserAccount._meta.get_fields():
            print(f"    - {field.name} ({field.__class__.__name__})")
    except Exception as e:
        print(f"  Error al importar modelo: {e}")
    
    # Verificar controladores de autenticación
    print("\n\n8. Controladores de Autenticación:")
    print("-" * 80)
    auth_files = [
        "app/controllers/auth_controller.py",
        "app/views/auth_view.py",
    ]
    for file_path in auth_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            print(f"  ✓ {file_path}")
            # Contar líneas
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"    Líneas: {lines}")
        else:
            print(f"  ✗ {file_path} no existe")
    
    # Verificar dependencias actuales
    print("\n\n9. Dependencias Actuales:")
    print("-" * 80)
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            print(f.read())
    
    # Verificar Docker
    print("\n\n10. Estado de Docker:")
    print("-" * 80)
    docker_status = run_command("docker --version")
    print(f"  Docker: {docker_status.strip()}")
    
    docker_compose_status = run_command("docker-compose --version")
    print(f"  Docker Compose: {docker_compose_status.strip()}")
    
    # Recomendaciones
    print("\n\n" + "=" * 80)
    print("RECOMENDACIONES PARA MIGRACIÓN")
    print("=" * 80)
    print("""
1. ✓ Crear backup de la base de datos antes de migrar
2. ✓ Implementar feature flags para activar/desactivar nuevas funcionalidades
3. ✓ Crear estructura de settings modular sin modificar el actual
4. ✓ Extender UserAccount existente en lugar de reemplazarlo
5. ✓ Mantener URLs actuales y agregar nuevas en paralelo
6. ✓ Implementar migración incremental de usuarios
7. ✓ Configurar rollback automático en caso de errores

PRÓXIMOS PASOS:
- Fase 1: División de Settings (sin afectar el actual)
- Fase 2: Extensión del modelo de usuario (sin eliminar campos)
- Fase 3: Integración de allauth en paralelo
- Fase 4: Migración gradual de usuarios
    """)
    
    print("\n" + "=" * 80)
    print("EVALUACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    check_current_system()

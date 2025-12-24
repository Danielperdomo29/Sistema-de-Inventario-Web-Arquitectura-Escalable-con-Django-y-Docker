"""
Script de pruebas manuales para verificar ambos sistemas de autenticación.
Ejecutar: python scripts/test_parallel_auth.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models.user_account import UserAccount
from allauth.account.models import EmailAddress
from django.contrib.auth import authenticate


def print_header(text):
    """Imprime un header formateado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_legacy_system():
    """Prueba el sistema antiguo"""
    print_header("TEST 1: Sistema Antiguo (/login/)")
    
    # Buscar usuario legacy
    legacy_users = UserAccount.objects.filter(use_allauth=False)
    
    if not legacy_users.exists():
        print("⚠️  No hay usuarios del sistema antiguo")
        print("   Creando usuario de prueba...")
        
        user = UserAccount.objects.create_user(
            username='legacy_test',
            email='legacy@ejemplo.com',
            password='LegacyPassword123!',
            rol_id=2,
            use_allauth=False
        )
        print(f"✓ Usuario creado: {user.username}")
    else:
        user = legacy_users.first()
        print(f"✓ Usuario encontrado: {user.username}")
    
    # Verificar autenticación
    auth_user = authenticate(username=user.username, password='LegacyPassword123!')
    if auth_user:
        print(f"✓ Autenticación exitosa")
        print(f"  - Username: {auth_user.username}")
        print(f"  - Email: {auth_user.email}")
        print(f"  - Rol ID: {auth_user.rol_id}")
        print(f"  - Use Allauth: {auth_user.use_allauth}")
    else:
        print("✗ Autenticación falló")
    
    return user


def test_allauth_system():
    """Prueba el sistema allauth"""
    print_header("TEST 2: Sistema Allauth (/accounts/login/)")
    
    # Buscar usuario allauth
    allauth_users = UserAccount.objects.filter(use_allauth=True)
    
    if not allauth_users.exists():
        print("⚠️  No hay usuarios de allauth")
        print("   Creando usuario de prueba...")
        
        user = UserAccount.objects.create_user(
            username='allauth_test',
            email='allauth@ejemplo.com',
            password='AllauthPassword123!',
            rol_id=2,
            use_allauth=True,
            email_verified=True
        )
        
        # Crear EmailAddress
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True
        )
        print(f"✓ Usuario creado: {user.username}")
    else:
        user = allauth_users.first()
        print(f"✓ Usuario encontrado: {user.username}")
    
    # Verificar EmailAddress
    email_address = EmailAddress.objects.filter(user=user).first()
    if email_address:
        print(f"✓ EmailAddress encontrado")
        print(f"  - Email: {email_address.email}")
        print(f"  - Verificado: {email_address.verified}")
        print(f"  - Primario: {email_address.primary}")
    else:
        print("✗ EmailAddress no encontrado")
    
    return user


def test_permissions():
    """Prueba permisos de usuarios"""
    print_header("TEST 3: Permisos y Acceso")
    
    users = UserAccount.objects.all()[:5]
    
    print(f"\nVerificando {users.count()} usuarios:")
    print(f"{'Username':<20} {'Email':<25} {'Rol':<5} {'Allauth':<8} {'Verified'}")
    print("-" * 70)
    
    for user in users:
        email_verified = '✓' if user.email_verified else '✗'
        use_allauth = '✓' if user.use_allauth else '✗'
        
        print(f"{user.username:<20} {user.email:<25} {user.rol_id:<5} {use_allauth:<8} {email_verified}")


def test_migration_status():
    """Verifica estado de migración"""
    print_header("TEST 4: Estado de Migración")
    
    total_users = UserAccount.objects.count()
    allauth_users = UserAccount.objects.filter(use_allauth=True).count()
    legacy_users = UserAccount.objects.filter(use_allauth=False).count()
    
    print(f"\nEstadísticas:")
    print(f"  Total usuarios: {total_users}")
    print(f"  Usuarios allauth: {allauth_users} ({allauth_users/total_users*100:.1f}%)")
    print(f"  Usuarios legacy: {legacy_users} ({legacy_users/total_users*100:.1f}%)")
    
    # Usuarios sin EmailAddress
    users_without_email = UserAccount.objects.filter(
        use_allauth=True
    ).exclude(
        id__in=EmailAddress.objects.values_list('user_id', flat=True)
    ).count()
    
    if users_without_email > 0:
        print(f"\n⚠️  {users_without_email} usuarios allauth sin EmailAddress")
        print("   Ejecutar: python manage.py migrate_users_to_allauth --auto-verify")
    else:
        print(f"\n✓ Todos los usuarios allauth tienen EmailAddress")


def test_urls():
    """Muestra URLs disponibles"""
    print_header("TEST 5: URLs Disponibles")
    
    print("\nSistema Antiguo:")
    print("  - Login:    http://localhost:8000/login/")
    print("  - Register: http://localhost:8000/register/")
    print("  - Logout:   http://localhost:8000/logout/")
    
    print("\nSistema Allauth:")
    print("  - Login:    http://localhost:8000/accounts/login/")
    print("  - Signup:   http://localhost:8000/accounts/signup/")
    print("  - Logout:   http://localhost:8000/accounts/logout/")
    print("  - Password Reset: http://localhost:8000/accounts/password/reset/")
    
    print("\nDashboard:")
    print("  - Home:       http://localhost:8000/")
    print("  - Productos:  http://localhost:8000/productos/")
    print("  - Categorías: http://localhost:8000/categorias/")


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "🧪 PRUEBAS DE AUTENTICACIÓN PARALELA".center(70))
    
    try:
        test_legacy_system()
        test_allauth_system()
        test_permissions()
        test_migration_status()
        test_urls()
        
        print_header("✅ PRUEBAS COMPLETADAS")
        print("\nPróximos pasos:")
        print("1. Probar login en navegador con ambos sistemas")
        print("2. Verificar acceso al dashboard")
        print("3. Migrar usuarios restantes si es necesario")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

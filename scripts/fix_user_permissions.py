"""
Script de diagnóstico para verificar y reparar usuarios.
Ejecutar: python scripts/fix_user_permissions.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models.user_account import UserAccount


def fix_user_permissions():
    """Repara permisos de usuarios"""
    print("=" * 70)
    print("REPARACIÓN DE PERMISOS DE USUARIOS")
    print("=" * 70)
    print()
    
    users = UserAccount.objects.all()
    fixed = 0
    
    print(f"Verificando {users.count()} usuarios...\n")
    
    for user in users:
        needs_fix = False
        changes = []
        
        # Verificar rol_id
        if user.rol_id is None:
            user.rol_id = 2  # Usuario por defecto
            needs_fix = True
            changes.append("rol_id=2")
        
        # Verificar use_allauth
        if not hasattr(user, 'use_allauth'):
            user.use_allauth = False
            needs_fix = True
            changes.append("use_allauth=False")
        
        if needs_fix:
            user.save()
            fixed += 1
            print(f"✓ Reparado: {user.username} ({', '.join(changes)})")
        else:
            print(f"○ OK: {user.username}")
    
    print()
    print("=" * 70)
    if fixed > 0:
        print(f"✅ {fixed} usuarios reparados")
    else:
        print("✅ Todos los usuarios están correctos")
    print("=" * 70)
    print()
    
    # Mostrar resumen
    print("Resumen de usuarios:")
    print(f"{'Username':<20} {'Email':<30} {'Rol':<5} {'Allauth'}")
    print("-" * 70)
    
    for user in UserAccount.objects.all()[:10]:
        allauth_mark = '✓' if user.use_allauth else '✗'
        print(f"{user.username:<20} {user.email:<30} {user.rol_id:<5} {allauth_mark}")


if __name__ == '__main__':
    try:
        fix_user_permissions()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

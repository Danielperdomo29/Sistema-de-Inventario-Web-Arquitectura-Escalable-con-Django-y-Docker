import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from app.models import UserAccount


def fix_admin():
    admin = UserAccount.objects.filter(username="admin").first()
    if admin:
        admin.rol_id = 1
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print(f"Updated {admin.username}: Rol={admin.rol_id}, Active={admin.is_active}")
    else:
        print("Admin user not found")


if __name__ == "__main__":
    fix_admin()

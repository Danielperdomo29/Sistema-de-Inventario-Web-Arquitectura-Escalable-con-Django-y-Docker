"""
Comando para migrar usuarios existentes a allauth.
Uso: python manage.py migrate_users_to_allauth [--auto-verify]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from allauth.account.models import EmailAddress

from app.models.user_account import UserAccount


class Command(BaseCommand):
    help = "Migra usuarios existentes a allauth"

    def add_arguments(self, parser):
        parser.add_argument(
            "--auto-verify",
            action="store_true",
            help="Marcar emails como verificados automáticamente",
        )
        parser.add_argument("--user-id", type=int, help="ID de usuario específico a migrar")

    def handle(self, *args, **options):
        auto_verify = options["auto_verify"]
        user_id = options.get("user_id")

        # Filtrar usuarios
        if user_id:
            users = UserAccount.objects.filter(id=user_id)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"Usuario con ID {user_id} no encontrado"))
                return
        else:
            users = UserAccount.objects.filter(use_allauth=False)

        if not users.exists():
            self.stdout.write(self.style.WARNING("No hay usuarios para migrar"))
            return

        self.stdout.write(f"\nMigrando {users.count()} usuario(s)...\n")

        migrated = 0
        errors = 0

        for user in users:
            try:
                # Verificar que el usuario tenga email
                if not user.email:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Usuario {user.username} no tiene email, omitiendo")
                    )
                    continue

                # Crear EmailAddress si no existe
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={
                        "primary": True,
                        "verified": auto_verify or user.email_verified,
                    },
                )

                if not created and not email_address.verified and auto_verify:
                    # Actualizar verificación si se solicitó auto-verify
                    email_address.verified = True
                    email_address.save()

                # Marcar usuario como migrado
                user.use_allauth = True
                if auto_verify and not user.email_verified:
                    user.email_verified = True
                    user.email_verified_at = timezone.now()

                # Asegurar que tiene rol
                if user.rol_id is None:
                    user.rol_id = 2  # Usuario por defecto

                user.save()

                migrated += 1
                status = "✓" if email_address.verified else "○"
                self.stdout.write(f"{status} Migrado: {user.email} (ID: {user.id})")

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"✗ Error migrando {user.email}: {str(e)}"))

        # Resumen
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✅ {migrated} usuarios migrados exitosamente"))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"❌ {errors} errores durante la migración"))
        self.stdout.write("=" * 60 + "\n")

        # Instrucciones
        if migrated > 0:
            self.stdout.write("\nPróximos pasos:")
            self.stdout.write("1. Los usuarios migrados ahora pueden usar /accounts/login/")
            self.stdout.write("2. Pueden usar username O email para iniciar sesión")
            if not auto_verify:
                self.stdout.write("3. Usuarios con email no verificado deben verificarlo primero")

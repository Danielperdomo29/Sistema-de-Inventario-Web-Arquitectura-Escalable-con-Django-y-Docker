from django.core.management.base import BaseCommand

from app.models.role import Role
from app.models.ui_config import UIConfig


class Command(BaseCommand):
    help = "Configura los roles iniciales y la UI Premium"

    def handle(self, *args, **options):
        self.stdout.write("Configurando sistema...")

        # 1. Configurar Roles según SOLID
        roles_data = [
            {"id": 1, "nombre": "Administrador", "descripcion": "Control total del sistema"},
            {"id": 2, "nombre": "Colaborador", "descripcion": "Lectura y creación (sin editar/eliminar)"},
            {"id": 3, "nombre": "Cliente", "descripcion": "Acceso a reportes y facturas propias"},
        ]

        for role_info in roles_data:
            role, created = Role.objects.update_or_create(
                id=role_info["id"], defaults={"nombre": role_info["nombre"], "descripcion": role_info["descripcion"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Rol creado: {role.nombre}"))

        # 2. Configurar UI Inicial
        ui, created = UIConfig.objects.get_or_create(
            name="Configuración Pro",
            defaults={
                "is_active": True,
                "primary_color": "#3B82F6",
                "secondary_color": "#1E40AF",
                "welcome_title": "BizFlow Pro",
                "welcome_subtitle": "Gestión Inteligente de Inventarios y Facturación",
                "footer_text": "Sistema Empresarial • HUB de Administración",
                "enable_social_login": True,
            },
        )

        if not ui.is_active:
            ui.is_active = True
            ui.save()

        self.stdout.write(self.style.SUCCESS("UI Configurada exitosamente."))
        self.stdout.write(self.style.NOTICE("Nota: Ahora puedes subir fondos desde el administrador de Django."))

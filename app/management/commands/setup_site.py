"""
Management command para crear/actualizar el Site object automáticamente.
Se ejecuta al levantar el contenedor Docker o durante el deploy.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Crea o actualiza el Site object para django-allauth'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default=None,
            help='Dominio del sitio (ej: example.com)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default=None,
            help='Nombre del sitio'
        )
    
    def handle(self, *args, **options):
        # Obtener configuración desde variables de entorno o argumentos
        domain = options['domain'] or os.getenv('SITE_DOMAIN', 'localhost:8000')
        name = options['name'] or os.getenv('SITE_NAME', 'Sistema de Inventario')
        site_id = getattr(settings, 'SITE_ID', 1)
        
        try:
            # Intentar obtener el site existente
            site = Site.objects.get(id=site_id)
            
            # Actualizar si es necesario
            updated = False
            if site.domain != domain:
                site.domain = domain
                updated = True
            if site.name != name:
                site.name = name
                updated = True
            
            if updated:
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Site actualizado: {site.name} ({site.domain})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Site ya existe: {site.name} ({site.domain})'
                    )
                )
        
        except Site.DoesNotExist:
            # Crear nuevo site
            site = Site.objects.create(
                id=site_id,
                domain=domain,
                name=name
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Site creado: {site.name} ({site.domain})'
                )
            )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Error al crear/actualizar Site: {str(e)}'
                )
            )
            raise

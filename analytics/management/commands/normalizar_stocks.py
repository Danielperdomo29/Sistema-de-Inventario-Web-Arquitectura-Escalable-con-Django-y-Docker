"""
Comando para normalizar stocks negativos

Uso:
    python manage.py normalizar_stocks --dry-run  # Ver sin modificar
    python manage.py normalizar_stocks            # Corregir
"""

from django.core.management.base import BaseCommand
from django.db.models import F

from app.models import Product


class Command(BaseCommand):
    help = 'Normaliza stocks negativos estableciéndolos a 0'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra productos sin modificar'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Obtener productos con stock negativo
        productos_negativos = Product.objects.filter(stock_actual__lt=0)
        count = productos_negativos.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('[OK] No hay productos con stock negativo'))
            return
        
        self.stdout.write(f'\n[!] Encontrados {count} productos con stock negativo:\n')
        
        for p in productos_negativos:
            self.stdout.write(f'  - [{p.codigo}] {p.nombre}: {p.stock_actual} unidades')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY-RUN] No se modificaron productos'
            ))
            self.stdout.write('   Ejecuta sin --dry-run para corregir')
            return
        
        # Corregir stocks negativos
        updated = productos_negativos.update(stock_actual=0)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Corregidos {updated} productos - Stock establecido a 0'
        ))

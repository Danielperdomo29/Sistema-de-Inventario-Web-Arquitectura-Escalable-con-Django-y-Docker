"""
Management command para cargar impuestos básicos colombianos.

Carga IVA y retenciones estándar.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from app.fiscal.models import Impuesto, CuentaContable


class Command(BaseCommand):
    help = 'Carga impuestos básicos colombianos (IVA, Retenciones)'
    
    def handle(self, *args, **options):
        self.stdout.write('Cargando impuestos básicos...')
        
        # Obtener cuentas contables necesarias
        try:
            cuenta_iva = CuentaContable.objects.get(codigo='2408')
            cuenta_retefuente = CuentaContable.objects.get(codigo='2365')
        except CuentaContable.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] Error: Cuentas contables no encontradas. '
                    f'Ejecuta primero: python manage.py load_puc'
                )
            )
            return
        
        # Definir impuestos básicos
        impuestos_data = [
            # IVA
            {
                'codigo': 'IVA19',
                'nombre': 'IVA 19%',
                'tipo': 'IVA',
                'porcentaje': Decimal('19.00'),
                'cuenta_por_pagar': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
                'activo': True,
            },
            {
                'codigo': 'IVA5',
                'nombre': 'IVA 5%',
                'tipo': 'IVA',
                'porcentaje': Decimal('5.00'),
                'cuenta_por_pagar': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
                'activo': True,
            },
            {
                'codigo': 'IVA0',
                'nombre': 'IVA 0% (Excluido)',
                'tipo': 'IVA',
                'porcentaje': Decimal('0.00'),
                'cuenta_por_pagar': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
                'activo': True,
            },
            
            # RETENCIONES
            {
                'codigo': 'RTE25',
                'nombre': 'Retención en la Fuente 2.5%',
                'tipo': 'RETEFUENTE',
                'porcentaje': Decimal('2.5'),
                'base_minima': Decimal('1000000.00'),  # 1 millón COP
                'cuenta_por_pagar': cuenta_retefuente,
                'aplica_compras': True,
                'aplica_ventas': False,
                'activo': True,
            },
            {
                'codigo': 'RTE4',
                'nombre': 'Retención en la Fuente 4%',
                'tipo': 'RETEFUENTE',
                'porcentaje': Decimal('4.00'),
                'base_minima': Decimal('1000000.00'),
                'cuenta_por_pagar': cuenta_retefuente,
                'aplica_compras': True,
                'aplica_ventas': False,
                'activo': True,
            },
            {
                'codigo': 'RTEIVA15',
                'nombre': 'Retención de IVA 15%',
                'tipo': 'RETEIVA',
                'porcentaje': Decimal('15.00'),
                'cuenta_por_pagar': cuenta_retefuente,
                'aplica_compras': True,
                'aplica_ventas': False,
                'activo': True,
            },
        ]
        
        # Crear impuestos
        impuestos_creados = 0
        impuestos_existentes = 0
        
        for impuesto_data in impuestos_data:
            codigo = impuesto_data['codigo']
            
            # Verificar si ya existe
            if Impuesto.objects.filter(codigo=codigo).exists():
                impuestos_existentes += 1
                self.stdout.write(f'  - Ya existe: {codigo} - {impuesto_data["nombre"]}')
                continue
            
            # Crear impuesto
            impuesto = Impuesto.objects.create(**impuesto_data)
            
            impuestos_creados += 1
            self.stdout.write(
                f'  [OK] Creado: {codigo} - {impuesto.nombre} ({impuesto.porcentaje}%)'
            )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'[SUCCESS] Impuestos basicos cargados exitosamente'))
        self.stdout.write(f'  - Impuestos creados: {impuestos_creados}')
        self.stdout.write(f'  - Impuestos existentes: {impuestos_existentes}')
        self.stdout.write(f'  - Total en BD: {Impuesto.objects.count()}')

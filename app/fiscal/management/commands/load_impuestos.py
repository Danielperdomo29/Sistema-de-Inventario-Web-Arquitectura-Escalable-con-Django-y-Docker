"""
Management command para cargar impuestos básicos colombianos.

Carga IVA y retenciones estándar con sus cuentas contables.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from app.fiscal.models import Impuesto, CuentaContable


class Command(BaseCommand):
    help = 'Carga impuestos básicos colombianos (IVA, Retenciones)'
    
    def handle(self, *args, **options):
        self.stdout.write('Cargando impuestos básicos...')
        
        # Verificar que existan las cuentas contables necesarias
        self.stdout.write('Verificando cuentas contables...')
        
        # Crear cuenta IVA por pagar si no existe
        cuenta_iva = self.get_or_create_cuenta_iva()
        cuenta_retefuente = self.get_or_create_cuenta_retefuente()
        cuenta_reteiva = self.get_or_create_cuenta_reteiva()
        
        created_count = 0
        
        # IVA
        impuestos_iva = [
            {
                'codigo': 'IVA19',
                'nombre': 'IVA 19%',
                'tipo': 'IVA',
                'porcentaje': Decimal('19.00'),
                'cuenta': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
            },
            {
                'codigo': 'IVA5',
                'nombre': 'IVA 5%',
                'tipo': 'IVA',
                'porcentaje': Decimal('5.00'),
                'cuenta': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
            },
            {
                'codigo': 'IVA0',
                'nombre': 'IVA 0% (Excluido)',
                'tipo': 'IVA',
                'porcentaje': Decimal('0.00'),
                'cuenta': cuenta_iva,
                'aplica_ventas': True,
                'aplica_compras': True,
            },
        ]
        
        for imp_data in impuestos_iva:
            impuesto, created = Impuesto.objects.get_or_create(
                codigo=imp_data['codigo'],
                defaults={
                    'nombre': imp_data['nombre'],
                    'tipo': imp_data['tipo'],
                    'porcentaje': imp_data['porcentaje'],
                    'cuenta_por_pagar': imp_data['cuenta'],
                    'aplica_ventas': imp_data['aplica_ventas'],
                    'aplica_compras': imp_data['aplica_compras'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creado: {impuesto.codigo} - {impuesto.nombre}')
        
        # Retenciones en la Fuente
        retenciones = [
            {
                'codigo': 'RTE25',
                'nombre': 'Retención 2.5%',
                'tipo': 'RETEFUENTE',
                'porcentaje': Decimal('2.5'),
                'base_minima': Decimal('1000000.00'),
                'cuenta': cuenta_retefuente,
            },
            {
                'codigo': 'RTE4',
                'nombre': 'Retención 4%',
                'tipo': 'RETEFUENTE',
                'porcentaje': Decimal('4.00'),
                'base_minima': Decimal('1000000.00'),
                'cuenta': cuenta_retefuente,
            },
            {
                'codigo': 'RTEIVA15',
                'nombre': 'Retención IVA 15%',
                'tipo': 'RETEIVA',
                'porcentaje': Decimal('15.00'),
                'cuenta': cuenta_reteiva,
                'aplica_compras': True,
            },
        ]
        
        for ret_data in retenciones:
            impuesto, created = Impuesto.objects.get_or_create(
                codigo=ret_data['codigo'],
                defaults={
                    'nombre': ret_data['nombre'],
                    'tipo': ret_data['tipo'],
                    'porcentaje': ret_data['porcentaje'],
                    'base_minima': ret_data.get('base_minima'),
                    'cuenta_por_pagar': ret_data['cuenta'],
                    'aplica_compras': ret_data.get('aplica_compras', False),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creado: {impuesto.codigo} - {impuesto.nombre}')
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Impuestos básicos cargados exitosamente'))
        self.stdout.write(f'  • Impuestos creados: {created_count}')
        self.stdout.write(f'  • Total en sistema: {Impuesto.objects.count()}')
    
    def get_or_create_cuenta_iva(self):
        """Crea jerarquía completa para IVA por pagar"""
        # Clase PASIVO
        clase, _ = CuentaContable.objects.get_or_create(
            codigo='2',
            defaults={'nombre': 'PASIVO', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'PASIVO'}
        )
        
        # Grupo IMPUESTOS POR PAGAR
        grupo, _ = CuentaContable.objects.get_or_create(
            codigo='24',
            defaults={
                'nombre': 'IMPUESTOS POR PAGAR',
                'nivel': 2,
                'padre': clase,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        # Cuenta IVA
        cuenta, _ = CuentaContable.objects.get_or_create(
            codigo='2408',
            defaults={
                'nombre': 'IMPUESTO SOBRE LAS VENTAS POR PAGAR',
                'nivel': 3,
                'padre': grupo,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        # Subcuenta IVA POR PAGAR
        subcuenta, created = CuentaContable.objects.get_or_create(
            codigo='240801',
            defaults={
                'nombre': 'IVA POR PAGAR',
                'nivel': 4,
                'padre': cuenta,
                'naturaleza': 'C',
                'tipo': 'PASIVO',
                'acepta_movimiento': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Creada cuenta: {subcuenta.codigo} - {subcuenta.nombre}')
        
        return subcuenta
    
    def get_or_create_cuenta_retefuente(self):
        """Crea jerarquía para Retención en la Fuente"""
        clase, _ = CuentaContable.objects.get_or_create(
            codigo='2',
            defaults={'nombre': 'PASIVO', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'PASIVO'}
        )
        
        grupo, _ = CuentaContable.objects.get_or_create(
            codigo='23',
            defaults={
                'nombre': 'CUENTAS POR PAGAR',
                'nivel': 2,
                'padre': clase,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        cuenta, _ = CuentaContable.objects.get_or_create(
            codigo='2365',
            defaults={
                'nombre': 'RETENCION EN LA FUENTE',
                'nivel': 3,
                'padre': grupo,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        subcuenta, created = CuentaContable.objects.get_or_create(
            codigo='236505',
            defaults={
                'nombre': 'RETENCION EN LA FUENTE POR PAGAR',
                'nivel': 4,
                'padre': cuenta,
                'naturaleza': 'C',
                'tipo': 'PASIVO',
                'acepta_movimiento': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Creada cuenta: {subcuenta.codigo} - {subcuenta.nombre}')
        
        return subcuenta
    
    def get_or_create_cuenta_reteiva(self):
        """Crea jerarquía para Retención de IVA"""
        clase, _ = CuentaContable.objects.get_or_create(
            codigo='2',
            defaults={'nombre': 'PASIVO', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'PASIVO'}
        )
        
        grupo, _ = CuentaContable.objects.get_or_create(
            codigo='23',
            defaults={
                'nombre': 'CUENTAS POR PAGAR',
                'nivel': 2,
                'padre': clase,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        cuenta, _ = CuentaContable.objects.get_or_create(
            codigo='2367',
            defaults={
                'nombre': 'RETENCION DE IVA',
                'nivel': 3,
                'padre': grupo,
                'naturaleza': 'C',
                'tipo': 'PASIVO'
            }
        )
        
        subcuenta, created = CuentaContable.objects.get_or_create(
            codigo='236705',
            defaults={
                'nombre': 'RETENCION DE IVA POR PAGAR',
                'nivel': 4,
                'padre': cuenta,
                'naturaleza': 'C',
                'tipo': 'PASIVO',
                'acepta_movimiento': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Creada cuenta: {subcuenta.codigo} - {subcuenta.nombre}')
        
        return subcuenta

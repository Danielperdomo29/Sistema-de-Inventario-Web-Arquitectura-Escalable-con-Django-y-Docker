"""
Management command para cargar Plan Único de Cuentas (PUC) básico.

Carga las 20 cuentas principales del PUC colombiano.
"""
from django.core.management.base import BaseCommand
from app.fiscal.models import CuentaContable


class Command(BaseCommand):
    help = 'Carga el Plan Único de Cuentas (PUC) básico colombiano'
    
    def handle(self, *args, **options):
        self.stdout.write('Cargando PUC básico...')
        
        # Definir cuentas principales del PUC colombiano
        cuentas_puc = [
            # CLASE 1: ACTIVO
            {'codigo': '1', 'nombre': 'ACTIVO', 'nivel': 1, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre': None},
            {'codigo': '11', 'nombre': 'DISPONIBLE', 'nivel': 2, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre_codigo': '1'},
            {'codigo': '1105', 'nombre': 'CAJA', 'nivel': 3, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre_codigo': '11'},
            {'codigo': '1110', 'nombre': 'BANCOS', 'nivel': 3, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre_codigo': '11'},
            {'codigo': '13', 'nombre': 'DEUDORES', 'nivel': 2, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre_codigo': '1'},
            {'codigo': '1305', 'nombre': 'CLIENTES', 'nivel': 3, 'naturaleza': 'D', 'tipo': 'ACTIVO', 'padre_codigo': '13'},
            
            # CLASE 2: PASIVO
            {'codigo': '2', 'nombre': 'PASIVO', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre': None},
            {'codigo': '23', 'nombre': 'CUENTAS POR PAGAR', 'nivel': 2, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre_codigo': '2'},
            {'codigo': '2335', 'nombre': 'COSTOS Y GASTOS POR PAGAR', 'nivel': 3, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre_codigo': '23'},
            {'codigo': '2365', 'nombre': 'RETENCION EN LA FUENTE', 'nivel': 3, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre_codigo': '23'},
            {'codigo': '24', 'nombre': 'IMPUESTOS GRAVAMENES Y TASAS', 'nivel': 2, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre_codigo': '2'},
            {'codigo': '2408', 'nombre': 'IMPUESTO SOBRE LAS VENTAS POR PAGAR', 'nivel': 3, 'naturaleza': 'C', 'tipo': 'PASIVO', 'padre_codigo': '24'},
            
            # CLASE 3: PATRIMONIO
            {'codigo': '3', 'nombre': 'PATRIMONIO', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'PATRIMONIO', 'padre': None},
            {'codigo': '31', 'nombre': 'CAPITAL SOCIAL', 'nivel': 2, 'naturaleza': 'C', 'tipo': 'PATRIMONIO', 'padre_codigo': '3'},
            
            # CLASE 4: INGRESOS
            {'codigo': '4', 'nombre': 'INGRESOS', 'nivel': 1, 'naturaleza': 'C', 'tipo': 'INGRESO', 'padre': None},
            {'codigo': '41', 'nombre': 'OPERACIONALES', 'nivel': 2, 'naturaleza': 'C', 'tipo': 'INGRESO', 'padre_codigo': '4'},
            {'codigo': '4135', 'nombre': 'COMERCIO AL POR MAYOR Y AL POR MENOR', 'nivel': 3, 'naturaleza': 'C', 'tipo': 'INGRESO', 'padre_codigo': '41'},
            
            # CLASE 5: GASTOS
            {'codigo': '5', 'nombre': 'GASTOS', 'nivel': 1, 'naturaleza': 'D', 'tipo': 'GASTO', 'padre': None},
            {'codigo': '51', 'nombre': 'OPERACIONALES DE ADMINISTRACION', 'nivel': 2, 'naturaleza': 'D', 'tipo': 'GASTO', 'padre_codigo': '5'},
            
            # CLASE 6: COSTOS
            {'codigo': '6', 'nombre': 'COSTOS DE VENTAS', 'nivel': 1, 'naturaleza': 'D', 'tipo': 'COSTO', 'padre': None},
            {'codigo': '61', 'nombre': 'COSTO DE VENTAS Y DE PRESTACION DE SERVICIOS', 'nivel': 2, 'naturaleza': 'D', 'tipo': 'COSTO', 'padre_codigo': '6'},
        ]
        
        # Crear cuentas
        cuentas_creadas = 0
        cuentas_existentes = 0
        
        for cuenta_data in cuentas_puc:
            codigo = cuenta_data['codigo']
            
            # Verificar si ya existe
            if CuentaContable.objects.filter(codigo=codigo).exists():
                cuentas_existentes += 1
                self.stdout.write(f'  - Ya existe: {codigo} - {cuenta_data["nombre"]}')
                continue
            
            # Obtener padre si existe
            padre = None
            if 'padre_codigo' in cuenta_data:
                try:
                    padre = CuentaContable.objects.get(codigo=cuenta_data['padre_codigo'])
                except CuentaContable.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Padre no encontrado para {codigo}: {cuenta_data["padre_codigo"]}'
                        )
                    )
                    continue
            
            # Crear cuenta
            cuenta = CuentaContable.objects.create(
                codigo=codigo,
                nombre=cuenta_data['nombre'],
                nivel=cuenta_data['nivel'],
                naturaleza=cuenta_data['naturaleza'],
                tipo=cuenta_data['tipo'],
                padre=padre
            )
            
            cuentas_creadas += 1
            self.stdout.write(f'  ✓ Creada: {codigo} - {cuenta.nombre}')
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ PUC básico cargado exitosamente'))
        self.stdout.write(f'  • Cuentas creadas: {cuentas_creadas}')
        self.stdout.write(f'  • Cuentas existentes: {cuentas_existentes}')
        self.stdout.write(f'  • Total en BD: {CuentaContable.objects.count()}')

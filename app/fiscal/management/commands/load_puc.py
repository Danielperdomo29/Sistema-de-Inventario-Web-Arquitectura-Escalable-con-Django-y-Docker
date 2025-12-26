"""
Management command para cargar el Plan Único de Cuentas (PUC) básico.

Carga las 20 cuentas principales del PUC colombiano con su jerarquía.
"""
from django.core.management.base import BaseCommand
from app.fiscal.models import CuentaContable


class Command(BaseCommand):
    help = 'Carga el Plan Único de Cuentas (PUC) básico colombiano'
    
    def handle(self, *args, **options):
        self.stdout.write('Cargando PUC básico...')
        
        # Contador de cuentas creadas
        created_count = 0
        
        # NIVEL 1: CLASES
        clases = [
            {'codigo': '1', 'nombre': 'ACTIVO', 'naturaleza': 'D', 'tipo': 'ACTIVO'},
            {'codigo': '2', 'nombre': 'PASIVO', 'naturaleza': 'C', 'tipo': 'PASIVO'},
            {'codigo': '3', 'nombre': 'PATRIMONIO', 'naturaleza': 'C', 'tipo': 'PATRIMONIO'},
            {'codigo': '4', 'nombre': 'INGRESOS', 'naturaleza': 'C', 'tipo': 'INGRESO'},
            {'codigo': '5', 'nombre': 'GASTOS', 'naturaleza': 'D', 'tipo': 'GASTO'},
            {'codigo': '6', 'nombre': 'COSTOS DE VENTAS', 'naturaleza': 'D', 'tipo': 'COSTO'},
        ]
        
        for clase_data in clases:
            clase, created = CuentaContable.objects.get_or_create(
                codigo=clase_data['codigo'],
                defaults={
                    'nombre': clase_data['nombre'],
                    'nivel': 1,
                    'naturaleza': clase_data['naturaleza'],
                    'tipo': clase_data['tipo'],
                    'acepta_movimiento': False
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creada: {clase.codigo} - {clase.nombre}')
        
        # NIVEL 2: GRUPOS (ejemplos principales)
        grupos = [
            # ACTIVO
            {'codigo': '11', 'nombre': 'DISPONIBLE', 'padre_codigo': '1'},
            {'codigo': '12', 'nombre': 'INVERSIONES', 'padre_codigo': '1'},
            {'codigo': '13', 'nombre': 'DEUDORES', 'padre_codigo': '1'},
            {'codigo': '15', 'nombre': 'PROPIEDADES PLANTA Y EQUIPO', 'padre_codigo': '1'},
            # PASIVO
            {'codigo': '21', 'nombre': 'OBLIGACIONES FINANCIERAS', 'padre_codigo': '2'},
            {'codigo': '23', 'nombre': 'CUENTAS POR PAGAR', 'padre_codigo': '2'},
            {'codigo': '24', 'nombre': 'IMPUESTOS POR PAGAR', 'padre_codigo': '2'},
            # PATRIMONIO
            {'codigo': '31', 'nombre': 'CAPITAL SOCIAL', 'padre_codigo': '3'},
            {'codigo': '36', 'nombre': 'RESULTADOS DEL EJERCICIO', 'padre_codigo': '3'},
            # INGRESOS
            {'codigo': '41', 'nombre': 'OPERACIONALES', 'padre_codigo': '4'},
            {'codigo': '42', 'nombre': 'NO OPERACIONALES', 'padre_codigo': '4'},
            # GASTOS
            {'codigo': '51', 'nombre': 'OPERACIONALES DE ADMINISTRACION', 'padre_codigo': '5'},
            {'codigo': '52', 'nombre': 'OPERACIONALES DE VENTAS', 'padre_codigo': '5'},
            # COSTOS
            {'codigo': '61', 'nombre': 'COSTO DE VENTAS Y PRESTACION DE SERVICIOS', 'padre_codigo': '6'},
        ]
        
        for grupo_data in grupos:
            padre = CuentaContable.objects.get(codigo=grupo_data['padre_codigo'])
            grupo, created = CuentaContable.objects.get_or_create(
                codigo=grupo_data['codigo'],
                defaults={
                    'nombre': grupo_data['nombre'],
                    'nivel': 2,
                    'padre': padre,
                    'naturaleza': padre.naturaleza,
                    'tipo': padre.tipo,
                    'acepta_movimiento': False
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creada: {grupo.codigo} - {grupo.nombre}')
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ PUC básico cargado exitosamente'))
        self.stdout.write(f'  • Cuentas creadas: {created_count}')
        self.stdout.write(f'  • Total en sistema: {CuentaContable.objects.count()}')

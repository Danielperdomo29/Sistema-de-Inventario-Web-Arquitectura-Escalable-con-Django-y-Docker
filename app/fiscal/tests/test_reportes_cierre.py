import pytest
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from app.fiscal.models import CuentaContable, PeriodoContable, AsientoContable, DetalleAsiento
from app.fiscal.core.reporte_fiscal import ReporteFiscalService
from app.fiscal.core.cierre_contable import CierreContableService
from app.fiscal.core.pdf_generator import PDFGenerator
from app.models.user_account import UserAccount

@pytest.fixture
def setup_datos_reportes(db):
    """Crea datos base para pruebas de reportes"""
    # 1. Periodo
    periodo = PeriodoContable.objects.create(
        año=2024,
        mes=1,
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 31),
        estado='ABIERTO'
    )
    
    # helper
    def create_acc(codigo, nombre, naturaleza, tipo, padre=None, acepta=False):
        return CuentaContable.objects.create(
            codigo=codigo, nombre=nombre, naturaleza=naturaleza, 
            tipo=tipo, padre=padre, acepta_movimiento=acepta
        )

    # 2. Cuentas - Jerarquía Completa
    
    # ACTIVO (1)
    act = create_acc('1', 'ACTIVO', 'D', 'ACTIVO', None)
    disp = create_acc('11', 'DISPONIBLE', 'D', 'ACTIVO', act)
    caj = create_acc('1105', 'CAJA', 'D', 'ACTIVO', disp)
    caja = create_acc('110505', 'Caja General', 'D', 'ACTIVO', caj, True)
    
    ban = create_acc('1110', 'BANCOS', 'D', 'ACTIVO', disp)
    bancos = create_acc('111005', 'Bancos', 'D', 'ACTIVO', ban, True)
    
    # INGRESOS (4)
    ing = create_acc('4', 'INGRESOS', 'C', 'INGRESO', None)
    ope = create_acc('41', 'OPERACIONALES', 'C', 'INGRESO', ing)
    com = create_acc('4135', 'COMERCIO', 'C', 'INGRESO', ope)
    ventas = create_acc('413505', 'Ventas', 'C', 'INGRESO', com, True)
    
    # GASTOS (5)
    gas = create_acc('5', 'GASTOS', 'D', 'GASTO', None)
    adm = create_acc('51', 'ADMINISTRACION', 'D', 'GASTO', gas)
    per = create_acc('5105', 'PERSONAL', 'D', 'GASTO', adm)
    gastos_admin = create_acc('510505', 'Gastos Personal', 'D', 'GASTO', per, True)
    
    # PATRIMONIO (3)
    pat = create_acc('3', 'PATRIMONIO', 'C', 'PATRIMONIO', None)
    res = create_acc('36', 'RESULTADOS', 'C', 'PATRIMONIO', pat)
    utilidad = create_acc('3605', 'Utilidad Ejercicio', 'C', 'PATRIMONIO', res, True) # Usamos 3605 directamente como en cierre
    
    # User
    user = UserAccount.objects.create(username='test_fiscal', email='test@example.com')

    # 3. Asiento de Venta (Ingreso)
    asiento_venta = AsientoContable.objects.create(
        fecha_contable=date(2024, 1, 15),
        periodo_contable=periodo,
        descripcion="Venta de mercancia",
        estado='ACTIVO',
        numero_asiento=1,
        usuario_creacion=user
    )
    # Debito a Caja, Credito a Ventas (Ingreso)
    DetalleAsiento.objects.create(asiento=asiento_venta, cuenta_contable=caja, debito=Decimal('1000.00'), credito=0, descripcion_detalle="Cobro venta", orden=1)
    DetalleAsiento.objects.create(asiento=asiento_venta, cuenta_contable=ventas, debito=0, credito=Decimal('1000.00'), descripcion_detalle="Ingreso venta", orden=2)
    
    # 4. Asiento de Gasto
    asiento_gasto = AsientoContable.objects.create(
        fecha_contable=date(2024, 1, 20),
        periodo_contable=periodo,
        descripcion="Pago nomina",
        estado='ACTIVO',
        numero_asiento=2,
        usuario_creacion=user
    )
    # Debito a Gasto, Credito a Bancos
    DetalleAsiento.objects.create(asiento=asiento_gasto, cuenta_contable=gastos_admin, debito=Decimal('400.00'), credito=0, descripcion_detalle="Gasto nomina", orden=1)
    DetalleAsiento.objects.create(asiento=asiento_gasto, cuenta_contable=bancos, debito=0, credito=Decimal('400.00'), descripcion_detalle="Pago banco", orden=2)
    
    return {
        'periodo': periodo,
        'cuentas': {'caja': caja, 'ventas': ventas, 'gastos': gastos_admin, 'utilidad': utilidad},
        'asientos': [asiento_venta, asiento_gasto],
        'user': user
    }

class TestReportesFiscales:
    def test_generar_libro_diario(self, setup_datos_reportes):
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2024, 1, 31)
        
        reporte = ReporteFiscalService.generar_libro_diario(fecha_inicio, fecha_fin)
        
        # Deben haber 2 fechas con asientos
        # Pero ambos asientos son de fechas distintas...
        # 2024-01-15 y 2024-01-20
        assert len(reporte) == 2
        assert '2024-01-15' in reporte
        assert '2024-01-20' in reporte
        
        # Verificar totales del dia 15
        asiento_data = reporte['2024-01-15'][0]
        assert asiento_data['total_debito'] == Decimal('1000.00')
        assert asiento_data['total_credito'] == Decimal('1000.00')

    def test_generar_balance_prueba(self, setup_datos_reportes):
        fecha_corte = date(2024, 1, 31)
        balance = ReporteFiscalService.generar_balance_prueba(fecha_corte)
        
        # Debe estar cuadrado
        assert balance['totales']['diferencia'] == Decimal('0.00')
        assert balance['totales']['total_debito'] == Decimal('1400.00') # 1000 caja + 400 gasto
        assert balance['totales']['total_credito'] == Decimal('1400.00') # 1000 ingreso + 400 banco
        
    def test_generar_estado_resultados(self, setup_datos_reportes):
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2024, 1, 31)
        
        estado = ReporteFiscalService.generar_estado_resultados(fecha_inicio, fecha_fin)
        
        assert estado['ingresos'] == Decimal('1000.00')
        assert estado['gastos'] == Decimal('400.00')
        assert estado['utilidad_neta'] == Decimal('600.00')

class TestPDFGenerator:
    def test_pdf_no_crashea(self, setup_datos_reportes):
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2024, 1, 31)
        
        # Obtener datos
        libro_diario = ReporteFiscalService.generar_libro_diario(fecha_inicio, fecha_fin)
        
        # Generar PDF
        gen = PDFGenerator("Test", "Empresa", "900")
        buffer = gen.generar_libro_diario_pdf(libro_diario, str(fecha_inicio), str(fecha_fin))
        
        # Verificar que generó algo
        content = buffer.getvalue()
        assert len(content) > 0
        assert b"%PDF" in content[:10]

class TestCierreContable:
    def test_validar_cuadre_periodo(self, setup_datos_reportes):
        periodo = setup_datos_reportes['periodo']
        servicio = CierreContableService(periodo.id)
        
        assert servicio.validar_cuadre_periodo() is True
    
    def test_calcular_resultado(self, setup_datos_reportes):
        periodo = setup_datos_reportes['periodo']
        servicio = CierreContableService(periodo.id)
        
        resultado = servicio.calcular_resultado()
        assert resultado['utilidad_neta'] == Decimal('600.00')
        
    def test_generar_asiento_cierre(self, setup_datos_reportes):
        periodo = setup_datos_reportes['periodo']
        user = setup_datos_reportes['user']
        servicio = CierreContableService(periodo.id)
        
        # Ejecutar cierre
        asiento_cierre = servicio.generar_asiento_cierre(user)
        
        assert asiento_cierre.tipo_asiento == 'CIERRE'
        
        # Verificar que se cancelaron las cuentas de resultados
        # Ingreso (4) debe tener un debito para quedar en 0
        detalle_ingreso = asiento_cierre.detalles.filter(cuenta_contable__codigo__startswith='4').first()
        assert detalle_ingreso.debito == Decimal('1000.00')
        
        # Gasto (5) debe tener un credito para quedar en 0
        detalle_gasto = asiento_cierre.detalles.filter(cuenta_contable__codigo__startswith='5').first()
        assert detalle_gasto.credito == Decimal('400.00')
        
        # Utilidad (3) debe acreditarse la ganancia
        detalle_utilidad = asiento_cierre.detalles.filter(cuenta_contable__codigo__startswith='3').first()
        assert detalle_utilidad.credito == Decimal('600.00')
        
    def test_cerrar_periodo(self, setup_datos_reportes):
        periodo = setup_datos_reportes['periodo']
        user = setup_datos_reportes['user']
        servicio = CierreContableService(periodo.id)
        
        res = servicio.cerrar_periodo(user)
        
        periodo.refresh_from_db()
        assert periodo.estado == 'CERRADO'
        assert periodo.fecha_cierre is not None
        assert res['estado'] == 'CERRADO'

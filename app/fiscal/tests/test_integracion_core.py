"""
Tests de Integración Core - Fase 2
Verifica el flujo completo: Venta -> Signal -> Asiento -> Hash/Validación
"""
import pytest
from decimal import Decimal
from django.utils import timezone
# Imports de modelos se harán localmente en las fixtures para evitar problemas de carga

@pytest.mark.django_db
class TestIntegracionCore:
    
    @pytest.fixture
    def setup_data(self):
        # 1. Crear usuario
        from app.models.user_account import UserAccount
        from app.models.client import Client
        from app.fiscal.models import AsientoContable, CuentaContable, DetalleAsiento, LogAuditoriaContable
        
        self.user = UserAccount.objects.create(email='test@example.com', username='testuser', first_name='Test User')
        
        # 2. Crear Cuentas PUC mínimas (Jerarquía completa requerida por validación)
        # Nivel 1
        cta_activo = CuentaContable.objects.create(
            codigo='1', nombre='ACTIVO', nivel=1, naturaleza='D', tipo='ACTIVO', acepta_movimiento=False, activa=True
        )
        cta_ingresos = CuentaContable.objects.create(
            codigo='4', nombre='INGRESOS', nivel=1, naturaleza='C', tipo='INGRESO', acepta_movimiento=False, activa=True
        )
        
        # Nivel 2
        cta_disponible = CuentaContable.objects.create(
            codigo='11', nombre='DISPONIBLE', nivel=2, padre=cta_activo, naturaleza='D', tipo='ACTIVO', acepta_movimiento=False, activa=True
        )
        cta_ventas = CuentaContable.objects.create(
            codigo='41', nombre='OPERACIONALES', nivel=2, padre=cta_ingresos, naturaleza='C', tipo='INGRESO', acepta_movimiento=False, activa=True
        )
        
        # Nivel 3
        cta_caja_grupo = CuentaContable.objects.create(
            codigo='1105', nombre='CAJA', nivel=3, padre=cta_disponible, naturaleza='D', tipo='ACTIVO', acepta_movimiento=False, activa=True
        )
        cta_comercio = CuentaContable.objects.create(
            codigo='4135', nombre='COMERCIO', nivel=3, padre=cta_ventas, naturaleza='C', tipo='INGRESO', acepta_movimiento=False, activa=True
        )
        
        # Nivel 4 (Movimiento)
        self.cta_caja = CuentaContable.objects.create(
            codigo='110505', nombre='Caja General', nivel=4, padre=cta_caja_grupo,
            naturaleza='D', tipo='ACTIVO', acepta_movimiento=True, activa=True
        )
        self.cta_ingreso = CuentaContable.objects.create(
            codigo='413501', nombre='Comercio al por menor', nivel=4, padre=cta_comercio,
            naturaleza='C', tipo='INGRESO', acepta_movimiento=True, activa=True
        )
        
        # 3. Datos de venta simulados
        class VentaMock:
            def __init__(self, id, numero, total, usuario, cliente=None):
                self.id = id
                self.numero = numero
                self.total = total
                self.usuario = usuario
                self.cliente = cliente
                self.estado = 'completada'
                self.fecha = timezone.now()
        
        return VentaMock(1, 'FACT-001', Decimal('1000.00'), self.user)

    def test_flujo_completo_venta_asiento(self, setup_data):
        """Prueba que una venta genera un asiento válido y hash correcto"""
        from app.fiscal.services.contador_automatico import ContadorAutomatico
        from app.fiscal.models import LogAuditoriaContable, AsientoContable
        
        venta = setup_data
        
        # 1. Ejecutar servicio (simulando señal)
        asiento = ContadorAutomatico.contabilizar_venta(venta)
        
        # VERIFICACIONES
        
        # A. Asiento creado
        assert asiento is not None
        assert asiento.documento_origen_numero == str(venta.id)
        assert asiento.total_debito == venta.total
        assert asiento.total_credito == venta.total
        assert asiento.diferencia == 0
        
        # B. Detalles creados
        assert asiento.detalles.count() == 2
        
        # C. Hash Generado
        assert asiento.hash_integridad is not None
        assert len(asiento.hash_integridad) == 64
        
        # D. Integridad verificada
        valido, _, _ = asiento.verificar_integridad()
        assert valido is True
        
        # E. Auditoría registrada
        logs = LogAuditoriaContable.objects.filter(asiento=asiento)
        assert logs.exists()
        assert logs.filter(tipo_evento='CREACION_ASIENTO').exists()
        assert logs.filter(tipo_evento='MODIFICACION_ASIENTO').exists()

    def test_idempotencia_contabilizacion(self, setup_data):
        """Verifica que no se dupliquen asientos por la misma venta"""
        from app.fiscal.services.contador_automatico import ContadorAutomatico
        from app.fiscal.models import AsientoContable
        
        venta = setup_data
        
        asiento1 = ContadorAutomatico.contabilizar_venta(venta)
        asiento2 = ContadorAutomatico.contabilizar_venta(venta)
        
        assert asiento1 is not None
        # asiento2 debe ser None porque ya existe
        assert asiento2 is None 
        assert AsientoContable.objects.count() == 1

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from app.models.sale import Sale
from app.models.client import Client
from app.models.user_account import UserAccount
from app.fiscal.models import FacturaElectronica

@pytest.mark.django_db
class TestFacturacionSignals:
    
    @pytest.fixture
    def setup_data(self):
        """Crear datos base para pruebas"""
        User = get_user_model()
        # Verificar si ya existe para evitar errores en tests paralelos db reuse
        try:
             user_account = User.objects.get(username='testuser')
        except User.DoesNotExist:
             user_account = User.objects.create_user(email='test@example.com', username='testuser', password='password123')
        
        client = Client.objects.create(documento='123456789', nombre='Cliente Test', email='cliente@test.com')
        return {
            'user_account': user_account,
            'client': client
        }

    def test_generacion_automatica_factura(self, setup_data):
        """Validar que se crea FacturaElectronica al completar Venta"""
        client = setup_data['client']
        user = setup_data['user_account']
        
        # 1. Crear Venta
        venta = Sale.objects.create(
            numero_factura='FAC-TEST-001',
            cliente=client,
            usuario=user,
            fecha=datetime.now(timezone.utc),
            total=Decimal('150000.00'),
            estado='completada', # Estado trigger
            tipo_pago='efectivo'
        )
        
        # 2. Verificar existencia de FacturaElectronica
        assert hasattr(venta, 'factura_electronica')
        factura = venta.factura_electronica
        
        # 3. Validar datos generados
        assert factura.estado_dian in ['GENERADO', 'PENDIENTE']
        assert factura.cufe is not None
        assert len(factura.cufe) > 0
        assert factura.xml_firmado.name.startswith('fiscal/xml/firmados/')
        
    def test_no_generar_si_no_completada(self, setup_data):
        """Validar que NO se crea FacturaElectronica si Venta no está completada"""
        client = setup_data['client']
        user = setup_data['user_account']
        
        venta = Sale.objects.create(
            numero_factura='FAC-TEST-002',
            cliente=client,
            usuario=user,
            fecha=datetime.now(timezone.utc),
            total=Decimal('10000.00'),
            estado='pendiente', # Estado NO trigger
            tipo_pago='efectivo'
        )
        
        assert not hasattr(venta, 'factura_electronica')
        
    def test_idempotencia(self, setup_data):
        """Validar que guardar 2 veces no duplica ni falla"""
        client = setup_data['client']
        user = setup_data['user_account']
        
        venta = Sale.objects.create(
            numero_factura='FAC-TEST-003',
            cliente=client,
            usuario=user,
            fecha=datetime.now(timezone.utc),
            total=Decimal('200000.00'),
            estado='completada',
        )
        
        assert FacturaElectronica.objects.filter(venta=venta).count() == 1
        
        # Guardar de nuevo
        venta.save()
        
        assert FacturaElectronica.objects.filter(venta=venta).count() == 1

"""
Tests unitarios para Impuesto model.
Siguiendo TDD: Tests primero, implementación después.

Configuración de impuestos (IVA, Retenciones) con cálculos automáticos.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from app.fiscal.models.impuesto import Impuesto
from app.fiscal.models.cuenta_contable import CuentaContable


pytestmark = pytest.mark.django_db


@pytest.fixture
def cuenta_iva_por_pagar():
    """Fixture: Cuenta contable IVA por pagar con jerarquía completa"""
    # Crear jerarquía completa
    clase = CuentaContable.objects.create(
        codigo='2',
        nombre='PASIVO',
        nivel=1,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    grupo = CuentaContable.objects.create(
        codigo='24',
        nombre='IMPUESTOS POR PAGAR',
        nivel=2,
        padre=clase,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    cuenta = CuentaContable.objects.create(
        codigo='2408',
        nombre='IVA',
        nivel=3,
        padre=grupo,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    subcuenta = CuentaContable.objects.create(
        codigo='240801',
        nombre='IVA POR PAGAR',
        nivel=4,
        padre=cuenta,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    return subcuenta


@pytest.fixture
def cuenta_retefuente():
    """Fixture: Cuenta contable Retención en la Fuente con jerarquía completa"""
    clase = CuentaContable.objects.create(
        codigo='2',
        nombre='PASIVO',
        nivel=1,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    grupo = CuentaContable.objects.create(
        codigo='23',
        nombre='CUENTAS POR PAGAR',
        nivel=2,
        padre=clase,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    cuenta = CuentaContable.objects.create(
        codigo='2365',
        nombre='RETENCIONES',
        nivel=3,
        padre=grupo,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    subcuenta = CuentaContable.objects.create(
        codigo='236505',
        nombre='RETEFUENTE POR PAGAR',
        nivel=4,
        padre=cuenta,
        naturaleza='C',
        tipo='PASIVO'
    )
    
    return subcuenta


class TestImpuestoCalculation:
    """Tests para cálculos de impuestos"""
    
    def test_calcular_impuesto_base_normal(self, cuenta_iva_por_pagar):
        """Test: Calcula impuesto sobre base normal"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='IVA19',
            nombre='IVA 19%',
            tipo='IVA',
            porcentaje=Decimal('19.00'),
            cuenta_por_pagar=cuenta_iva_por_pagar,
            aplica_ventas=True
        )
        
        # When
        valor = impuesto.calcular(Decimal('1000.00'))
        
        # Then
        assert valor == Decimal('190.00')
    
    def test_calcular_impuesto_con_base_minima(self, cuenta_retefuente):
        """Test: No calcula impuesto si base es menor a base mínima"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='RTE25',
            nombre='Retención 2.5%',
            tipo='RETEFUENTE',
            porcentaje=Decimal('2.5'),
            base_minima=Decimal('1000000.00'),
            cuenta_por_pagar=cuenta_retefuente
        )
        
        # When
        valor = impuesto.calcular(Decimal('500000.00'))  # Menor a base mínima
        
        # Then
        assert valor == Decimal('0.00')
    
    def test_calcular_impuesto_base_cero(self, cuenta_iva_por_pagar):
        """Test: Retorna cero si base es cero"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='IVA19',
            nombre='IVA 19%',
            tipo='IVA',
            porcentaje=Decimal('19.00'),
            cuenta_por_pagar=cuenta_iva_por_pagar
        )
        
        # When
        valor = impuesto.calcular(Decimal('0.00'))
        
        # Then
        assert valor == Decimal('0.00')
    
    def test_redondeo_dos_decimales(self, cuenta_iva_por_pagar):
        """Test: Redondea resultado a 2 decimales"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='IVA19',
            nombre='IVA 19%',
            tipo='IVA',
            porcentaje=Decimal('19.00'),
            cuenta_por_pagar=cuenta_iva_por_pagar
        )
        
        # When
        valor = impuesto.calcular(Decimal('1000.33'))
        
        # Then
        assert valor == Decimal('190.06')  # Redondeado a 2 decimales


class TestImpuestoValidation:
    """Tests para validaciones de impuestos"""
    
    def test_porcentaje_valido(self, cuenta_iva_por_pagar):
        """Test: Porcentaje debe estar entre 0 y 100"""
        # When/Then - Porcentaje negativo
        with pytest.raises(ValidationError):
            impuesto = Impuesto(
                codigo='IVA',
                nombre='IVA',
                tipo='IVA',
                porcentaje=Decimal('-5.00'),  # Inválido
                cuenta_por_pagar=cuenta_iva_por_pagar
            )
            impuesto.full_clean()
    
    def test_cuenta_contable_requerida(self):
        """Test: Cuenta por pagar es requerida"""
        # When/Then
        with pytest.raises(ValidationError):
            impuesto = Impuesto(
                codigo='IVA19',
                nombre='IVA 19%',
                tipo='IVA',
                porcentaje=Decimal('19.00')
                # Sin cuenta_por_pagar
            )
            impuesto.full_clean()
    
    def test_tipo_impuesto_valido(self, cuenta_iva_por_pagar):
        """Test: Tipo de impuesto debe ser válido"""
        # Tipos válidos
        tipos_validos = ['IVA', 'RETEFUENTE', 'RETEIVA', 'RETEICA']
        
        for i, tipo in enumerate(tipos_validos):
            impuesto = Impuesto(
                codigo=f'T{i}',  # Código corto
                nombre=f'Test {tipo}',
                tipo=tipo,
                porcentaje=Decimal('10.00'),
                cuenta_por_pagar=cuenta_iva_por_pagar
            )
            impuesto.full_clean()  # No debe fallar


class TestImpuestoMethods:
    """Tests para métodos del modelo Impuesto"""
    
    def test_aplicable_a_venta(self, cuenta_iva_por_pagar):
        """Test: Verifica si impuesto aplica a ventas"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='IVA19',
            nombre='IVA 19%',
            tipo='IVA',
            porcentaje=Decimal('19.00'),
            cuenta_por_pagar=cuenta_iva_por_pagar,
            aplica_ventas=True,
            aplica_compras=False
        )
        
        # When/Then
        assert impuesto.es_aplicable('venta') is True
        assert impuesto.es_aplicable('compra') is False
    
    def test_aplicable_a_compra(self, cuenta_retefuente):
        """Test: Verifica si impuesto aplica a compras"""
        # Given
        impuesto = Impuesto.objects.create(
            codigo='RTE25',
            nombre='Retención 2.5%',
            tipo='RETEFUENTE',
            porcentaje=Decimal('2.5'),
            cuenta_por_pagar=cuenta_retefuente,
            aplica_compras=True,
            aplica_ventas=False
        )
        
        # When/Then
        assert impuesto.es_aplicable('compra') is True
        assert impuesto.es_aplicable('venta') is False
    
    def test_str_representation(self, cuenta_iva_por_pagar):
        """Test: Representación en string"""
        impuesto = Impuesto.objects.create(
            codigo='IVA19',
            nombre='IVA 19%',
            tipo='IVA',
            porcentaje=Decimal('19.00'),
            cuenta_por_pagar=cuenta_iva_por_pagar
        )
        
        assert 'IVA19' in str(impuesto)
        assert 'IVA 19%' in str(impuesto)

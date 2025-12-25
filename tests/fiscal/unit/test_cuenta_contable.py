"""
Tests unitarios para CuentaContable model.
Siguiendo TDD: Tests primero, implementación después.

Plan Único de Cuentas (PUC) colombiano con jerarquía de 5 niveles.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.fiscal.models.cuenta_contable import CuentaContable


pytestmark = pytest.mark.django_db


class TestCuentaContableCreation:
    """Tests para creación de cuentas contables"""
    
    def test_crear_cuenta_clase_nivel_1(self):
        """Test: Crea cuenta clase (nivel 1)"""
        # Given/When
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # Then
        assert cuenta.id is not None
        assert cuenta.nivel == 1
        assert cuenta.padre is None
        assert cuenta.acepta_movimiento is False
    
    def test_crear_cuenta_con_padre(self):
        """Test: Crea cuenta con padre (jerarquía)"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When
        grupo = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # Then
        assert grupo.padre == clase
        assert grupo.nivel == 2
    
    def test_solo_auxiliares_aceptan_movimiento(self):
        """Test: Solo cuentas auxiliares (nivel 5) aceptan movimiento"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        cuenta = CuentaContable.objects.create(
            codigo='1105',
            nombre='CAJA',
            nivel=3,
            padre=grupo,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        subcuenta = CuentaContable.objects.create(
            codigo='110505',
            nombre='CAJA GENERAL',
            nivel=4,
            padre=cuenta,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When
        auxiliar = CuentaContable.objects.create(
            codigo='11050501',
            nombre='Caja Principal',
            nivel=5,
            padre=subcuenta,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True
        )
        
        # Then
        assert clase.acepta_movimiento is False
        assert auxiliar.acepta_movimiento is True


class TestCuentaContableValidation:
    """Tests para validaciones de cuentas contables"""
    
    def test_codigo_unico(self):
        """Test: Código debe ser único"""
        # Given
        CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When/Then
        with pytest.raises(IntegrityError):
            CuentaContable.objects.create(
                codigo='1',  # Duplicado
                nombre='OTRO',
                nivel=1,
                naturaleza='D',
                tipo='ACTIVO'
            )
    
    def test_nivel_coherente_con_codigo(self):
        """Test: Nivel debe ser coherente con longitud del código"""
        # When/Then
        with pytest.raises(ValidationError):
            cuenta = CuentaContable(
                codigo='11',  # 2 dígitos
                nombre='DISPONIBLE',
                nivel=1,  # Incorrecto (debería ser 2)
                naturaleza='D',
                tipo='ACTIVO'
            )
            cuenta.full_clean()
    
    def test_padre_debe_ser_nivel_anterior(self):
        """Test: Padre debe ser del nivel inmediatamente anterior"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When/Then - Intentar crear nivel 3 con padre nivel 1
        with pytest.raises(ValidationError):
            cuenta = CuentaContable(
                codigo='1105',
                nombre='CAJA',
                nivel=3,
                padre=clase,  # Nivel 1 (debería ser nivel 2)
                naturaleza='D',
                tipo='ACTIVO'
            )
            cuenta.full_clean()
    
    def test_naturaleza_heredada_de_padre(self):
        """Test: Naturaleza debe heredarse del padre"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When - Intentar crear con naturaleza diferente
        with pytest.raises(ValidationError):
            grupo = CuentaContable(
                codigo='11',
                nombre='DISPONIBLE',
                nivel=2,
                padre=clase,
                naturaleza='C',  # Diferente al padre (D)
                tipo='ACTIVO'
            )
            grupo.full_clean()


class TestCuentaContableMethods:
    """Tests para métodos del modelo CuentaContable"""
    
    def test_get_nivel_from_codigo(self):
        """Test: Calcula nivel basado en longitud del código"""
        cuenta = CuentaContable(codigo='110505')
        assert cuenta.get_nivel_from_codigo() == 4
        
        cuenta2 = CuentaContable(codigo='1')
        assert cuenta2.get_nivel_from_codigo() == 1
    
    def test_get_ruta_jerarquica(self):
        """Test: Retorna ruta jerárquica completa"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        cuenta = CuentaContable.objects.create(
            codigo='1105',
            nombre='CAJA',
            nivel=3,
            padre=grupo,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When
        ruta = cuenta.get_ruta_jerarquica()
        
        # Then
        assert len(ruta) == 3
        assert ruta[0] == clase
        assert ruta[1] == grupo
        assert ruta[2] == cuenta
    
    def test_get_subcuentas(self):
        """Test: Retorna todas las subcuentas hijas"""
        # Given
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo1 = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo2 = CuentaContable.objects.create(
            codigo='12',
            nombre='INVERSIONES',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        # When
        subcuentas = clase.get_subcuentas()
        
        # Then
        assert subcuentas.count() == 2
        assert grupo1 in subcuentas
        assert grupo2 in subcuentas
    
    def test_puede_tener_movimientos(self):
        """Test: Verifica si la cuenta puede tener movimientos"""
        # Given
        cuenta_clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=cuenta_clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        cuenta = CuentaContable.objects.create(
            codigo='1105',
            nombre='CAJA',
            nivel=3,
            padre=grupo,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        subcuenta = CuentaContable.objects.create(
            codigo='110505',
            nombre='CAJA GENERAL',
            nivel=4,
            padre=cuenta,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        cuenta_auxiliar = CuentaContable.objects.create(
            codigo='11050501',
            nombre='Caja Principal',
            nivel=5,
            padre=subcuenta,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True
        )
        
        # When/Then
        assert cuenta_clase.puede_tener_movimientos() is False
        assert cuenta_auxiliar.puede_tener_movimientos() is True
    
    def test_str_representation(self):
        """Test: Representación en string"""
        clase = CuentaContable.objects.create(
            codigo='1',
            nombre='ACTIVO',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        grupo = CuentaContable.objects.create(
            codigo='11',
            nombre='DISPONIBLE',
            nivel=2,
            padre=clase,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        cuenta = CuentaContable.objects.create(
            codigo='1105',
            nombre='CAJA',
            nivel=3,
            padre=grupo,
            naturaleza='D',
            tipo='ACTIVO'
        )
        
        assert '1105' in str(cuenta)
        assert 'CAJA' in str(cuenta)

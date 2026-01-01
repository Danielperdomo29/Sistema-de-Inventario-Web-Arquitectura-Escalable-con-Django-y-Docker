"""
Tests para Validadores DIAN
Valida reglas de negocio contable según normativa DIAN
"""
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from app.fiscal.validators import (
    ValidadorCuadreContable,
    ValidadorPeriodoAbierto,
    ValidadorCuentasPUC,
    ValidadorMontosPositivos,
    ValidadorSecuenciaNumerica,
    ValidadorLimitesUsuario,
    ValidadorTercerosDIAN,
    CadenaValidacionContable
)
from app.fiscal.models import PeriodoContable, CuentaContable, PerfilFiscal

User = get_user_model()


@pytest.mark.django_db
class TestValidadorCuadreContable:
    """
    Tests del validador MÁS CRÍTICO: Cuadre Contable
    Débitos = Créditos (tolerancia ≤ $0.01)
    """
    
    def test_asiento_cuadrado_valido(self):
        """Asiento perfectamente cuadrado debe pasar"""
        validador = ValidadorCuadreContable()
        
        asiento_data = {
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'detalles': [
                {'debito': Decimal('1000.00'), 'credito': Decimal('0.00')},
                {'debito': Decimal('0.00'), 'credito': Decimal('1000.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
        assert mensaje == ""
    
    def test_descuadre_mayor_tolerancia_invalido(self):
        """Descuadre > $0.01 debe fallar"""
        validador = ValidadorCuadreContable()
        
        asiento_data = {
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('999.98'),  # Diferencia de $0.02
            'detalles': [
                {'debito': Decimal('1000.00'), 'credito': Decimal('0.00')},
                {'debito': Decimal('0.00'), 'credito': Decimal('999.98')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'Descuadre' in mensaje
        assert '0.02' in mensaje
    
    def test_tolerancia_exacta_valido(self):
        """Descuadre de exactamente $0.01 debe pasar"""
        validador = ValidadorCuadreContable()
        
        asiento_data = {
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('999.99'),  # Diferencia de $0.01
            'detalles': [
                {'debito': Decimal('1000.00'), 'credito': Decimal('0.00')},
                {'debito': Decimal('0.00'), 'credito': Decimal('999.99')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
    
    def test_sin_detalles_invalido(self):
        """Asiento sin detalles debe fallar"""
        validador = ValidadorCuadreContable()
        
        asiento_data = {
            'total_debito': Decimal('0.00'),
            'total_credito': Decimal('0.00'),
            'detalles': []
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'al menos un detalle' in mensaje.lower()
    
    def test_totales_no_coinciden_con_detalles(self):
        """Totales del asiento deben coincidir con suma de detalles"""
        validador = ValidadorCuadreContable()
        
        asiento_data = {
            'total_debito': Decimal('1500.00'),  # Incorrecto
            'total_credito': Decimal('1000.00'),
            'detalles': [
                {'debito': Decimal('1000.00'), 'credito': Decimal('0.00')},
                {'debito': Decimal('0.00'), 'credito': Decimal('1000.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'no coincide' in mensaje.lower()


@pytest.mark.django_db
class TestValidadorPeriodoAbierto:
    """
    Tests del validador de período contable abierto
    """
    
    def test_periodo_abierto_valido(self):
        """Período abierto debe permitir crear asientos"""
        # Crear período abierto
        periodo = PeriodoContable.objects.create(
            año=2025,
            mes=1,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 31),
            estado='ABIERTO'
        )
        
        validador = ValidadorPeriodoAbierto()
        
        asiento_data = {
            'fecha_contable': date(2025, 1, 15),
            'periodo_contable': periodo
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
        assert mensaje == ""
    
    def test_periodo_cerrado_invalido(self):
        """Período cerrado debe bloquear creación de asientos"""
        # Crear período cerrado
        periodo = PeriodoContable.objects.create(
            año=2025,
            mes=1,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 31),
            estado='CERRADO'
        )
        
        validador = ValidadorPeriodoAbierto()
        
        asiento_data = {
            'fecha_contable': date(2025, 1, 15),
            'periodo_contable': periodo
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'CERRADO' in mensaje
    
    def test_periodo_bloqueado_invalido(self):
        """Período bloqueado debe rechazar asientos"""
        periodo = PeriodoContable.objects.create(
            año=2025,
            mes=1,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 31),
            estado='BLOQUEADO'
        )
        
        validador = ValidadorPeriodoAbierto()
        
        asiento_data = {
            'fecha_contable': date(2025, 1, 15),
            'periodo_contable': periodo
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'BLOQUEADO' in mensaje
    
    def test_sin_periodo_valido(self):
        """Sin período definido debe permitir (se creará automáticamente)"""
        validador = ValidadorPeriodoAbierto()
        
        asiento_data = {
            'fecha_contable': date(2025, 6, 15),
            'periodo_contable': None
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True


@pytest.mark.django_db
class TestValidadorCuentasPUC:
    """
    Tests del validador de cuentas PUC
    """
    
    def test_cuenta_valida_activa(self):
        """Cuenta válida y activa debe pasar"""
        # Crear cuenta válida
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        validador = ValidadorCuentasPUC()
        
        asiento_data = {
            'detalles': [
                {'cuenta_contable_id': cuenta.id, 'debito': Decimal('1000.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
    
    def test_cuenta_inexistente_invalida(self):
        """Cuenta que no existe debe fallar"""
        validador = ValidadorCuentasPUC()
        
        asiento_data = {
            'detalles': [
                {'cuenta_contable_id': 99999, 'debito': Decimal('1000.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'no existe' in mensaje.lower()
    
    def test_cuenta_no_permite_movimiento_invalida(self):
        """Cuenta agrupadora (no permite movimiento) debe fallar"""
        cuenta = CuentaContable.objects.create(
            codigo='2',
            nombre='Pasivo',
            nivel=1,
            naturaleza='C',
            tipo='PASIVO',
            acepta_movimiento=False,  # Agrupadora
            activa=True
        )
        
        validador = ValidadorCuentasPUC()
        
        asiento_data = {
            'detalles': [
                {'cuenta_contable_id': cuenta.id, 'debito': Decimal('1000.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'no permite movimiento' in mensaje.lower()
    
    def test_cuenta_inactiva_invalida(self):
        """Cuenta inactiva debe fallar"""
        cuenta = CuentaContable.objects.create(
            codigo='3',
            nombre='Patrimonio',
            nivel=1,
            naturaleza='C',
            tipo='PATRIMONIO',
            acepta_movimiento=True,
            activa=False  # Inactiva
        )
        
        validador = ValidadorCuentasPUC()
        
        asiento_data = {
            'detalles': [
                {'cuenta_contable_id': cuenta.id, 'debito': Decimal('1000.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'inactiva' in mensaje.lower()


@pytest.mark.django_db
class TestValidadorMontosPositivos:
    """
    Tests del validador de montos positivos
    """
    
    def test_montos_positivos_validos(self):
        """Montos positivos válidos deben pasar"""
        validador = ValidadorMontosPositivos()
        
        asiento_data = {
            'detalles': [
                {'debito': Decimal('1000.00'), 'credito': Decimal('0.00')},
                {'debito': Decimal('0.00'), 'credito': Decimal('1000.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
    
    def test_monto_negativo_invalido(self):
        """Montos negativos deben fallar"""
        validador = ValidadorMontosPositivos()
        
        asiento_data = {
            'detalles': [
                {'debito': Decimal('-100.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'negativo' in mensaje.lower()
    
    def test_debito_y_credito_simultaneos_invalido(self):
        """Línea con débito Y crédito debe fallar"""
        validador = ValidadorMontosPositivos()
        
        asiento_data = {
            'detalles': [
                {'debito': Decimal('100.00'), 'credito': Decimal('50.00')}  # Ambos
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'simultáneamente' in mensaje.lower()
    
    def test_ambos_cero_invalido(self):
        """Línea con débito y crédito en cero debe fallar"""
        validador = ValidadorMontosPositivos()
        
        asiento_data = {
            'detalles': [
                {'debito': Decimal('0.00'), 'credito': Decimal('0.00')}
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'mayor a cero' in mensaje.lower()
    
    def test_mas_de_dos_decimales_invalido(self):
        """Montos con más de 2 decimales deben fallar"""
        validador = ValidadorMontosPositivos()
        
        asiento_data = {
            'detalles': [
                {'debito': Decimal('100.123'), 'credito': Decimal('0.00')}  # 3 decimales
            ]
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'decimales' in mensaje.lower()


@pytest.mark.django_db
class TestValidadorSecuenciaNumerica:
    """
    Tests del validador de secuencia numérica
    """
    
    def test_primer_asiento_debe_ser_uno(self):
        """Primer asiento del sistema debe ser número 1"""
        from app.fiscal.models import AsientoContable
        
        # Asegurar que no hay asientos
        AsientoContable.objects.all().delete()
        
        validador = ValidadorSecuenciaNumerica()
        
        asiento_data = {
            'numero_asiento': 1,
            'fecha_contable': date(2025, 1, 15)
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is True
    
    def test_primer_asiento_no_uno_invalido(self):
        """Primer asiento con número != 1 debe fallar"""
        from app.fiscal.models import AsientoContable
        
        AsientoContable.objects.all().delete()
        
        validador = ValidadorSecuenciaNumerica()
        
        asiento_data = {
            'numero_asiento': 5,  # No es 1
            'fecha_contable': date(2025, 1, 15)
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'debe ser número 1' in mensaje.lower()


@pytest.mark.django_db
class TestCadenaValidacion:
    """
    Tests de integración de la cadena de validación
    """
    
    def test_cadena_ejecuta_todos_validadores(self):
        """Cadena debe ejecutar todos los validadores"""
        cadena = CadenaValidacionContable()
        
        # Contar validadores
        validadores = cadena.obtener_validadores()
        
        assert len(validadores) == 7, "Debe haber 7 validadores"
    
    def test_asiento_valido_pasa_cadena(self):
        """Asiento completamente válido debe pasar toda la cadena"""
        # Crear datos necesarios
        cuenta1 = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        cuenta2 = CuentaContable.objects.create(
            codigo='4',
            nombre='Ingresos',
            nivel=1,
            naturaleza='C',
            tipo='INGRESO',
            acepta_movimiento=True,
            activa=True
        )
        
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        cadena = CadenaValidacionContable()
        
        asiento_data = {
            'numero_asiento': 1,
            'fecha_contable': date(2025, 1, 15),
            'tipo_asiento': 'VENTA',
            'descripcion': 'Venta de productos',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'usuario': usuario,
            'detalles': [
                {
                    'cuenta_contable_id': cuenta1.id,
                    'debito': Decimal('1000.00'),
                    'credito': Decimal('0.00'),
                    'orden': 1
                },
                {
                    'cuenta_contable_id': cuenta2.id,
                    'debito': Decimal('0.00'),
                    'credito': Decimal('1000.00'),
                    'orden': 2
                }
            ]
        }
        
        es_valido, errores = cadena.validar(asiento_data)
        
        assert es_valido is True
        assert len(errores) == 0
    
    def test_asiento_invalido_recolecta_errores(self):
        """Asiento inválido debe recolectar todos los errores"""
        cadena = CadenaValidacionContable()
        
        asiento_data = {
            'numero_asiento': None,  # Inválido
            'fecha_contable': date(2025, 1, 15),
            'tipo_asiento': 'VENTA',
            'descripcion': 'Test',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('500.00'),  # Descuadrado
            'detalles': []  # Sin detalles
        }
        
        es_valido, errores = cadena.validar(asiento_data)
        
        assert es_valido is False
        assert len(errores) > 0


# Configuración de pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

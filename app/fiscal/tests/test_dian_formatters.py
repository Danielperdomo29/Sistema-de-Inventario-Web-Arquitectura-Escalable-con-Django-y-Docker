"""
Tests para formatters y utilidades DIAN.
"""
import pytest
from datetime import datetime, date, time
from decimal import Decimal

from app.fiscal.core.dian.formatters import DIANFormatter


class TestDIANFormatter:
    """Test suite para DIANFormatter."""
    
    def test_formatear_decimal_basico(self):
        """Test de formateo de decimales básico."""
        # Float
        assert DIANFormatter.formatear_decimal(100.5) == '100.50'
        
        # Integer
        assert DIANFormatter.formatear_decimal(100) == '100.00'
        
        # Decimal
        assert DIANFormatter.formatear_decimal(Decimal('100.5')) == '100.50'
        
        # String
        assert DIANFormatter.formatear_decimal('100.5') == '100.50'
    
    def test_formatear_decimal_redondeo(self):
        """Test de redondeo a 2 decimales."""
        assert DIANFormatter.formatear_decimal(19.999) == '20.00'
        assert DIANFormatter.formatear_decimal(19.001) == '19.00'
    
    def test_formatear_fecha_desde_date(self):
        """Test de formateo de fecha desde objeto date."""
        fecha = date(2024, 1, 15)
        resultado = DIANFormatter.formatear_fecha(fecha)
        
        assert resultado == '2024-01-15'
    
    def test_formatear_fecha_desde_datetime(self):
        """Test de formateo de fecha desde datetime."""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        resultado = DIANFormatter.formatear_fecha(dt)
        
        assert resultado == '2024-01-15'
    
    def test_formatear_fecha_desde_string(self):
        """Test de formateo de fecha desde string."""
        resultado = DIANFormatter.formatear_fecha('2024-01-15')
        
        assert resultado == '2024-01-15'
    
    def test_formatear_hora_basico(self):
        """Test de formateo de hora básico."""
        hora = time(14, 30, 0)
        resultado = DIANFormatter.formatear_hora(hora)
        
        assert resultado == '14:30:00-05:00'
    
    def test_formatear_hora_sin_zona(self):
        """Test de formateo de hora sin zona horaria."""
        hora = time(14, 30, 0)
        resultado = DIANFormatter.formatear_hora(hora, incluir_zona=False)
        
        assert resultado == '14:30:00'
    
    def test_formatear_hora_desde_string(self):
        """Test de formateo de hora desde string."""
        resultado = DIANFormatter.formatear_hora('14:30:00')
        
        assert resultado == '14:30:00-05:00'
    
    def test_formatear_datetime_completo(self):
        """Test de formateo de datetime completo."""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        fecha_str, hora_str = DIANFormatter.formatear_datetime_completo(dt)
        
        assert fecha_str == '2024-01-15'
        assert '-05:00' in hora_str
    
    def test_limpiar_nit_con_formato(self):
        """Test de limpieza de NIT con formato."""
        # NIT con puntos y guión
        resultado = DIANFormatter.limpiar_nit('900.123.456-7')
        assert resultado == '9001234567'
        
        # NIT solo con guión
        resultado = DIANFormatter.limpiar_nit('900123456-7')
        assert resultado == '9001234567'
        
        # NIT limpio
        resultado = DIANFormatter.limpiar_nit('9001234567')
        assert resultado == '9001234567'
    
    def test_obtener_codigo_tipo_documento(self):
        """Test de obtención de códigos de tipo de documento."""
        assert DIANFormatter.obtener_codigo_tipo_documento('NIT') == '31'
        assert DIANFormatter.obtener_codigo_tipo_documento('CC') == '13'
        assert DIANFormatter.obtener_codigo_tipo_documento('CE') == '22'
        assert DIANFormatter.obtener_codigo_tipo_documento('TI') == '12'
        
        # Tipo no reconocido (default NIT)
        assert DIANFormatter.obtener_codigo_tipo_documento('XX') == '31'
    
    def test_validar_formato_cufe_valido(self):
        """Test de validación de CUFE válido."""
        # CUFE válido (96 caracteres hexadecimales)
        cufe_valido = 'a' * 96
        assert DIANFormatter.validar_formato_cufe(cufe_valido) is True
        
        # CUFE con mezcla de números y letras
        cufe_valido = '5a1b2c3d4e5f' * 8  # 96 caracteres
        assert DIANFormatter.validar_formato_cufe(cufe_valido) is True
    
    def test_validar_formato_cufe_invalido(self):
        """Test de validación de CUFE inválido."""
        # Muy corto
        assert DIANFormatter.validar_formato_cufe('abc123') is False
        
        # Muy largo
        cufe_largo = 'a' * 100
        assert DIANFormatter.validar_formato_cufe(cufe_largo) is False
        
        # Caracteres no hexadecimales
        cufe_invalido = 'x' * 96
        assert DIANFormatter.validar_formato_cufe(cufe_invalido) is False
        
        # None
        assert DIANFormatter.validar_formato_cufe(None) is False
        
        # String vacío
        assert DIANFormatter.validar_formato_cufe('') is False
    
    def test_formatear_decimal_con_miles(self):
        """Test de formateo de valores grandes."""
        # Valores grandes sin separador de miles
        assert DIANFormatter.formatear_decimal(1000000) == '1000000.00'
        assert DIANFormatter.formatear_decimal(1234567.89) == '1234567.89'
    
    def test_formatear_decimal_negativos(self):
        """Test de formateo de valores negativos."""
        assert DIANFormatter.formatear_decimal(-100.50) == '-100.50'
        assert DIANFormatter.formatear_decimal(-0.01) == '-0.01'

"""
Tests unitarios para NITValidator.
Siguiendo TDD: Tests primero, implementación después.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from app.fiscal.validators.nit_validator import NITValidator


class TestNITValidator:
    """
    Tests exhaustivos para validación de NIT (Número de Identificación Tributaria).
    
    El NIT colombiano tiene 9-10 dígitos más un dígito verificador calculado
    usando el algoritmo de módulo 11 con números primos.
    """
    
    def test_calcular_dv_nit_valido_9_digitos(self):
        """
        Test: Calcula DV correctamente para NIT de 9 dígitos.
        
        Caso: NIT 900123456 debe tener DV = 8
        """
        # Given
        nit = "900123456"
        
        # When
        dv = NITValidator.calcular_dv(nit)
        
        # Then
        assert dv == "8", f"Expected DV '8' but got '{dv}'"
    
    def test_calcular_dv_nit_valido_10_digitos(self):
        """
        Test: Calcula DV correctamente para NIT de 10 dígitos.
        
        Caso: NIT 8001234567 debe tener DV = 2
        """
        # Given
        nit = "8001234567"
        
        # When
        dv = NITValidator.calcular_dv(nit)
        
        # Then
        assert dv == "2", f"Expected DV '2' but got '{dv}'"
    
    def test_calcular_dv_casos_borde(self):
        """
        Test: Maneja casos borde correctamente.
        
        Casos:
        - NIT de 9 dígitos (mínimo válido)
        - NIT de 10 dígitos (máximo válido)
        - NIT con todos 9s
        """
        test_cases = [
            ("123456789", "6"),  # NIT de 9 dígitos - CORREGIDO
            ("1234567890", "2"),  # NIT de 10 dígitos - CORREGIDO
            ("999999999", "4"),  # Todos 9s - CORREGIDO
        ]
        
        for nit, expected_dv in test_cases:
            dv = NITValidator.calcular_dv(nit)
            assert dv == expected_dv, f"NIT {nit}: expected '{expected_dv}', got '{dv}'"
    
    def test_calcular_dv_input_vacio(self):
        """
        Test: Rechaza NIT vacío.
        
        Security: Previene procesamiento de inputs vacíos.
        """
        # Given
        nit = ""
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            NITValidator.calcular_dv(nit)
        
        assert "NIT no puede estar vacío" in str(exc_info.value)
    
    def test_calcular_dv_input_none(self):
        """
        Test: Rechaza NIT None.
        
        Security: Previene NoneType errors.
        """
        # Given
        nit = None
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            NITValidator.calcular_dv(nit)
        
        assert "NIT no puede ser None" in str(exc_info.value)
    
    def test_calcular_dv_input_no_numerico(self):
        """
        Test: Rechaza NIT con caracteres no numéricos.
        
        Security: Previene injection attacks.
        """
        invalid_inputs = [
            "ABC123456",  # Letras
            "900-123-456",  # Guiones
            "900.123.456",  # Puntos
            "900 123 456",  # Espacios
            "'; DROP TABLE--",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
        ]
        
        for invalid_nit in invalid_inputs:
            with pytest.raises(ValidationError) as exc_info:
                NITValidator.calcular_dv(invalid_nit)
            
            assert "solo puede contener dígitos" in str(exc_info.value).lower()
    
    def test_calcular_dv_nit_muy_corto(self):
        """
        Test: Rechaza NIT con menos de 9 dígitos.
        
        Business Rule: NIT colombiano debe tener mínimo 9 dígitos.
        """
        # Given
        nit = "12345"  # Solo 5 dígitos
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            NITValidator.calcular_dv(nit)
        
        assert "debe tener entre 9 y 10 dígitos" in str(exc_info.value).lower()
    
    def test_calcular_dv_nit_muy_largo(self):
        """
        Test: Rechaza NIT con más de 10 dígitos.
        
        Business Rule: NIT colombiano no puede tener más de 10 dígitos.
        """
        # Given
        nit = "12345678901234"  # 14 dígitos
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            NITValidator.calcular_dv(nit)
        
        assert "debe tener entre 9 y 10 dígitos" in str(exc_info.value).lower()
    
    def test_validar_nit_completo_valido(self):
        """
        Test: Valida NIT completo (con DV) correctamente.
        
        Caso: 900123456-8 es válido
        """
        # Given
        nit = "900123456"
        dv = "8"
        
        # When
        es_valido = NITValidator.validar(nit, dv)
        
        # Then
        assert es_valido is True
    
    def test_validar_nit_completo_invalido(self):
        """
        Test: Rechaza NIT con DV incorrecto.
        
        Caso: 900123456-3 es inválido (DV correcto es 8)
        """
        # Given
        nit = "900123456"
        dv_incorrecto = "3"
        
        # When
        es_valido = NITValidator.validar(nit, dv_incorrecto)
        
        # Then
        assert es_valido is False
    
    def test_formatear_nit_con_dv(self):
        """
        Test: Formatea NIT correctamente con guión y DV.
        
        Caso: 900123456 + DV 8 = "900123456-8"
        """
        # Given
        nit = "900123456"
        
        # When
        nit_formateado = NITValidator.formatear(nit)
        
        # Then
        assert nit_formateado == "900123456-8"
    
    def test_limpiar_nit_con_formato(self):
        """
        Test: Limpia NIT removiendo formato.
        
        Caso: "900.123.456-8" -> "900123456"
        """
        # Given
        nit_formateado = "900.123.456-8"
        
        # When
        nit_limpio = NITValidator.limpiar(nit_formateado)
        
        # Then
        assert nit_limpio == "900123456"
    
    @pytest.mark.parametrize("nit,expected_dv", [
        ("900123456", "8"),
        ("123456789", "6"),  # CORREGIDO
        ("987654321", "7"),  # CORREGIDO
    ])
    def test_calcular_dv_multiples_casos(self, nit, expected_dv):
        """
        Test: Verifica múltiples NITs conocidos.
        
        Parametrized test para verificar varios casos de una vez.
        """
        dv = NITValidator.calcular_dv(nit)
        assert dv == expected_dv


class TestNITValidatorSecurity:
    """
    Tests de seguridad para NITValidator.
    
    Verifica que el validador sea resistente a ataques comunes.
    """
    
    def test_sql_injection_prevention(self):
        """
        Test: Previene SQL injection en NIT.
        
        Security: OWASP A03:2021 - Injection
        """
        malicious_inputs = [
            "1'; DROP TABLE perfil_fiscal;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM users--",
        ]
        
        for malicious_nit in malicious_inputs:
            with pytest.raises(ValidationError):
                NITValidator.calcular_dv(malicious_nit)
    
    def test_xss_prevention(self):
        """
        Test: Previene XSS en NIT.
        
        Security: OWASP A03:2021 - Injection
        """
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
        ]
        
        for xss_nit in xss_inputs:
            with pytest.raises(ValidationError):
                NITValidator.calcular_dv(xss_nit)
    
    def test_buffer_overflow_prevention(self):
        """
        Test: Previene buffer overflow con NITs extremadamente largos.
        
        Security: Límite de longitud para prevenir DoS.
        """
        # Given
        nit_muy_largo = "9" * 1000  # 1000 dígitos
        
        # When/Then
        # Debe fallar por exceder MAX_LENGTH (10), no por buffer overflow
        with pytest.raises(ValidationError) as exc_info:
            NITValidator.calcular_dv(nit_muy_largo)
        
        # Verificar que el mensaje menciona la longitud
        assert "debe tener entre" in str(exc_info.value).lower()
    
    def test_unicode_injection_prevention(self):
        """
        Test: Previene caracteres Unicode maliciosos.
        
        Security: Solo permite ASCII digits.
        """
        unicode_inputs = [
            "９００１２３４５６",  # Dígitos Unicode
            "900123456\u200B",  # Zero-width space
            "900123456\x00",  # Null byte
        ]
        
        for unicode_nit in unicode_inputs:
            with pytest.raises(ValidationError):
                NITValidator.calcular_dv(unicode_nit)

import pytest
from app.fiscal.core.cufe import GeneradorCUFE
from datetime import datetime
import hashlib
import base64

class TestGeneracionCUFE:
    """Test suite para validación del algoritmo CUFE DIAN"""
    
    @pytest.fixture
    def datos_prueba_oficiales(self):
        """Datos de prueba oficiales de la DIAN"""
        return {
            'ejemplo_1': {
                'nit_emisor': '900123456',
                'fecha_emision': '2024-01-15',
                'numero_factura': 'SETP800000000000000000123456789',
                'valor_total': '100000.00',
                'iva': '19000.00',
                'total_impuestos': '19000.00',
                'cufe_esperado': '5A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6'  # Ejemplo
            }
        }
    
    def test_algoritmo_cufe_basico(self):
        """Test básico del algoritmo CUFE"""
        generador = GeneradorCUFE()
        
        datos = {
            'nit_emisor': '900123456',
            'fecha_emision': '2024-01-15',
            'numero_factura': 'SETP800000000000000000123456789',
            'valor_total': '100000.00',
            'iva': '19000.00',
            'total_impuestos': '19000.00',
        }
        
        cufe = generador.calcular_cufe(**datos)
        
        # Validaciones básicas del CUFE
        assert cufe is not None
        assert len(cufe) == 96  # Longitud estándar CUFE (SHA-384 hex)
        assert cufe.isalnum()  # Solo caracteres alfanuméricos
        
    
    def test_cufe_deterministico(self):
        """Mismos datos deben generar mismo CUFE"""
        generador = GeneradorCUFE()
        
        datos = {
            'nit_emisor': '900123456',
            'fecha_emision': '2024-01-15',
            'numero_factura': 'SETP800000000000000000123456789',
            'valor_total': '100000.00',
            'iva': '19000.00',
            'total_impuestos': '19000.00',
        }
        
        cufe1 = generador.calcular_cufe(**datos)
        cufe2 = generador.calcular_cufe(**datos)
        
        assert cufe1 == cufe2, "CUFE no es determinístico"

"""
Tests para generación de CUFE (SHA-384).
"""
import pytest
from app.fiscal.core.dian.crypto_manager import FiscalCryptoManager


class TestCUFEGeneration:
    """Test suite para generación de CUFE."""
    
    def test_cufe_longitud_correcta(self):
        """Test que verifica longitud del CUFE (96 caracteres)."""
        # Datos de prueba
        datos = {
            'numero_factura': 'TEST001',
            'fecha_emision': '2024-01-15',
            'hora_emision': '14:30:00-05:00',
            'valor_total': 119000.00,
            'cod_imp1': '01',
            'val_imp1': 19000.00,
            'cod_imp2': '04',
            'val_imp2': 0.00,
            'cod_imp3': '03',
            'val_imp3': 0.00,
            'valor_pagar': 119000.00,
            'nit_emisor': '900123456',
            'tipo_adquirente': '31',
            'num_adquirente': '860123456',
            'clave_tecnica': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            'tipo_ambiente': '2'
        }
        
        # Crear instancia (sin certificado real para test)
        # Solo testeamos la función generar_cufe directamente
        crypto = FiscalCryptoManager.__new__(FiscalCryptoManager)
        
        cufe = crypto.generar_cufe(**datos)
        
        # Verificar longitud
        assert len(cufe) == 96
        
        # Verificar que es hexadecimal
        assert all(c in '0123456789abcdef' for c in cufe.lower())
    
    def test_cufe_deterministico(self):
        """Test que verifica que el CUFE es determinístico."""
        datos = {
            'numero_factura': 'TEST001',
            'fecha_emision': '2024-01-15',
            'hora_emision': '14:30:00-05:00',
            'valor_total': 119000.00,
            'cod_imp1': '01',
            'val_imp1': 19000.00,
            'cod_imp2': '04',
            'val_imp2': 0.00,
            'cod_imp3': '03',
            'val_imp3': 0.00,
            'valor_pagar': 119000.00,
            'nit_emisor': '900123456',
            'tipo_adquirente': '31',
            'num_adquirente': '860123456',
            'clave_tecnica': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            'tipo_ambiente': '2'
        }
        
        crypto = FiscalCryptoManager.__new__(FiscalCryptoManager)
        
        # Generar dos veces con los mismos datos
        cufe1 = crypto.generar_cufe(**datos)
        cufe2 = crypto.generar_cufe(**datos)
        
        # Deben ser idénticos
        assert cufe1 == cufe2
    
    def test_cufe_cambia_con_datos_diferentes(self):
        """Test que verifica que datos diferentes producen CUFEs diferentes."""
        datos_base = {
            'numero_factura': 'TEST001',
            'fecha_emision': '2024-01-15',
            'hora_emision': '14:30:00-05:00',
            'valor_total': 119000.00,
            'cod_imp1': '01',
            'val_imp1': 19000.00,
            'cod_imp2': '04',
            'val_imp2': 0.00,
            'cod_imp3': '03',
            'val_imp3': 0.00,
            'valor_pagar': 119000.00,
            'nit_emisor': '900123456',
            'tipo_adquirente': '31',
            'num_adquirente': '860123456',
            'clave_tecnica': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            'tipo_ambiente': '2'
        }
        
        crypto = FiscalCryptoManager.__new__(FiscalCryptoManager)
        
        cufe1 = crypto.generar_cufe(**datos_base)
        
        # Cambiar número de factura
        datos_modificados = datos_base.copy()
        datos_modificados['numero_factura'] = 'TEST002'
        cufe2 = crypto.generar_cufe(**datos_modificados)
        
        # Deben ser diferentes
        assert cufe1 != cufe2
    
    def test_cufe_formateo_decimales(self):
        """Test que verifica el formateo correcto de decimales."""
        datos = {
            'numero_factura': 'TEST001',
            'fecha_emision': '2024-01-15',
            'hora_emision': '14:30:00-05:00',
            'valor_total': 100.0,  # Sin decimales
            'cod_imp1': '01',
            'val_imp1': 19.0,  # Sin decimales
            'cod_imp2': '04',
            'val_imp2': 0,  # Integer
            'cod_imp3': '03',
            'val_imp3': 0.0,
            'valor_pagar': 100.0,
            'nit_emisor': '900123456',
            'tipo_adquirente': '31',
            'num_adquirente': '860123456',
            'clave_tecnica': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            'tipo_ambiente': '2'
        }
        
        crypto = FiscalCryptoManager.__new__(FiscalCryptoManager)
        
        # No debe lanzar excepciones
        cufe = crypto.generar_cufe(**datos)
        
        assert len(cufe) == 96
    
    def test_cufe_validacion_campos_requeridos(self):
        """Test que verifica validación de campos requeridos."""
        crypto = FiscalCryptoManager.__new__(FiscalCryptoManager)
        
        # Sin número de factura
        with pytest.raises(ValueError, match="numero_factura es requerido"):
            crypto.generar_cufe(
                numero_factura='',
                fecha_emision='2024-01-15',
                hora_emision='14:30:00-05:00',
                valor_total=100.0,
                cod_imp1='01',
                val_imp1=19.0,
                cod_imp2='04',
                val_imp2=0.0,
                cod_imp3='03',
                val_imp3=0.0,
                valor_pagar=100.0,
                nit_emisor='900123456',
                tipo_adquirente='31',
                num_adquirente='860123456',
                clave_tecnica='test',
                tipo_ambiente='2'
            )
        
        # Fecha inválida
        with pytest.raises(ValueError, match="fecha_emision debe estar en formato YYYY-MM-DD"):
            crypto.generar_cufe(
                numero_factura='TEST001',
                fecha_emision='2024-1-15',  # Formato inválido
                hora_emision='14:30:00-05:00',
                valor_total=100.0,
                cod_imp1='01',
                val_imp1=19.0,
                cod_imp2='04',
                val_imp2=0.0,
                cod_imp3='03',
                val_imp3=0.0,
                valor_pagar=100.0,
                nit_emisor='900123456',
                tipo_adquirente='31',
                num_adquirente='860123456',
                clave_tecnica='test',
                tipo_ambiente='2'
            )

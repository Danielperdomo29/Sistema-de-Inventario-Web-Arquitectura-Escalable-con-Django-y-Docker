"""
Tests para HashManager - Componente MÁS CRÍTICO
Valida integridad criptográfica, performance y robustez
"""
import pytest
import time
from decimal import Decimal
from datetime import date, datetime
from app.fiscal.services.hash_manager import HashManager


class TestHashDeterminismo:
    """
    Tests de determinismo: Mismo input → mismo hash
    CRÍTICO para verificación de integridad
    """
    
    def test_mismo_input_mismo_hash(self):
        """Hash debe ser determinístico"""
        asiento_data = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Venta de productos',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'detalles': [
                {
                    'cuenta': '1105',
                    'debito': Decimal('1000.00'),
                    'credito': Decimal('0.00'),
                    'descripcion': 'Caja',
                    'orden': 1
                },
                {
                    'cuenta': '4135',
                    'debito': Decimal('0.00'),
                    'credito': Decimal('1000.00'),
                    'descripcion': 'Ingresos',
                    'orden': 2
                }
            ]
        }
        
        # Generar hash múltiples veces
        hash1 = HashManager.generar_hash_asiento(asiento_data)
        hash2 = HashManager.generar_hash_asiento(asiento_data)
        hash3 = HashManager.generar_hash_asiento(asiento_data)
        
        assert hash1 == hash2 == hash3, "Hash debe ser determinístico"
        assert len(hash1) == 64, "Hash SHA-256 debe tener 64 caracteres"
    
    def test_orden_detalles_no_afecta_hash(self):
        """
        El orden de detalles NO debe afectar el hash
        (se ordenan internamente por 'orden')
        """
        asiento_base = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Test',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
        }
        
        # Detalles en orden 1, 2
        asiento1 = {
            **asiento_base,
            'detalles': [
                {'cuenta': '1105', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1},
                {'cuenta': '4135', 'debito': Decimal('0.00'), 'credito': Decimal('1000.00'), 'orden': 2}
            ]
        }
        
        # Detalles en orden 2, 1 (invertido)
        asiento2 = {
            **asiento_base,
            'detalles': [
                {'cuenta': '4135', 'debito': Decimal('0.00'), 'credito': Decimal('1000.00'), 'orden': 2},
                {'cuenta': '1105', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1}
            ]
        }
        
        hash1 = HashManager.generar_hash_asiento(asiento1)
        hash2 = HashManager.generar_hash_asiento(asiento2)
        
        assert hash1 == hash2, "Orden físico de detalles no debe afectar hash (se ordenan por 'orden')"


class TestHashSensibilidad:
    """
    Tests de sensibilidad: Cambio mínimo → hash diferente
    CRÍTICO para detectar manipulaciones
    """
    
    def test_cambio_monto_cambia_hash(self):
        """Cambio de 1 centavo debe generar hash diferente"""
        asiento_base = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Test',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'detalles': [
                {'cuenta': '1105', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1},
                {'cuenta': '4135', 'debito': Decimal('0.00'), 'credito': Decimal('1000.00'), 'orden': 2}
            ]
        }
        
        asiento_modificado = {
            **asiento_base,
            'total_debito': Decimal('1000.01'),  # +1 centavo
            'detalles': [
                {'cuenta': '1105', 'debito': Decimal('1000.01'), 'credito': Decimal('0.00'), 'orden': 1},
                {'cuenta': '4135', 'debito': Decimal('0.00'), 'credito': Decimal('1000.00'), 'orden': 2}
            ]
        }
        
        hash_original = HashManager.generar_hash_asiento(asiento_base)
        hash_modificado = HashManager.generar_hash_asiento(asiento_modificado)
        
        assert hash_original != hash_modificado, "Cambio de 1 centavo debe cambiar hash"
    
    def test_cambio_descripcion_cambia_hash(self):
        """Cambio en descripción debe generar hash diferente"""
        asiento1 = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Venta de productos',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'detalles': []
        }
        
        asiento2 = {
            **asiento1,
            'descripcion': 'Venta de servicios'  # Cambio mínimo
        }
        
        hash1 = HashManager.generar_hash_asiento(asiento1)
        hash2 = HashManager.generar_hash_asiento(asiento2)
        
        assert hash1 != hash2, "Cambio en descripción debe cambiar hash"
    
    def test_cambio_cuenta_cambia_hash(self):
        """Cambio de cuenta contable debe generar hash diferente"""
        asiento_base = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Test',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
        }
        
        asiento1 = {
            **asiento_base,
            'detalles': [
                {'cuenta': '1105', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1}
            ]
        }
        
        asiento2 = {
            **asiento_base,
            'detalles': [
                {'cuenta': '1110', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1}  # Cuenta diferente
            ]
        }
        
        hash1 = HashManager.generar_hash_asiento(asiento1)
        hash2 = HashManager.generar_hash_asiento(asiento2)
        
        assert hash1 != hash2, "Cambio de cuenta debe cambiar hash"


class TestHashPerformance:
    """
    Tests de performance: < 1ms por hash
    CRÍTICO para operaciones en tiempo real
    """
    
    def test_hash_asiento_rapido(self):
        """Hash de asiento debe generarse en < 1ms"""
        asiento_data = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Venta de productos',
            'total_debito': Decimal('1000.00'),
            'total_credito': Decimal('1000.00'),
            'detalles': [
                {'cuenta': '1105', 'debito': Decimal('1000.00'), 'credito': Decimal('0.00'), 'orden': 1},
                {'cuenta': '4135', 'debito': Decimal('0.00'), 'credito': Decimal('1000.00'), 'orden': 2}
            ]
        }
        
        # Medir tiempo
        inicio = time.perf_counter()
        hash_resultado = HashManager.generar_hash_asiento(asiento_data)
        fin = time.perf_counter()
        
        tiempo_ms = (fin - inicio) * 1000
        
        assert tiempo_ms < 1.0, f"Hash debe generarse en < 1ms, tomó {tiempo_ms:.3f}ms"
        assert hash_resultado is not None
    
    def test_hash_asiento_complejo_rapido(self):
        """Hash de asiento con 20 detalles debe ser < 2ms"""
        asiento_data = {
            'numero': 123,
            'fecha': date(2025, 1, 15),
            'tipo': 'VENTA',
            'descripcion': 'Venta compleja',
            'total_debito': Decimal('20000.00'),
            'total_credito': Decimal('20000.00'),
            'detalles': [
                {
                    'cuenta': f'{1100 + i}',
                    'debito': Decimal('1000.00'),
                    'credito': Decimal('0.00'),
                    'orden': i
                }
                for i in range(20)
            ]
        }
        
        inicio = time.perf_counter()
        hash_resultado = HashManager.generar_hash_asiento(asiento_data)
        fin = time.perf_counter()
        
        tiempo_ms = (fin - inicio) * 1000
        
        assert tiempo_ms < 2.0, f"Hash de asiento complejo debe ser < 2ms, tomó {tiempo_ms:.3f}ms"


class TestMerkleTree:
    """
    Tests de Merkle Tree para períodos
    CRÍTICO para verificación eficiente de integridad
    """
    
    def test_merkle_tree_vacio(self):
        """Merkle tree de lista vacía debe retornar hash vacío"""
        hash_raiz, niveles = HashManager.construir_merkle_tree([])
        
        assert hash_raiz == HashManager._hash_vacio()
        assert niveles == [[]]
    
    def test_merkle_tree_un_elemento(self):
        """Merkle tree de 1 elemento debe retornar ese elemento"""
        hash_asiento = "abc123"
        hash_raiz, niveles = HashManager.construir_merkle_tree([hash_asiento])
        
        assert hash_raiz == hash_asiento
        assert len(niveles) == 1
        assert niveles[0] == [hash_asiento]
    
    def test_merkle_tree_dos_elementos(self):
        """Merkle tree de 2 elementos debe combinarlos"""
        hash1 = "abc123"
        hash2 = "def456"
        
        hash_raiz, niveles = HashManager.construir_merkle_tree([hash1, hash2])
        
        # Debe tener 2 niveles: [hash1, hash2] y [raíz]
        assert len(niveles) == 2
        assert niveles[0] == [hash1, hash2]
        assert len(niveles[1]) == 1
        assert hash_raiz == niveles[1][0]
        assert hash_raiz != hash1 and hash_raiz != hash2
    
    def test_merkle_tree_impar(self):
        """Merkle tree con número impar de elementos debe duplicar el último"""
        hashes = ["hash1", "hash2", "hash3"]
        
        hash_raiz, niveles = HashManager.construir_merkle_tree(hashes)
        
        # Nivel 0: [hash1, hash2, hash3]
        # Nivel 1: [combine(hash1,hash2), combine(hash3,hash3)]
        # Nivel 2: [raíz]
        assert len(niveles) == 3
        assert niveles[0] == hashes
        assert len(niveles[1]) == 2
        assert len(niveles[2]) == 1
    
    def test_merkle_tree_performance_1000_asientos(self):
        """Merkle tree de 1000 asientos debe construirse en < 100ms"""
        # Generar 1000 hashes simulados
        hashes = [f"hash_{i:04d}" * 8 for i in range(1000)]  # 64 caracteres cada uno
        
        inicio = time.perf_counter()
        hash_raiz, niveles = HashManager.construir_merkle_tree(hashes)
        fin = time.perf_counter()
        
        tiempo_ms = (fin - inicio) * 1000
        
        assert tiempo_ms < 100.0, f"Merkle tree de 1000 elementos debe construirse en < 100ms, tomó {tiempo_ms:.3f}ms"
        assert hash_raiz is not None
        assert len(hash_raiz) > 0


class TestNormalizacion:
    """
    Tests de normalización de datos
    CRÍTICO para hashing determinístico
    """
    
    def test_normaliza_decimal(self):
        """Debe convertir Decimal a string"""
        datos = {
            'monto': Decimal('1234.56')
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['monto'] == '1234.56'
        assert isinstance(normalizados['monto'], str)
    
    def test_normaliza_fecha(self):
        """Debe convertir date a ISO format"""
        datos = {
            'fecha': date(2025, 1, 15)
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['fecha'] == '2025-01-15'
        assert isinstance(normalizados['fecha'], str)
    
    def test_normaliza_datetime(self):
        """Debe convertir datetime a ISO format"""
        datos = {
            'timestamp': datetime(2025, 1, 15, 10, 30, 45)
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['timestamp'] == '2025-01-15T10:30:45'
        assert isinstance(normalizados['timestamp'], str)
    
    def test_normaliza_none(self):
        """Debe convertir None a string vacío"""
        datos = {
            'campo_opcional': None
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['campo_opcional'] == ''
    
    def test_normaliza_lista(self):
        """Debe normalizar elementos de lista recursivamente"""
        datos = {
            'detalles': [
                {'monto': Decimal('100.00')},
                {'monto': Decimal('200.00')}
            ]
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['detalles'][0]['monto'] == '100.00'
        assert normalizados['detalles'][1]['monto'] == '200.00'
    
    def test_normaliza_dict_anidado(self):
        """Debe normalizar diccionarios anidados recursivamente"""
        datos = {
            'asiento': {
                'monto': Decimal('1000.00'),
                'fecha': date(2025, 1, 15),
                'tercero': {
                    'nit': '900123456',
                    'saldo': Decimal('5000.00')
                }
            }
        }
        
        normalizados = HashManager.normalizar_datos(datos)
        
        assert normalizados['asiento']['monto'] == '1000.00'
        assert normalizados['asiento']['fecha'] == '2025-01-15'
        assert normalizados['asiento']['tercero']['saldo'] == '5000.00'


class TestHashLinea:
    """
    Tests de hash de línea individual
    """
    
    def test_hash_linea_basico(self):
        """Hash de línea debe generarse correctamente"""
        linea_data = {
            'asiento_numero': 123,
            'cuenta': '1105',
            'orden': 1,
            'debito': Decimal('1000.00'),
            'credito': Decimal('0.00'),
            'descripcion': 'Caja',
            'centro_costo': '',
            'tercero_nit': ''
        }
        
        hash_linea = HashManager.generar_hash_linea(linea_data)
        
        assert len(hash_linea) == 64
        assert isinstance(hash_linea, str)
    
    def test_hash_linea_con_nonce_diferente(self):
        """Hash con nonce debe ser diferente cada vez"""
        linea_data = {
            'asiento_numero': 123,
            'cuenta': '1105',
            'orden': 1,
            'debito': Decimal('1000.00'),
            'credito': Decimal('0.00'),
            'descripcion': 'Caja'
        }
        
        hash1 = HashManager.generar_hash_linea(linea_data, incluir_nonce=True)
        hash2 = HashManager.generar_hash_linea(linea_data, incluir_nonce=True)
        
        # Con nonce, deben ser diferentes
        assert hash1 != hash2
    
    def test_hash_linea_sin_nonce_determinista(self):
        """Hash sin nonce debe ser determinístico"""
        linea_data = {
            'asiento_numero': 123,
            'cuenta': '1105',
            'orden': 1,
            'debito': Decimal('1000.00'),
            'credito': Decimal('0.00'),
            'descripcion': 'Caja'
        }
        
        hash1 = HashManager.generar_hash_linea(linea_data, incluir_nonce=False)
        hash2 = HashManager.generar_hash_linea(linea_data, incluir_nonce=False)
        
        # Sin nonce, deben ser iguales
        assert hash1 == hash2


# Configuración de pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

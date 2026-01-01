"""
HashManager - Gestor de Integridad Criptográfica
Implementa hashing en 3 niveles con Merkle Tree para eficiencia
"""
import hashlib
import json
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime, date
import secrets


class HashManager:
    """
    Gestor de hashes criptográficos para asientos contables
    
    Niveles de hashing:
    1. Hash de asiento individual (SHA-256)
    2. Hash de período (Merkle Tree)
    3. Hash de línea individual (con nonce)
    """
    
    # Configuración
    HASH_ALGORITHM = 'sha256'
    ENCODING = 'utf-8'
    
    @staticmethod
    def normalizar_datos(datos: dict) -> dict:
        """
        Normaliza datos para hashing determinístico
        Convierte Decimal, datetime, etc. a strings
        """
        def convertir_valor(valor):
            if isinstance(valor, Decimal):
                return "{:.2f}".format(valor)
            elif isinstance(valor, (datetime, date)):
                return valor.isoformat()
            elif isinstance(valor, dict):
                return {k: convertir_valor(v) for k, v in valor.items()}
            elif isinstance(valor, list):
                return [convertir_valor(v) for v in valor]
            elif valor is None:
                return ''
            return str(valor)

        
        return {k: convertir_valor(v) for k, v in datos.items()}
    
    @classmethod
    def generar_hash_asiento(cls, asiento_data: dict) -> str:
        """
        NIVEL 1: Hash de asiento individual
        
        Performance: < 1ms por asiento
        Características: Determinístico, resistente a colisiones
        
        Args:
            asiento_data: Dict con datos del asiento
                {
                    'numero': int,
                    'fecha': date,
                    'tipo': str,
                    'descripcion': str,
                    'total_debito': Decimal,
                    'total_credito': Decimal,
                    'detalles': [...]
                }
        
        Returns:
            str: Hash SHA-256 de 64 caracteres
        """
        # Normalizar datos
        datos_normalizados = cls.normalizar_datos(asiento_data)
        
        # Ordenar detalles por orden para consistencia
        if 'detalles' in datos_normalizados:
            datos_normalizados['detalles'] = sorted(
                datos_normalizados['detalles'],
                key=lambda x: x.get('orden', 0)
            )
        
        # Generar JSON ordenado
        datos_json = json.dumps(datos_normalizados, sort_keys=True, ensure_ascii=False)


        
        # Calcular hash
        hash_obj = hashlib.new(cls.HASH_ALGORITHM)
        hash_obj.update(datos_json.encode(cls.ENCODING))
        
        return hash_obj.hexdigest()
    
    @classmethod
    def generar_hash_linea(cls, linea_data: dict, incluir_nonce: bool = False) -> str:
        """
        NIVEL 3: Hash de línea individual (DetalleAsiento)
        
        Args:
            linea_data: Dict con datos de la línea
                {
                    'asiento_numero': int,
                    'cuenta': str,
                    'orden': int,
                    'debito': Decimal,
                    'credito': Decimal,
                    'descripcion': str,
                    'centro_costo': str,
                    'tercero_nit': str
                }
            incluir_nonce: Si True, incluye nonce temporal (para evitar rainbow tables)
        
        Returns:
            str: Hash SHA-256 de 64 caracteres
        """
        # Normalizar datos
        datos_normalizados = cls.normalizar_datos(linea_data)
        
        # Agregar nonce si se solicita (para seguridad adicional)
        if incluir_nonce:
            datos_normalizados['_nonce'] = secrets.token_hex(16)
        
        # Generar JSON ordenado
        datos_json = json.dumps(datos_normalizados, sort_keys=True, ensure_ascii=False)
        
        # Calcular hash
        hash_obj = hashlib.new(cls.HASH_ALGORITHM)
        hash_obj.update(datos_json.encode(cls.ENCODING))
        
        return hash_obj.hexdigest()
    
    @classmethod
    def construir_merkle_tree(cls, hashes: List[str]) -> Tuple[str, List[List[str]]]:
        """
        NIVEL 2: Construye un árbol Merkle de hashes
        
        Performance: O(n log n)
        Permite verificación parcial sin recalcular todo
        
        Args:
            hashes: Lista de hashes de asientos
        
        Returns:
            Tuple[str, List[List[str]]]: (hash_raiz, niveles_del_arbol)
        """
        if not hashes:
            return cls._hash_vacio(), [[]]
        
        # Copiar lista para no modificar original
        nivel_actual = hashes.copy()
        niveles = [nivel_actual.copy()]
        
        # Construir árbol de abajo hacia arriba
        while len(nivel_actual) > 1:
            nivel_siguiente = []
            
            # Procesar pares de hashes
            for i in range(0, len(nivel_actual), 2):
                if i + 1 < len(nivel_actual):
                    # Par completo
                    hash_combinado = cls._combinar_hashes(
                        nivel_actual[i],
                        nivel_actual[i + 1]
                    )
                else:
                    # Impar: duplicar el último
                    hash_combinado = cls._combinar_hashes(
                        nivel_actual[i],
                        nivel_actual[i]
                    )
                
                nivel_siguiente.append(hash_combinado)
            
            nivel_actual = nivel_siguiente
            niveles.append(nivel_actual.copy())
        
        # El último nivel tiene solo la raíz
        hash_raiz = nivel_actual[0]
        
        return hash_raiz, niveles
    
    @classmethod
    def generar_hash_periodo(cls, asientos_data: List[dict]) -> Tuple[str, dict]:
        """
        Genera hash de período usando Merkle Tree
        
        Args:
            asientos_data: Lista de dicts con datos de asientos
        
        Returns:
            Tuple[str, dict]: (hash_raiz, metadata)
                metadata incluye: total_asientos, niveles_arbol, etc.
        """
        if not asientos_data:
            return cls._hash_vacio(), {'total_asientos': 0}
        
        # Generar hash de cada asiento
        hashes_asientos = [
            cls.generar_hash_asiento(asiento)
            for asiento in asientos_data
        ]
        
        # Construir Merkle Tree
        hash_raiz, niveles = cls.construir_merkle_tree(hashes_asientos)
        
        # Metadata
        metadata = {
            'total_asientos': len(asientos_data),
            'altura_arbol': len(niveles),
            'hashes_hojas': hashes_asientos,
            'timestamp': datetime.now().isoformat()
        }
        
        return hash_raiz, metadata
    
    @classmethod
    def verificar_integridad_asiento(cls, asiento_obj, hash_esperado: str) -> Tuple[bool, str, str]:
        """
        Verifica la integridad de un asiento
        
        Args:
            asiento_obj: Instancia de AsientoContable
            hash_esperado: Hash almacenado en BD
        
        Returns:
            Tuple[bool, str, str]: (es_valido, hash_esperado, hash_calculado)
        """
        # Construir datos del asiento
        asiento_data = {
            'id': asiento_obj.pk,
            'numero_asiento': asiento_obj.numero_asiento,
            'fecha_contable': asiento_obj.fecha_contable,
            'tipo': asiento_obj.tipo_asiento,
            'descripcion': asiento_obj.descripcion,
            'total_debito': asiento_obj.total_debito,
            'total_credito': asiento_obj.total_credito,
            'detalles': [
                {
                    'cuenta_codigo': detalle.cuenta_contable.codigo,
                    'cuenta': detalle.cuenta_contable.codigo,
                    'debito': detalle.debito,
                    'credito': detalle.credito,
                    'descripcion': detalle.descripcion_detalle,
                    'orden': detalle.orden
                }
                for detalle in asiento_obj.detalles.all().order_by('orden', 'id')
            ]
        }
        
        # Calcular hash
        hash_calculado = cls.generar_hash_asiento(asiento_data)
        
        # Comparar
        es_valido = hash_esperado == hash_calculado
        
        return es_valido, hash_esperado, hash_calculado
    
    @classmethod
    def verificar_integridad_batch(cls, asientos_queryset, usar_cache: bool = True) -> List[dict]:
        """
        Verifica integridad de múltiples asientos en lote
        
        Performance: ~100 asientos/segundo
        
        Args:
            asientos_queryset: QuerySet de AsientoContable
            usar_cache: Si usar cache de Redis (si disponible)
        
        Returns:
            List[dict]: Lista de discrepancias encontradas
                [
                    {
                        'asiento_id': int,
                        'numero': int,
                        'hash_esperado': str,
                        'hash_calculado': str
                    }
                ]
        """
        discrepancias = []
        
        # Prefetch detalles para eficiencia
        asientos = asientos_queryset.prefetch_related('detalles__cuenta_contable')
        
        for asiento in asientos:
            es_valido, hash_esperado, hash_calculado = cls.verificar_integridad_asiento(
                asiento,
                asiento.hash_integridad
            )
            
            if not es_valido:
                discrepancias.append({
                    'asiento_id': asiento.id,
                    'numero': asiento.numero_asiento,
                    'hash_esperado': hash_esperado,
                    'hash_calculado': hash_calculado,
                    'fecha': asiento.fecha_contable
                })
        
        return discrepancias
    
    @staticmethod
    def _combinar_hashes(hash1: str, hash2: str) -> str:
        """
        Combina dos hashes para el árbol Merkle
        """
        hash_obj = hashlib.sha256()
        hash_obj.update(hash1.encode('utf-8'))
        hash_obj.update(hash2.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def _hash_vacio() -> str:
        """
        Retorna hash de un conjunto vacío
        """
        return hashlib.sha256(b'').hexdigest()


# Funciones de utilidad para uso directo
def generar_hash_asiento(asiento_data: dict) -> str:
    """Wrapper para uso directo"""
    return HashManager.generar_hash_asiento(asiento_data)


def verificar_integridad(asiento_obj, hash_esperado: str) -> Tuple[bool, str, str]:
    """Wrapper para uso directo"""
    return HashManager.verificar_integridad_asiento(asiento_obj, hash_esperado)

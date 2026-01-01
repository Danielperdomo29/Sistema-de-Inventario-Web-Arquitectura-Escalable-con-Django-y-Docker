"""
Validador Base - Patrón Chain of Responsibility
Clase abstracta para todos los validadores DIAN
"""
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from decimal import Decimal


class ValidadorContable(ABC):
    """
    Clase base abstracta para validadores contables
    
    Implementa el patrón Chain of Responsibility
    Cada validador puede:
    1. Validar un asiento
    2. Retornar resultado (válido/inválido + mensaje)
    3. Registrar el intento en logs
    """
    
    def __init__(self):
        self.nombre = self.__class__.__name__
        self.siguiente: Optional['ValidadorContable'] = None
    
    def establecer_siguiente(self, validador: 'ValidadorContable') -> 'ValidadorContable':
        """
        Establece el siguiente validador en la cadena
        
        Returns:
            ValidadorContable: El validador establecido (para encadenamiento)
        """
        self.siguiente = validador
        return validador
    
    @abstractmethod
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida un asiento contable
        
        Args:
            asiento_data: Dict con datos del asiento a validar
                {
                    'numero_asiento': int,
                    'fecha_contable': date,
                    'tipo_asiento': str,
                    'descripcion': str,
                    'total_debito': Decimal,
                    'total_credito': Decimal,
                    'detalles': List[dict],
                    'usuario': User,
                    'periodo_contable': PeriodoContable (opcional)
                }
            contexto: Dict opcional con contexto adicional
                {
                    'request': HttpRequest,
                    'ip_origen': str,
                    'modo': 'creacion' | 'modificacion'
                }
        
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
                - es_valido: True si pasa la validación
                - mensaje_error: Descripción del error (vacío si es válido)
        """
        pass
    
    def validar_cadena(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, list]:
        """
        Ejecuta la validación en cadena
        
        Returns:
            Tuple[bool, list]: (es_valido_total, lista_errores)
        """
        errores = []
        
        # Validar con este validador
        es_valido, mensaje = self.validar(asiento_data, contexto)
        
        if not es_valido:
            errores.append({
                'validador': self.nombre,
                'mensaje': mensaje,
                'severidad': self.obtener_severidad()
            })
        
        # Continuar con el siguiente en la cadena
        if self.siguiente:
            es_valido_siguiente, errores_siguiente = self.siguiente.validar_cadena(
                asiento_data,
                contexto
            )
            errores.extend(errores_siguiente)
        
        # Retornar resultado consolidado
        es_valido_total = len(errores) == 0
        return es_valido_total, errores
    
    def obtener_severidad(self) -> str:
        """
        Retorna la severidad de este validador
        
        Returns:
            str: 'CRITICO' | 'ERROR' | 'ADVERTENCIA'
        """
        return 'ERROR'  # Por defecto
    
    def registrar_fallo(self, asiento_data: Dict, mensaje: str, contexto: Optional[Dict] = None):
        """
        Registra un fallo de validación en el log de auditoría
        """
        from app.fiscal.models import LogAuditoriaContable
        
        usuario = asiento_data.get('usuario')
        if not usuario:
            return
        
        LogAuditoriaContable.registrar(
            tipo_evento='ANOMALIA_DETECTADA',
            usuario=usuario,
            detalles={
                'validador': self.nombre,
                'mensaje': mensaje,
                'numero_asiento': asiento_data.get('numero_asiento'),
                'tipo_asiento': asiento_data.get('tipo_asiento')
            },
            ip_origen=contexto.get('ip_origen') if contexto else None,
            resultado='FALLIDO',
            severidad='WARNING'
        )


class ValidadorCritico(ValidadorContable):
    """
    Validador crítico - Si falla, bloquea completamente la operación
    """
    
    def obtener_severidad(self) -> str:
        return 'CRITICO'


class ValidadorAdvertencia(ValidadorContable):
    """
    Validador de advertencia - Permite continuar pero registra el problema
    """
    
    def obtener_severidad(self) -> str:
        return 'ADVERTENCIA'

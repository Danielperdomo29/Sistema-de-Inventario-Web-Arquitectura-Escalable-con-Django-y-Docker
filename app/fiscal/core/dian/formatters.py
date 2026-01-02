"""
Utilidades para formateo y validación de datos según estándares DIAN.
"""
from typing import Union
from decimal import Decimal
from datetime import datetime, date, time
from zoneinfo import ZoneInfo


class DIANFormatter:
    """
    Formateador de datos para cumplir con especificaciones DIAN.
    
    Asegura que todos los datos se formateen correctamente antes de:
    - Cálculo de CUFE
    - Generación de XML UBL
    - Envío a servicios DIAN
    """
    
    # Zona horaria de Colombia
    COLOMBIA_TZ = ZoneInfo('America/Bogota')
    
    @staticmethod
    def formatear_decimal(valor: Union[float, Decimal, int, str]) -> str:
        """
        Formatea un valor decimal según estándar DIAN.
        
        Reglas:
        - 2 decimales fijos
        - Punto como separador decimal
        - Sin separador de miles
        
        Args:
            valor: Valor numérico
            
        Returns:
            String con formato XX.XX
            
        Ejemplo:
            >>> DIANFormatter.formatear_decimal(1000)
            '1000.00'
            >>> DIANFormatter.formatear_decimal(19.5)
            '19.50'
        """
        if isinstance(valor, str):
            valor = float(valor.replace(',', ''))
        
        return f"{float(valor):.2f}"
    
    @staticmethod
    def formatear_fecha(fecha: Union[date, datetime, str]) -> str:
        """
        Formatea una fecha según estándar DIAN.
        
        Formato: YYYY-MM-DD
        
        Args:
            fecha: Objeto date, datetime o string
            
        Returns:
            String en formato YYYY-MM-DD
            
        Ejemplo:
            >>> DIANFormatter.formatear_fecha(date(2024, 1, 15))
            '2024-01-15'
        """
        if isinstance(fecha, str):
            # Asumir que ya está en formato correcto o intentar parsear
            if len(fecha) == 10 and fecha[4] == '-' and fecha[7] == '-':
                return fecha
            # Intentar parsear otros formatos comunes
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        
        return fecha.strftime('%Y-%m-%d')
    
    @staticmethod
    def formatear_hora(hora: Union[time, datetime, str], incluir_zona: bool = True) -> str:
        """
        Formatea una hora según estándar DIAN.
        
        Formato: HH:MM:SS-05:00 (con zona horaria Colombia)
        
        Args:
            hora: Objeto time, datetime o string
            incluir_zona: Si True, incluye zona horaria -05:00
            
        Returns:
            String en formato HH:MM:SS-05:00
            
        Ejemplo:
            >>> DIANFormatter.formatear_hora(time(14, 30, 0))
            '14:30:00-05:00'
        """
        if isinstance(hora, str):
            # Asumir formato HH:MM:SS o HH:MM:SS-05:00
            if incluir_zona and '-05:00' not in hora:
                # Quitar microsegundos si existen
                hora = hora.split('.')[0]
                return f"{hora}-05:00"
            return hora
        
        if isinstance(hora, datetime):
            hora_obj = hora.time()
        else:
            hora_obj = hora
        
        hora_str = hora_obj.strftime('%H:%M:%S')
        
        if incluir_zona:
            hora_str += '-05:00'
        
        return hora_str
    
    @staticmethod
    def formatear_datetime_completo(dt: Union[datetime, str]) -> tuple:
        """
        Formatea un datetime en fecha y hora separados según DIAN.
        
        Args:
            dt: Objeto datetime o string ISO
            
        Returns:
            Tuple (fecha_str, hora_str) en formatos DIAN
            
        Ejemplo:
            >>> DIANFormatter.formatear_datetime_completo(datetime.now())
            ('2024-01-15', '14:30:00-05:00')
        """
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        # Convertir a zona horaria Colombia si es necesario
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DIANFormatter.COLOMBIA_TZ)
        else:
            dt = dt.astimezone(DIANFormatter.COLOMBIA_TZ)
        
        fecha_str = DIANFormatter.formatear_fecha(dt)
        hora_str = DIANFormatter.formatear_hora(dt)
        
        return fecha_str, hora_str
    
    @staticmethod
    def limpiar_nit(nit: str) -> str:
        """
        Limpia un NIT removiendo caracteres no numéricos.
        
        Args:
            nit: NIT con o sin formato
            
        Returns:
            NIT solo con dígitos
            
        Ejemplo:
            >>> DIANFormatter.limpiar_nit('900.123.456-7')
            '9001234567'
        """
        return ''.join(filter(str.isdigit, nit))
    
    @staticmethod
    def obtener_codigo_tipo_documento(tipo: str) -> str:
        """
        Obtiene el código DIAN para tipo de documento de identificación.
        
        Args:
            tipo: Tipo de documento (NIT, CC, CE, etc.)
            
        Returns:
            Código DIAN (11, 12, 13, 21, 22, 31, etc.)
        """
        CODIGOS = {
            'RC': '11',      # Registro Civil
            'TI': '12',      # Tarjeta de Identidad
            'CC': '13',      # Cédula de Ciudadanía
            'TE': '21',      # Tarjeta de Extranjería
            'CE': '22',      # Cédula de Extranjería
            'NIT': '31',     # Número de Identificación Tributaria
            'PP': '41',      # Pasaporte
            'DIE': '42',     # Documento de Identificación Extranjero
            'NUIP': '50',    # NUIP (Número Único de Identificación Personal)
        }
        
        return CODIGOS.get(tipo.upper(), '31')  # Default NIT
    
    @staticmethod
    def validar_formato_cufe(cufe: str) -> bool:
        """
        Valida que un CUFE tenga el formato correcto.
        
        Args:
            cufe: String a validar
            
        Returns:
            True si el formato es válido
        """
        if not cufe:
            return False
        
        # CUFE debe ser SHA-384 en hexadecimal (96 caracteres)
        if len(cufe) != 96:
            return False
        
        # Solo caracteres hexadecimales
        try:
            int(cufe, 16)
            return True
        except ValueError:
            return False

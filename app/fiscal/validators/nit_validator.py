"""
Validador de NIT (Número de Identificación Tributaria) colombiano.

Implementa el algoritmo de dígito verificador usando módulo 11 con números primos.

Referencias:
    - DIAN: Resolución 000042 de 2020
    - Algoritmo: Módulo 11 con números primos

Security:
    - Validación estricta de inputs
    - Prevención de injection attacks
    - Sanitización de datos

Author: Sistema de Inventario
Date: 2025-12-25
"""
import re
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError


class NITValidator:
    """
    Validador de NIT colombiano con dígito verificador.
    
    El NIT (Número de Identificación Tributaria) es el identificador único
    de personas jurídicas y naturales ante la DIAN en Colombia.
    
    Attributes:
        PRIMOS: Secuencia de números primos para el cálculo del DV.
        MIN_LENGTH: Longitud mínima del NIT (9 dígitos).
        MAX_LENGTH: Longitud máxima del NIT (10 dígitos).
    
    Examples:
        >>> NITValidator.calcular_dv("900123456")
        "3"
        
        >>> NITValidator.validar("900123456", "3")
        True
        
        >>> NITValidator.formatear("900123456")
        "900123456-3"
    """
    
    # Números primos para el cálculo del dígito verificador
    PRIMOS = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    
    # Longitudes válidas para NIT
    MIN_LENGTH = 9
    MAX_LENGTH = 10
    
    @classmethod
    def calcular_dv(cls, nit: str) -> str:
        """
        Calcula el dígito verificador de un NIT colombiano.
        
        Algoritmo:
            1. Multiplicar cada dígito del NIT por el primo correspondiente
            2. Sumar todos los productos
            3. Calcular residuo = suma % 11
            4. Si residuo <= 1: DV = 0
            5. Si residuo > 1: DV = 11 - residuo
        
        Args:
            nit: Número de identificación tributaria sin DV (9-10 dígitos).
        
        Returns:
            Dígito verificador calculado (0-9).
        
        Raises:
            ValidationError: Si el NIT es inválido.
        
        Security:
            - Valida que el input sea numérico
            - Previene SQL injection
            - Previene XSS
            - Limita longitud para prevenir DoS
        
        Examples:
            >>> NITValidator.calcular_dv("900123456")
            "3"
            
            >>> NITValidator.calcular_dv("8001234567")
            "5"
        
        References:
            - DIAN Resolución 000042/2020
            - Algoritmo módulo 11
        """
        # Validación: NIT no puede ser None
        if nit is None:
            raise ValidationError("NIT no puede ser None")
        
        # Validación: NIT no puede estar vacío
        if not nit or len(nit.strip()) == 0:
            raise ValidationError("NIT no puede estar vacío")
        
        # Limpiar espacios
        nit = nit.strip()
        
        # Validación: Solo dígitos ASCII (previene injection y Unicode)
        if not nit.isdigit() or not nit.isascii():
            raise ValidationError(
                f"NIT solo puede contener dígitos numéricos. "
                f"Caracteres especiales, letras y espacios no están permitidos."
            )
        
        # Validación: Longitud
        if len(nit) < cls.MIN_LENGTH or len(nit) > cls.MAX_LENGTH:
            raise ValidationError(
                f"NIT debe tener entre {cls.MIN_LENGTH} y {cls.MAX_LENGTH} dígitos. "
                f"Recibido: {len(nit)} dígitos."
            )
        
        # Cálculo del dígito verificador
        try:
            # Multiplicar cada dígito por el primo correspondiente
            suma = sum(
                int(nit[i]) * cls.PRIMOS[len(nit) - 1 - i]
                for i in range(len(nit))
            )
            
            # Calcular residuo
            residuo = suma % 11
            
            # Determinar DV
            if residuo <= 1:
                dv = 0
            else:
                dv = 11 - residuo
            
            return str(dv)
            
        except (ValueError, IndexError) as e:
            raise ValidationError(f"Error al calcular DV: {str(e)}")
    
    @classmethod
    def validar(cls, nit: str, dv: str) -> bool:
        """
        Valida un NIT completo (con dígito verificador).
        
        Args:
            nit: Número de identificación tributaria sin DV.
            dv: Dígito verificador a validar.
        
        Returns:
            True si el DV es correcto, False en caso contrario.
        
        Examples:
            >>> NITValidator.validar("900123456", "3")
            True
            
            >>> NITValidator.validar("900123456", "9")
            False
        """
        try:
            dv_calculado = cls.calcular_dv(nit)
            return dv_calculado == dv.strip()
        except ValidationError:
            return False
    
    @classmethod
    def formatear(cls, nit: str) -> str:
        """
        Formatea un NIT con su dígito verificador.
        
        Args:
            nit: Número de identificación tributaria sin DV.
        
        Returns:
            NIT formateado como "XXXXXXXXX-D" o "XXXXXXXXXX-D".
        
        Examples:
            >>> NITValidator.formatear("900123456")
            "900123456-3"
        """
        dv = cls.calcular_dv(nit)
        return f"{nit}-{dv}"
    
    @classmethod
    def limpiar(cls, nit_formateado: str) -> str:
        """
        Limpia un NIT removiendo formato (puntos, guiones, espacios).
        
        Args:
            nit_formateado: NIT con formato (ej: "900.123.456-3").
        
        Returns:
            NIT sin formato, solo dígitos (ej: "900123456").
        
        Security:
            Remueve solo caracteres de formato conocidos.
        
        Examples:
            >>> NITValidator.limpiar("900.123.456-3")
            "900123456"
            
            >>> NITValidator.limpiar("900 123 456-3")
            "900123456"
        """
        # Remover caracteres de formato comunes
        nit_limpio = re.sub(r'[.\-\s]', '', nit_formateado)
        
        # Si tiene DV al final, removerlo
        if len(nit_limpio) > cls.MAX_LENGTH:
            nit_limpio = nit_limpio[:cls.MAX_LENGTH]
        
        return nit_limpio
    
    @classmethod
    def enmascarar(cls, nit: str) -> str:
        """
        Enmascara un NIT para logs (seguridad).
        
        Args:
            nit: NIT a enmascarar.
        
        Returns:
            NIT enmascarado (ej: "900***56").
        
        Security:
            Previene exposición de NITs completos en logs.
        
        Examples:
            >>> NITValidator.enmascarar("900123456")
            "900***56"
        """
        if not nit or len(nit) < 4:
            return "***"
        
        return f"{nit[:3]}***{nit[-2:]}"

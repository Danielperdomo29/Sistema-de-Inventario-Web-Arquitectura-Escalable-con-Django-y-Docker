"""
Validadores personalizados para módulo fiscal.

Valida códigos DANE, responsabilidades tributarias, y otros datos fiscales.
"""
import re
from django.core.exceptions import ValidationError


def validar_codigo_dane_departamento(codigo):
    """
    Valida código DANE de departamento colombiano.
    
    Args:
        codigo: Código de 2 dígitos (01-99)
    
    Raises:
        ValidationError: Si el código es inválido
    
    Examples:
        >>> validar_codigo_dane_departamento('11')  # Bogotá - OK
        >>> validar_codigo_dane_departamento('05')  # Antioquia - OK
        >>> validar_codigo_dane_departamento('1')   # Error
    """
    if not codigo:
        raise ValidationError("Código de departamento es requerido")
    
    if not re.match(r'^\d{2}$', codigo):
        raise ValidationError(
            f"Código de departamento debe tener 2 dígitos. Recibido: '{codigo}'"
        )
    
    codigo_int = int(codigo)
    if codigo_int < 1 or codigo_int > 99:
        raise ValidationError(
            f"Código de departamento debe estar entre 01 y 99. Recibido: {codigo}"
        )


def validar_codigo_dane_municipio(codigo):
    """
    Valida código DANE de municipio colombiano.
    
    Args:
        codigo: Código de 3 dígitos (001-999)
    
    Raises:
        ValidationError: Si el código es inválido
    
    Examples:
        >>> validar_codigo_dane_municipio('001')  # Capital - OK
        >>> validar_codigo_dane_municipio('1')    # Error
    """
    if not codigo:
        raise ValidationError("Código de municipio es requerido")
    
    if not re.match(r'^\d{3}$', codigo):
        raise ValidationError(
            f"Código de municipio debe tener 3 dígitos. Recibido: '{codigo}'"
        )
    
    codigo_int = int(codigo)
    if codigo_int < 1 or codigo_int > 999:
        raise ValidationError(
            f"Código de municipio debe estar entre 001 y 999. Recibido: {codigo}"
        )


def validar_responsabilidades_tributarias(responsabilidades):
    """
    Valida formato de responsabilidades tributarias DIAN.
    
    Args:
        responsabilidades: Lista de códigos como ['O-13', 'O-15', 'R-99-PN']
    
    Raises:
        ValidationError: Si algún código es inválido
    
    Examples:
        >>> validar_responsabilidades_tributarias(['O-13', 'O-15'])  # OK
        >>> validar_responsabilidades_tributarias(['INVALID'])  # Error
    """
    if not isinstance(responsabilidades, list):
        raise ValidationError("Responsabilidades debe ser una lista")
    
    # Patrón: O-XX o R-XX-XX
    patron = r'^[OR]-\d{2}(-[A-Z]{2})?$'
    
    for resp in responsabilidades:
        if not isinstance(resp, str):
            raise ValidationError(
                f"Responsabilidad debe ser string. Recibido: {type(resp)}"
            )
        
        # Prevenir injection
        if not resp.replace('-', '').replace(' ', '').isalnum():
            raise ValidationError(
                f"Responsabilidad contiene caracteres inválidos: '{resp}'"
            )
        
        if not re.match(patron, resp):
            raise ValidationError(
                f"Formato de responsabilidad inválido: '{resp}'. "
                f"Debe ser O-XX o R-XX-XX"
            )


def validar_codigo_ciiu(codigo):
    """
    Valida código CIIU (Clasificación Industrial Internacional Uniforme).
    
    Args:
        codigo: Código de 4 dígitos
    
    Raises:
        ValidationError: Si el código es inválido
    
    Examples:
        >>> validar_codigo_ciiu('4711')  # OK
        >>> validar_codigo_ciiu('47')    # Error
    """
    if not codigo:
        return  # Opcional
    
    if not re.match(r'^\d{4}$', codigo):
        raise ValidationError(
            f"Código CIIU debe tener 4 dígitos. Recibido: '{codigo}'"
        )


def validar_numero_documento(numero, tipo_documento):
    """
    Valida formato de número de documento según tipo.
    
    Args:
        numero: Número de documento
        tipo_documento: Tipo ('13'=CC, '31'=NIT, etc.)
    
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not numero:
        raise ValidationError("Número de documento es requerido")
    
    # Solo dígitos (previene injection)
    if not numero.isdigit():
        raise ValidationError(
            f"Número de documento solo puede contener dígitos. Recibido: '{numero}'"
        )
    
    # Validar longitud según tipo
    if tipo_documento == '31':  # NIT
        if len(numero) < 9 or len(numero) > 10:
            raise ValidationError(
                f"NIT debe tener 9 o 10 dígitos. Recibido: {len(numero)}"
            )
    elif tipo_documento == '13':  # Cédula
        if len(numero) < 6 or len(numero) > 10:
            raise ValidationError(
                f"Cédula debe tener entre 6 y 10 dígitos. Recibido: {len(numero)}"
            )


def sanitizar_texto(texto, max_length=200):
    """
    Sanitiza texto para prevenir XSS y otros ataques.
    
    Args:
        texto: Texto a sanitizar
        max_length: Longitud máxima
    
    Returns:
        Texto sanitizado
    """
    if not texto:
        return texto
    
    # Remover tags HTML
    texto = re.sub(r'<[^>]+>', '', texto)
    
    # Remover caracteres de control
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
    
    # Limitar longitud
    texto = texto[:max_length]
    
    return texto.strip()

"""
Utilidades de encriptación para datos fiscales sensibles.

Usa Fernet (symmetric encryption) para encriptar/desencriptar datos.
"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os


class FiscalEncryption:
    """
    Encriptación para datos fiscales sensibles.
    
    Usa Fernet (AES 128 en modo CBC con HMAC para autenticación).
    
    Examples:
        >>> encrypted = FiscalEncryption.encrypt('900123456')
        >>> decrypted = FiscalEncryption.decrypt(encrypted)
        >>> assert decrypted == '900123456'
    """
    
    @staticmethod
    def get_key():
        """
        Obtiene la clave de encriptación desde settings.
        
        Returns:
            bytes: Clave de encriptación
        """
        key = getattr(settings, 'FISCAL_ENCRYPTION_KEY', None)
        
        if not key:
            # Generar clave temporal para desarrollo
            # EN PRODUCCIÓN DEBE ESTAR EN SETTINGS
            import warnings
            warnings.warn(
                "FISCAL_ENCRYPTION_KEY not set. Using temporary key. "
                "SET THIS IN PRODUCTION!",
                RuntimeWarning
            )
            key = Fernet.generate_key()
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    @staticmethod
    def encrypt(value):
        """
        Encripta un valor.
        
        Args:
            value: Valor a encriptar (str)
        
        Returns:
            str: Valor encriptado (base64)
        
        Examples:
            >>> encrypted = FiscalEncryption.encrypt('secret')
            >>> isinstance(encrypted, str)
            True
        """
        if value is None or value == '':
            return value
        
        if not isinstance(value, str):
            value = str(value)
        
        f = Fernet(FiscalEncryption.get_key())
        encrypted_bytes = f.encrypt(value.encode('utf-8'))
        
        # Retornar como string base64
        return encrypted_bytes.decode('utf-8')
    
    @staticmethod
    def decrypt(encrypted_value):
        """
        Desencripta un valor.
        
        Args:
            encrypted_value: Valor encriptado (str base64)
        
        Returns:
            str: Valor desencriptado
        
        Examples:
            >>> encrypted = FiscalEncryption.encrypt('secret')
            >>> decrypted = FiscalEncryption.decrypt(encrypted)
            >>> assert decrypted == 'secret'
        """
        if encrypted_value is None or encrypted_value == '':
            return encrypted_value
        
        if not isinstance(encrypted_value, str):
            encrypted_value = str(encrypted_value)
        
        try:
            f = Fernet(FiscalEncryption.get_key())
            decrypted_bytes = f.decrypt(encrypted_value.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # Si falla la desencriptación, retornar el valor original
            # Esto permite migración gradual
            import logging
            logger = logging.getLogger('fiscal_encryption')
            logger.warning(f"Failed to decrypt value: {e}")
            return encrypted_value
    
    @staticmethod
    def generate_key():
        """
        Genera una nueva clave de encriptación.
        
        Returns:
            str: Clave en formato base64
        
        Examples:
            >>> key = FiscalEncryption.generate_key()
            >>> len(key) == 44  # Fernet keys are 44 chars
            True
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')

"""
Custom Django fields para encriptación de datos fiscales.
"""
from django.db import models
from app.fiscal.encryption import FiscalEncryption


class EncryptedCharField(models.CharField):
    """
    CharField que encripta automáticamente los datos.
    
    Los datos se encriptan antes de guardar en BD y se desencriptan
    al leer desde BD.
    
    Examples:
        >>> class MyModel(models.Model):
        ...     secret = EncryptedCharField(max_length=100)
        >>> obj = MyModel(secret='my_secret')
        >>> obj.save()
        >>> # En BD está encriptado
        >>> obj.refresh_from_db()
        >>> assert obj.secret == 'my_secret'  # Desencriptado automáticamente
    """
    
    description = "CharField encriptado para datos sensibles"
    
    def from_db_value(self, value, expression, connection):
        """
        Convierte valor de BD a Python (desencripta).
        
        Args:
            value: Valor desde BD (encriptado)
        
        Returns:
            str: Valor desencriptado
        """
        if value is None:
            return value
        
        return FiscalEncryption.decrypt(value)
    
    def get_prep_value(self, value):
        """
        Prepara valor para guardar en BD (encripta).
        
        Args:
            value: Valor Python (plain text)
        
        Returns:
            str: Valor encriptado
        """
        if value is None:
            return value
        
        # Encriptar el valor
        encrypted = FiscalEncryption.encrypt(value)
        
        # Asegurar que no exceda max_length
        if self.max_length and len(encrypted) > self.max_length:
            raise ValueError(
                f"Encrypted value length ({len(encrypted)}) exceeds "
                f"max_length ({self.max_length}). "
                f"Increase max_length to at least {len(encrypted) + 50}"
            )
        
        return encrypted
    
    def to_python(self, value):
        """
        Convierte valor a Python.
        
        Args:
            value: Valor desde formulario o BD
        
        Returns:
            str: Valor en Python
        """
        if isinstance(value, str) or value is None:
            return value
        
        return str(value)


class EncryptedEmailField(models.EmailField):
    """
    EmailField que encripta automáticamente los datos.
    
    Similar a EncryptedCharField pero valida email antes de encriptar.
    """
    
    description = "EmailField encriptado para datos sensibles"
    
    def from_db_value(self, value, expression, connection):
        """Desencripta valor desde BD"""
        if value is None:
            return value
        
        return FiscalEncryption.decrypt(value)
    
    def get_prep_value(self, value):
        """Encripta valor para BD"""
        if value is None:
            return value
        
        # Validar email antes de encriptar
        value = super().get_prep_value(value)
        
        # Encriptar
        encrypted = FiscalEncryption.encrypt(value)
        
        # Verificar longitud
        if self.max_length and len(encrypted) > self.max_length:
            raise ValueError(
                f"Encrypted email length ({len(encrypted)}) exceeds "
                f"max_length ({self.max_length})"
            )
        
        return encrypted
    
    def to_python(self, value):
        """Convierte a Python"""
        if isinstance(value, str) or value is None:
            return value
        
        return str(value)


class EncryptedTextField(models.TextField):
    """
    TextField que encripta automáticamente los datos.
    
    Para textos largos como direcciones.
    """
    
    description = "TextField encriptado para datos sensibles"
    
    def from_db_value(self, value, expression, connection):
        """Desencripta valor desde BD"""
        if value is None:
            return value
        
        return FiscalEncryption.decrypt(value)
    
    def get_prep_value(self, value):
        """Encripta valor para BD"""
        if value is None:
            return value
        
        return FiscalEncryption.encrypt(value)
    
    def to_python(self, value):
        """Convierte a Python"""
        if isinstance(value, str) or value is None:
            return value
        
        return str(value)

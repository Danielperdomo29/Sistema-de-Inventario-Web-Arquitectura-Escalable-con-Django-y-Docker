from cryptography.fernet import Fernet
from django.conf import settings
import base64

class FiscalEncryptionManager:
    """
    Gestor de encriptación para datos sensibles fiscales como contraseñas de certificados.
    Usa la SECRET_KEY de Django para derivar la clave de encriptación.
    """
    
    @staticmethod
    def _get_key():
        """Genera una clave válida para Fernet basada en la SECRET_KEY"""
        # Aseguramos que la clave tenga 32 bytes para base64
        key = settings.SECRET_KEY.encode()[:32]
        # Padding si es muy corta (aunque SECRET_KEY suele ser larga)
        if len(key) < 32:
            key = key.ljust(32, b'=')
        return base64.urlsafe_b64encode(key)

    @staticmethod
    def encrypt(data):
        """Encripta un string"""
        if not data:
            return None
        f = Fernet(FiscalEncryptionManager._get_key())
        return f.encrypt(data.encode()).decode()

    @staticmethod
    def decrypt(encrypted_data):
        """Desencripta un string"""
        if not encrypted_data:
            return None
        f = Fernet(FiscalEncryptionManager._get_key())
        return f.decrypt(encrypted_data.encode()).decode()

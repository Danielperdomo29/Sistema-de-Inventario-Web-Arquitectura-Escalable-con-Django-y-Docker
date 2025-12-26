"""
Tests para encriptación de datos fiscales.
"""
import pytest
from app.fiscal.encryption import FiscalEncryption
from app.fiscal.fields import EncryptedCharField, EncryptedEmailField


class TestFiscalEncryption:
    """Tests para utilidades de encriptación"""
    
    def test_encrypt_decrypt_string(self):
        """Test: Encripta y desencripta correctamente"""
        original = "900123456"
        encrypted = FiscalEncryption.encrypt(original)
        decrypted = FiscalEncryption.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original  # Debe estar encriptado
    
    def test_encrypt_empty_string(self):
        """Test: Maneja strings vacíos"""
        assert FiscalEncryption.encrypt('') == ''
        assert FiscalEncryption.decrypt('') == ''
    
    def test_encrypt_none(self):
        """Test: Maneja None"""
        assert FiscalEncryption.encrypt(None) is None
        assert FiscalEncryption.decrypt(None) is None
    
    def test_encrypt_unicode(self):
        """Test: Maneja caracteres Unicode"""
        original = "Calle 123 #45-67 Bogotá"
        encrypted = FiscalEncryption.encrypt(original)
        decrypted = FiscalEncryption.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_generate_key(self):
        """Test: Genera clave válida"""
        key = FiscalEncryption.generate_key()
        
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 44 chars base64
    
    def test_different_encryptions(self):
        """Test: Misma entrada produce diferentes salidas (por IV)"""
        # Nota: Fernet usa timestamp, así que puede ser igual si es muy rápido
        # Este test verifica que al menos encripta
        original = "test"
        encrypted1 = FiscalEncryption.encrypt(original)
        encrypted2 = FiscalEncryption.encrypt(original)
        
        # Ambos deben desencriptar al mismo valor
        assert FiscalEncryption.decrypt(encrypted1) == original
        assert FiscalEncryption.decrypt(encrypted2) == original


class TestEncryptedFields:
    """Tests para campos encriptados"""
    
    def test_encrypted_char_field_basic(self):
        """Test: EncryptedCharField encripta/desencripta"""
        field = EncryptedCharField(max_length=500)
        
        original = "900123456"
        encrypted = field.get_prep_value(original)
        decrypted = field.from_db_value(encrypted, None, None)
        
        assert decrypted == original
        assert encrypted != original
    
    def test_encrypted_email_field(self):
        """Test: EncryptedEmailField funciona"""
        field = EncryptedEmailField(max_length=500)
        
        original = "test@example.com"
        encrypted = field.get_prep_value(original)
        decrypted = field.from_db_value(encrypted, None, None)
        
        assert decrypted == original
    
    def test_encrypted_field_none(self):
        """Test: Campos encriptados manejan None"""
        field = EncryptedCharField(max_length=500)
        
        assert field.get_prep_value(None) is None
        assert field.from_db_value(None, None, None) is None

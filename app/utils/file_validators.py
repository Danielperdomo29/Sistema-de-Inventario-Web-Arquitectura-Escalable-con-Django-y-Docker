"""
Utilidades para validación segura de archivos subidos.
"""

import os
import magic
import logging
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


@deconstructible
class ReceiptFileValidator:
    """Validador para archivos de facturas"""
    
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/bmp'
    }
    
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def __call__(self, file):
        """Valida un archivo de factura"""
        
        # 1. Validar extensión
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Extensión no permitida: {ext}. "
                f"Extensiones válidas: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # 2. Validar tamaño
        if file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"El archivo es demasiado grande ({file.size/1024/1024:.1f}MB). "
                f"Máximo permitido: {self.MAX_FILE_SIZE/1024/1024}MB"
            )
        
        # 3. Validar tipo MIME real (no solo por extensión)
        try:
            # Usar python-magic para detectar tipo real
            mime = magic.Magic(mime=True)
            
            # Guardar temporalmente para leer contenido
            file.seek(0)
            file_content = file.read(2048)  # Leer primeros 2KB
            file.seek(0)
            
            mime_type = mime.from_buffer(file_content)
            
            if mime_type not in self.ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"Tipo de archivo no permitido: {mime_type}. "
                    f"Tipos válidos: {', '.join(self.ALLOWED_MIME_TYPES)}"
                )
                
        except Exception as e:
            # Si magic falla, validar por extensión
            logger.warning(f"No se pudo validar MIME type: {str(e)}")
        
        # 4. Validar nombre del archivo (seguridad)
        filename = os.path.basename(file.name)
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Nombre de archivo no válido")
        
        # 5. Validar que sea un archivo legítimo (no vacío)
        if file.size == 0:
            raise ValidationError("El archivo está vacío")
    
    def __eq__(self, other):
        """Necesario para Django"""
        return isinstance(other, ReceiptFileValidator)


# Validador instanciado para uso en modelos
validate_receipt_file = ReceiptFileValidator()

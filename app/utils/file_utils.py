"""
Utilidades para manejo seguro de archivos.
"""

import os
import uuid
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_receipt_filename(original_filename):
    """
    Genera un nombre de archivo seguro y único para facturas.
    
    Args:
        original_filename: Nombre original del archivo.
        
    Returns:
        str: Nuevo nombre de archivo con estructura organizada.
    """
    # Extraer extensión
    ext = os.path.splitext(original_filename)[1].lower()
    
    # Generar nombre único
    unique_id = uuid.uuid4().hex
    new_filename = f"{unique_id}{ext}"
    
    # Organizar por fecha
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Ruta completa
    return f"receipts/{year}/{month:02d}/{new_filename}"


def save_receipt_file(file, filename=None):
    """
    Guarda un archivo de factura de forma segura.
    
    Args:
        file: Archivo subido (UploadedFile).
        filename: Nombre opcional, si no se genera automáticamente.
        
    Returns:
        str: Ruta donde se guardó el archivo.
    """
    if filename is None:
        filename = generate_receipt_filename(file.name)
    
    # Ruta completa en el sistema de archivos
    full_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Guardar archivo
    with open(full_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    logger.info(f"Archivo de factura guardado: {filename}")
    return filename


def delete_receipt_file(file_path):
    """
    Elimina un archivo de factura de forma segura.
    
    Args:
        file_path: Ruta del archivo a eliminar.
        
    Returns:
        bool: True si se eliminó correctamente.
    """
    try:
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Archivo de factura eliminado: {file_path}")
            return True
    except Exception as e:
        logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
    
    return False


def get_receipt_url(file_path):
    """
    Obtiene la URL completa para un archivo de factura.
    
    Args:
        file_path: Ruta relativa del archivo.
        
    Returns:
        str: URL completa o None.
    """
    if not file_path:
        return None
    
    # Asegurar que la ruta no comience con slash
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    return f"{settings.MEDIA_URL}{file_path}"

import os
from io import BytesIO

from django.core.files.base import ContentFile

from PIL import Image


class UIService:
    """
    Servicio para manejar la lógica de la interfaz de usuario.
    Incluye saneamiento de imágenes para seguridad informática.
    """

    @staticmethod
    def sanitize_image(image_file, max_size=(1920, 1080), quality=85):
        """
        Desinfecta una imagen:
        1. La abre con PIL para verificar que es una imagen válida.
        2. Elimina metadatos (EXIF) para privacidad y seguridad.
        3. Redimensiona si es necesario.
        4. La re-codifica para eliminar posibles scripts inyectados.
        """
        try:
            img = Image.open(image_file)

            # Formato original
            img_format = img.format if img.format else "JPEG"

            # Quitar EXIF y transponer según orientación si es necesario
            img = Image.Image.copy(img)

            # Redimensionar si excede el máximo
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Guardar en buffer
            buffer = BytesIO()
            img.save(buffer, format=img_format, quality=quality, optimize=True)

            # Crear un nuevo archivo de contenido
            new_image = ContentFile(buffer.getvalue(), name=image_file.name)
            return new_image
        except Exception as e:
            # Si algo falla, el archivo no es una imagen válida o está corrupto
            raise ValueError(f"Archivo de imagen inválido o malicioso: {str(e)}")

    @staticmethod
    def validate_image_extension(filename):
        """Valida que la extensión sea permitida."""
        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        ext = os.path.splitext(filename)[1].lower()
        return ext in valid_extensions

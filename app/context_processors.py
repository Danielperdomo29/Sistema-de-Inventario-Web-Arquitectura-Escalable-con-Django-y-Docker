from app.models.ui_config import UIConfig


def ui_config_processor(request):
    """
    Context processor para inyectar la configuración de UI en el sistema.
    Permite el acceso dinámico a colores, logos e imágenes del carrusel.
    """
    config = UIConfig.get_active()
    background_images = config.background_images.filter(is_active=True).order_by("order")

    return {
        "ui_config": config,
        "background_images": background_images,
    }

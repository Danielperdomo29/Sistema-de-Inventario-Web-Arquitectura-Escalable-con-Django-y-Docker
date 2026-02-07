"""
Configuración de la aplicación principal del sistema de inventario.
"""
from django.apps import AppConfig


class InventarioAppConfig(AppConfig):
    """Configuración de la app de inventario"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'Sistema de Inventario'
    
    def ready(self):
        """
        Método que se ejecuta cuando Django carga la aplicación.
        Aquí importamos los signals para que se registren automáticamente.
        """
        # Importar signals para registro automático
        import app.signals.stock_signals  # noqa: F401

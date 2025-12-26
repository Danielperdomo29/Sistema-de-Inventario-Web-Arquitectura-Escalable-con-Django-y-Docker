"""
Configuración de la app fiscal.
"""
from django.apps import AppConfig


class FiscalConfig(AppConfig):
    """Configuración del módulo fiscal"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.fiscal'
    verbose_name = 'Módulo Fiscal'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import app.fiscal.signals  # noqa

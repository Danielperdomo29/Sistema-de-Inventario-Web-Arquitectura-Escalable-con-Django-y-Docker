from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Core Infrastructure'
    
    def ready(self):
        # Importar señales para conectar eventos
        try:
            import core.signals  # noqa: F401
        except ImportError:
            pass

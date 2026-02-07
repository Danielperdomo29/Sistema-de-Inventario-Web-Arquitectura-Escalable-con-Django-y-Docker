from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Analytics - Predicción y Optimización'
    
    def ready(self):
        # Registrar suscripciones al EventBus
        try:
            from analytics.signals import inicializar_suscripciones
            inicializar_suscripciones()
        except ImportError:
            pass

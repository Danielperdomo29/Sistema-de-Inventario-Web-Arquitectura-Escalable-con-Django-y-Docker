from django.apps import AppConfig


class IAConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ia'
    verbose_name = 'IA - Inteligencia Artificial con RAG'
    
    def ready(self):
        try:
            from ia.signals import inicializar_suscripciones
            inicializar_suscripciones()
        except ImportError:
            pass

"""
Señales de IA - Integración con EventBus
"""

import logging

logger = logging.getLogger(__name__)


def inicializar_suscripciones():
    """
    Inicializa suscripciones del módulo IA al EventBus
    """
    try:
        from core.event_bus import event_bus, EventTypes
        
        def on_anomalia_detectada(event_data):
            """Procesar anomalías para posibles alertas inteligentes"""
            try:
                logger.debug("IA: Recibida notificación de anomalía")
                # Futuro: Generar alerta inteligente
            except Exception as e:
                logger.warning(f"Error procesando anomalía en IA: {e}")
        
        event_bus.subscribe(EventTypes.ANOMALIA_DETECTADA, on_anomalia_detectada)
        
        logger.info("✅ IA suscrita a eventos de anomalías")
        
    except ImportError:
        logger.debug("EventBus no disponible, suscripciones de IA no configuradas")
    except Exception as e:
        logger.error(f"Error inicializando suscripciones de IA: {e}")

"""
Señales de Analytics - Integración con EventBus
"""

import logging

logger = logging.getLogger(__name__)


def inicializar_suscripciones():
    """
    Inicializa suscripciones del módulo Analytics al EventBus
    """
    try:
        from core.event_bus import event_bus, EventTypes
        
        # Suscribir a eventos de venta para actualizar modelos
        def on_venta_registrada(event_data):
            try:
                logger.debug("Analytics: Recibido evento de venta")
                # Podría invalidar cache de modelos o programar reentrenamiento
            except Exception as e:
                logger.warning(f"Error procesando venta en Analytics: {e}")
        
        event_bus.subscribe(EventTypes.VENTA_REGISTRADA, on_venta_registrada)
        
        logger.info("✅ Analytics suscrito a eventos")
        
    except ImportError:
        logger.debug("EventBus no disponible, suscripciones de Analytics no configuradas")
    except Exception as e:
        logger.error(f"Error inicializando suscripciones de Analytics: {e}")

"""
Módulo Core - Infraestructura compartida para Analytics e IA

Este módulo proporciona:
- EventBus: Sistema de eventos resiliente usando Redis Pub/Sub
- DataAggregator: Agregador de datos de todos los módulos

Uso:
    from core import event_bus, data_aggregator
    
    # Publicar evento
    event_bus.publish('VENTA_REGISTRADA', {'venta_id': 123})
    
    # Obtener datos consolidados
    dashboard = data_aggregator.obtener_dashboard_completo()
"""

default_app_config = 'core.apps.CoreConfig'

# Imports diferidos para evitar importaciones circulares
_event_bus = None
_data_aggregator = None


def get_event_bus():
    """Obtiene instancia singleton del EventBus"""
    global _event_bus
    if _event_bus is None:
        from .event_bus import event_bus
        _event_bus = event_bus
    return _event_bus


def get_data_aggregator():
    """Obtiene instancia singleton del DataAggregator"""
    global _data_aggregator
    if _data_aggregator is None:
        from .data_integration import data_aggregator
        _data_aggregator = data_aggregator
    return _data_aggregator


# Exponer para import directo
event_bus = property(lambda self: get_event_bus())
data_aggregator = property(lambda self: get_data_aggregator())

__all__ = ['get_event_bus', 'get_data_aggregator']

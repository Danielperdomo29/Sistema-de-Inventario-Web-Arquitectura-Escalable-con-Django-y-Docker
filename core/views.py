"""
Core Views - Endpoints para monitoreo y debugging del módulo Core
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """
    GET /api/core/health/
    
    Endpoint de salud para monitoreo del sistema.
    Verifica estado de Redis, EventBus y DataAggregator.
    
    Returns:
        200: Sistema saludable
        500: Sistema degradado
    """
    try:
        from core.event_bus import event_bus
        from core.data_integration import data_aggregator
        
        # Verificar EventBus
        event_bus_health = event_bus.health_check()
        
        # Verificar DataAggregator
        data_aggregator_health = data_aggregator.health_check()
        
        # Determinar estado general
        all_healthy = (
            event_bus_health['status'] == 'healthy' and 
            data_aggregator_health['status'] == 'healthy'
        )
        
        response = {
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'components': {
                'event_bus': event_bus_health,
                'data_aggregator': data_aggregator_health
            }
        }
        
        status_code = 200 if all_healthy else 500
        return JsonResponse(response, status=status_code)
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_GET
def list_event_types(request):
    """
    GET /api/core/eventos/
    
    Lista tipos de eventos disponibles y suscriptores.
    Útil para debugging y monitoreo.
    
    Returns:
        200: Lista de eventos y estadísticas
    """
    try:
        from core.event_bus import event_bus, EventTypes
        
        # Obtener estadísticas
        stats = event_bus.get_stats()
        
        # Listar todos los tipos de eventos definidos
        all_event_types = [
            attr for attr in dir(EventTypes) 
            if not attr.startswith('_') and isinstance(getattr(EventTypes, attr), str)
        ]
        
        return JsonResponse({
            'event_types_defined': all_event_types,
            'event_types_with_subscribers': list(stats['subscribers'].keys()),
            'statistics': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listando eventos: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
def get_dashboard(request):
    """
    GET /api/core/dashboard/
    
    Obtiene dashboard consolidado con datos de todos los módulos.
    
    Query params:
        fecha_inicio: Fecha inicio (ISO format)
        fecha_fin: Fecha fin (ISO format)
    
    Returns:
        200: Dashboard con KPIs, analytics, alertas
        500: Error al generar dashboard
    """
    try:
        from core.data_integration import data_aggregator
        
        # Obtener parámetros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Generar dashboard
        dashboard = data_aggregator.obtener_dashboard_completo(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        return JsonResponse(dashboard)
        
    except Exception as e:
        logger.error(f"Error generando dashboard: {e}")
        return JsonResponse({
            'error': 'No se pudo generar el dashboard',
            'detail': str(e),
            'modo_fallback': True
        }, status=500)


@require_GET
def get_context_for_ai(request):
    """
    GET /api/core/contexto-ia/
    
    Obtiene contexto estructurado para consultas de IA (patrón RAG).
    Este endpoint prepara datos relevantes para enviar a LLMs.
    
    Query params:
        intencion: Tipo de consulta (VENTAS, INVENTARIO, FINANCIERO, PREDICCION)
        limite: Máximo de registros (default: 5)
    
    Returns:
        200: Contexto estructurado para LLM
    """
    try:
        from core.data_integration import data_aggregator
        
        intencion = request.GET.get('intencion', 'GENERAL').upper()
        limite = int(request.GET.get('limite', 5))
        
        # Obtener contexto para RAG
        contexto = data_aggregator.obtener_contexto_para_consulta(
            intencion=intencion,
            usuario_id=request.user.id if request.user.is_authenticated else None,
            limite=min(limite, 20)  # Limitar máximo
        )
        
        return JsonResponse(contexto)
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto IA: {e}")
        return JsonResponse({
            'error': str(e),
            'intencion': request.GET.get('intencion', 'GENERAL')
        }, status=500)


@require_GET
def publish_test_event(request):
    """
    GET /api/core/test-evento/
    
    Endpoint de prueba para verificar que el EventBus funciona.
    Solo disponible en modo DEBUG.
    
    Returns:
        200: Evento publicado exitosamente
        403: No disponible en producción
    """
    from django.conf import settings
    
    if not settings.DEBUG:
        return JsonResponse({
            'error': 'Endpoint solo disponible en modo DEBUG'
        }, status=403)
    
    try:
        from core.event_bus import event_bus, EventTypes
        
        test_data = {
            'test': True,
            'mensaje': 'Evento de prueba',
            'timestamp': timezone.now().isoformat()
        }
        
        success = event_bus.publish(EventTypes.SISTEMA_INICIADO, test_data)
        
        return JsonResponse({
            'success': success,
            'mensaje': 'Evento de prueba publicado',
            'event_data': test_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

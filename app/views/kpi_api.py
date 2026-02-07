"""
API REST para KPIs de Productos (Componente 1).
Proporciona endpoints para dashboard con métricas de ventas e inventario.

Principios de seguridad:
- Alta disponibilidad: Cache de 15 minutos
- Confidencialidad: Solo datos agregados
- Integridad: Validación de parámetros y rate limiting
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.utils import timezone
from app.services.kpi_service import KPIService
import traceback


@require_GET
@cache_page(60 * 15)  # Cache 15 minutos
@vary_on_cookie
def get_kpi_productos(request):
    """
    GET /api/kpi/productos/?dias=7&limit=5
    
    Retorna KPIs de productos para el dashboard.
    Combina métricas de VENTAS (análisis financiero) e INVENTARIO (gestión operativa).
    
    Query params:
        - dias: Período de análisis (7, 30, 90, 180, 365) - default: 7
        - limit: Cantidad de productos a retornar (1-20) - default: 5
    
    Returns:
        {
            'ventas': {
                'top_vendidos': [...],
                'rentabilidad': [...],
                'abc_analysis': {...}
            },
            'inventario': {
                'rotacion': [...]
            },
            'timestamp': ISO datetime,
            'cache_ttl': 900
        }
    """
    try:
        # Validar y sanitizar parámetros
        dias = int(request.GET.get('dias', 7))
        limit = int(request.GET.get('limit', 5))
        
        # Validaciones de seguridad
        if dias not in [7, 30, 90, 180, 365]:
            return JsonResponse({
                'error': 'Parámetro "dias" inválido. Valores permitidos: 7, 30, 90, 180, 365'
            }, status=400)
        
        if limit < 1 or limit > 20:
            return JsonResponse({
                'error': 'Parámetro "limit" inválido. Rango permitido: 1-20'
            }, status=400)
        
        # Obtener KPIs separados por categoría con manejo de errores individual
        top_vendidos = []
        rentabilidad = []
        abc_analysis = {'productos': [], 'resumen': {}}
        rotacion = []
        
        try:
            top_vendidos = KPIService.get_top_productos(dias=dias, limit=limit)
        except Exception as e:
            print(f"[ERROR] get_top_productos: {e}")
            traceback.print_exc()
        
        try:
            rentabilidad = KPIService.get_rentabilidad_productos(dias=dias, limit=limit)
        except Exception as e:
            print(f"[ERROR] get_rentabilidad_productos: {e}")
            traceback.print_exc()
        
        try:
            abc_analysis = KPIService.get_productos_abc_analysis(dias=dias)
        except Exception as e:
            print(f"[ERROR] get_productos_abc_analysis: {e}")
            traceback.print_exc()
        
        try:
            rotacion = KPIService.get_rotacion_inventario(limit=limit)
        except Exception as e:
            print(f"[ERROR] get_rotacion_inventario: {e}")
            traceback.print_exc()
        
        data = {
            'ventas': {
                'top_vendidos': top_vendidos,
                'rentabilidad': rentabilidad,
                'abc_analysis': abc_analysis
            },
            'inventario': {
                'rotacion': rotacion
            },
            'metadata': {
                'timestamp': timezone.now().isoformat(),
                'cache_ttl': 900,  # 15 minutos en segundos
                'periodo_dias': dias,
                'limite_productos': limit
            }
        }
        
        return JsonResponse(data)
    
    except ValueError as e:
        return JsonResponse({
            'error': f'Parámetros inválidos: {str(e)}'
        }, status=400)
    
    except Exception as e:
        # Log del error con traceback completo
        print(f"[ERROR] API KPI Productos: {str(e)}")
        traceback.print_exc()
        
        return JsonResponse({
            'error': 'Error interno del servidor',
            'error_detail': str(e),
            'ventas': {
                'top_vendidos': [],
                'rentabilidad': [],
                'abc_analysis': {'productos': [], 'resumen': {}}
            },
            'inventario': {
                'rotacion': []
            }
        }, status=500)


@require_GET
@cache_page(60 * 15)
def get_kpi_abc_detalle(request):
    """
    GET /api/kpi/productos/abc/?dias=30
    
    Endpoint específico para análisis ABC de Pareto.
    Útil para gráficas detalladas de clasificación de productos.
    
    Query params:
        - dias: Período de análisis (default: 30)
    
    Returns:
        {
            'productos': List[Dict],
            'resumen': Dict,
            'metadata': Dict
        }
    """
    try:
        dias = int(request.GET.get('dias', 30))
        
        if dias not in [7, 30, 90, 180, 365]:
            return JsonResponse({
                'error': 'Parámetro "dias" inválido'
            }, status=400)
        
        resultado = KPIService.get_productos_abc_analysis(dias=dias)
        resultado['metadata'] = {
            'timestamp': timezone.now().isoformat(),
            'periodo_dias': dias
        }
        
        return JsonResponse(resultado)
    
    except Exception as e:
        print(f"[ERROR] API ABC Analysis: {str(e)}")
        return JsonResponse({
            'error': 'Error interno del servidor'
        }, status=500)


@require_GET
def invalidar_cache_kpis(request):
    """
    GET /api/kpi/invalidar-cache/
    
    Invalida el caché de KPIs.
    Útil después de actualizaciones masivas de datos.
    
    NOTA: En producción, este endpoint debería estar protegido
    con autenticación de administrador.
    """
    try:
        KPIService.clear_all_kpi_cache()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Caché de KPIs invalidado exitosamente',
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

"""
API para gestión de alertas de stock en tiempo real.
Proporciona endpoints para polling de alertas y actualización de estado.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from app.models.alerta_automatica import AlertaAutomatica


@require_GET
def get_pending_stock_alerts(request):
    """
    GET /api/stock/alertas-pendientes/
    
    Retorna alertas de stock pendientes para mostrar en UI.
    El frontend hace polling cada 30 segundos.
    
    Returns:
        JsonResponse con lista de alertas pendientes
    """
    try:
        alertas = AlertaAutomatica.objects.filter(
            estado='PENDIENTE',
            tipo_alerta__in=['STOCK_CRITICO', 'STOCK_BAJO']
        ).select_related('producto').order_by('-nivel', 'fecha_creacion')[:10]
        
        data = []
        for alerta in alertas:
            data.append({
                'id': alerta.id,
                'nivel': alerta.nivel,
                'tipo': alerta.tipo_alerta,
                'mensaje': alerta.mensaje,
                'producto_id': alerta.producto.id,
                'producto_nombre': alerta.producto.nombre,
                'stock_actual': alerta.producto.stock_actual,
                'stock_minimo': alerta.producto.stock_minimo,
                'url_editar': f'/productos/{alerta.producto.id}/editar/',
                'fecha_creacion': alerta.fecha_creacion.isoformat()
            })
        
        return JsonResponse({'alertas': data, 'count': len(data)})
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'alertas': [],
            'count': 0
        }, status=500)


@require_POST
@csrf_exempt  # Temporal, luego agregar CSRF token en el frontend
def mark_alert_as_reviewed(request, alerta_id):
    """
    POST /api/stock/alertas/<id>/revisar/
    
    Marca una alerta como revisada (usuario la vio).
    
    Args:
        request: HttpRequest
        alerta_id: ID de la alerta
        
    Returns:
        JsonResponse con resultado de la operación
    """
    try:
        alerta = AlertaAutomatica.objects.get(id=alerta_id)
        alerta.revisar()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Alerta marcada como revisada'
        })
    
    except AlertaAutomatica.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alerta no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@csrf_exempt
def mark_alert_as_resolved(request, alerta_id):
    """
    POST /api/stock/alertas/<id>/resolver/
    
    Marca una alerta como resuelta.
    
    Args:
        request: HttpRequest
        alerta_id: ID de la alerta
        
    Returns:
        JsonResponse con resultado de la operación
    """
    try:
        alerta = AlertaAutomatica.objects.get(id=alerta_id)
        alerta.resolver()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Alerta marcada como resuelta'
        })
    
    except AlertaAutomatica.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alerta no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def get_all_alerts(request):
    """
    GET /api/stock/alertas/?estado=PENDIENTE&nivel=ROJO
    
    Retorna todas las alertas con filtros opcionales.
    
    Query params:
        - estado: PENDIENTE, REVISADA, RESUELTA, IGNORADA
        - nivel: ROJO, AMARILLO, VERDE
        - tipo: STOCK_CRITICO, STOCK_BAJO, etc.
        - limit: Cantidad máxima de resultados (default: 50)
        
    Returns:
        JsonResponse con lista de alertas
    """
    try:
        # Obtener filtros de query params
        estado = request.GET.get('estado')
        nivel = request.GET.get('nivel')
        tipo = request.GET.get('tipo')
        limit = int(request.GET.get('limit', 50))
        
        # Construir query
        queryset = AlertaAutomatica.objects.select_related('producto')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if nivel:
            queryset = queryset.filter(nivel=nivel)
        if tipo:
            queryset = queryset.filter(tipo_alerta=tipo)
        
        alertas = queryset.order_by('-nivel', '-fecha_creacion')[:limit]
        
        data = []
        for alerta in alertas:
            producto_data = None
            if alerta.producto:
                producto_data = {
                    'id': alerta.producto.id,
                    'nombre': alerta.producto.nombre,
                    'codigo': alerta.producto.codigo,
                    'stock_actual': alerta.producto.stock_actual,
                    'stock_minimo': alerta.producto.stock_minimo,
                    'url_editar': f'/productos/{alerta.producto.id}/editar/'
                }
            
            data.append({
                'id': alerta.id,
                'tipo': alerta.tipo_alerta,
                'nivel': alerta.nivel,
                'estado': alerta.estado,
                'mensaje': alerta.mensaje,
                'accion_sugerida': alerta.accion_sugerida,
                'producto': producto_data,
                'fecha_creacion': alerta.fecha_creacion.isoformat(),
                'fecha_resolucion': alerta.fecha_resolucion.isoformat() if alerta.fecha_resolucion else None,
                'dias_pendiente': alerta.dias_pendiente
            })
        
        return JsonResponse({
            'alertas': data,
            'count': len(data),
            'filtros': {
                'estado': estado,
                'nivel': nivel,
                'tipo': tipo
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'alertas': [],
            'count': 0
        }, status=500)

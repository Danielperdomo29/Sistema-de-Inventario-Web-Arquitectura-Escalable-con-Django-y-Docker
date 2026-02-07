"""
Vistas API de Analytics

Seguridad:
- Endpoints protegidos por API Token o sesión de usuario
- Rate limiting configurable
"""

import logging
from datetime import date, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone

from core.security import api_token_required
from .services import ETLProcessor, DemandForecaster, InventoryOptimizer, AnomalyDetector

logger = logging.getLogger(__name__)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def predecir_demanda(request):
    """
    GET /api/analytics/prediccion/
    
    Predice demanda de un producto
    
    Query params:
        producto_id: ID del producto (requerido)
        dias: Días a predecir (default: 30)
    """
    try:
        producto_id = request.GET.get('producto_id')
        dias = int(request.GET.get('dias', 30))
        
        if not producto_id:
            return JsonResponse({
                'error': 'producto_id es requerido'
            }, status=400)
        
        forecaster = DemandForecaster()
        resultado = forecaster.predecir_demanda(int(producto_id), dias)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def optimizar_inventario(request):
    """
    GET /api/analytics/optimizacion/
    
    Calcula parámetros óptimos de inventario
    
    Query params:
        producto_id: ID del producto (requerido)
        nivel_servicio: 0.90-0.99 (default: 0.95)
        lead_time: Días de entrega (default: 7)
    """
    try:
        producto_id = request.GET.get('producto_id')
        nivel_servicio = float(request.GET.get('nivel_servicio', 0.95))
        lead_time = int(request.GET.get('lead_time', 7))
        
        if not producto_id:
            return JsonResponse({
                'error': 'producto_id es requerido'
            }, status=400)
        
        optimizer = InventoryOptimizer()
        resultado = optimizer.optimizar_producto(
            int(producto_id),
            nivel_servicio=nivel_servicio,
            lead_time_dias=lead_time
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error en optimización: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def clasificacion_abc(request):
    """
    GET /api/analytics/abc/
    
    Clasificación ABC de productos
    
    Query params:
        top_n: Número de productos a analizar (default: 100)
    """
    try:
        top_n = int(request.GET.get('top_n', 100))
        
        optimizer = InventoryOptimizer()
        resultado = optimizer.clasificacion_abc(top_n)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error en clasificación ABC: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def detectar_anomalias(request):
    """
    GET /api/analytics/anomalias/
    
    Detecta anomalías en ventas
    
    Query params:
        dias: Días a analizar (default: 30)
        umbral: Z-score threshold (default: 3.0)
    """
    try:
        dias = int(request.GET.get('dias', 30))
        umbral = float(request.GET.get('umbral', 3.0))
        
        detector = AnomalyDetector()
        resultado = detector.detectar_anomalias_ventas(dias, umbral)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error detectando anomalías: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def productos_sin_movimiento(request):
    """
    GET /api/analytics/sin-movimiento/
    
    Lista productos sin ventas recientes
    
    Query params:
        dias: Días sin venta (default: 30)
    """
    try:
        dias = int(request.GET.get('dias', 30))
        
        detector = AnomalyDetector()
        resultado = detector.detectar_productos_sin_movimiento(dias)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error detectando productos sin movimiento: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def entrenar_modelo(request):
    """
    GET /api/analytics/entrenar/
    
    Entrena modelo de predicción para un producto
    
    Query params:
        producto_id: ID del producto (None = general)
        forzar: true/false - Forzar reentrenamiento
    """
    try:
        producto_id = request.GET.get('producto_id')
        forzar = request.GET.get('forzar', 'false').lower() == 'true'
        
        forecaster = DemandForecaster()
        resultado = forecaster.entrenar_modelo(
            producto_id=int(producto_id) if producto_id else None,
            forzar=forzar
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error entrenando modelo: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
def health_check(request):
    """
    GET /api/analytics/health/
    
    Verificación de salud del módulo Analytics
    """
    try:
        checks = {
            'etl_processor': False,
            'demand_forecaster': False,
            'inventory_optimizer': False,
            'anomaly_detector': False,
            'sklearn_disponible': False
        }
        
        # Verificar servicios
        try:
            etl = ETLProcessor()
            checks['etl_processor'] = True
        except Exception:
            pass
        
        try:
            forecaster = DemandForecaster()
            checks['demand_forecaster'] = True
        except Exception:
            pass
        
        try:
            optimizer = InventoryOptimizer()
            checks['inventory_optimizer'] = True
        except Exception:
            pass
        
        try:
            detector = AnomalyDetector()
            checks['anomaly_detector'] = True
        except Exception:
            pass
        
        # Verificar sklearn
        try:
            import sklearn
            checks['sklearn_disponible'] = True
            checks['sklearn_version'] = sklearn.__version__
        except ImportError:
            pass
        
        all_ok = all([
            checks['etl_processor'],
            checks['demand_forecaster'],
            checks['anomaly_detector']
        ])
        
        return JsonResponse({
            'status': 'healthy' if all_ok else 'degraded',
            'checks': checks,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

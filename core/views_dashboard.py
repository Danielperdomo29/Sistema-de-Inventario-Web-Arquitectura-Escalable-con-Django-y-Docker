"""
Dashboard Unificado - Vista consolidada de todos los módulos

Integra:
- Core: EventBus, DataAggregator
- Analytics: Predicciones, Anomalías, Optimización
- IA: Chatbot RAG, Recomendaciones
- Fiscal: KPIs financieros

Seguridad:
- Endpoints protegidos por API Token o sesión
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone

from core.security import api_token_required

logger = logging.getLogger(__name__)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def dashboard_unificado(request):
    """
    GET /api/dashboard/unificado/
    
    Dashboard ejecutivo que consolida todos los módulos
    """
    resultado = {
        'timestamp': timezone.now().isoformat(),
        'secciones': {},
        'alertas': [],
        'estado_sistema': {}
    }
    
    try:
        # 1. Obtener datos consolidados de Core
        resultado['secciones']['core'] = _obtener_datos_core()
        
        # 2. Obtener predicciones de Analytics
        resultado['secciones']['analytics'] = _obtener_datos_analytics()
        
        # 3. Obtener recomendaciones de IA
        resultado['secciones']['ia'] = _obtener_datos_ia()
        
        # 4. Obtener KPIs financieros
        resultado['secciones']['finanzas'] = _obtener_datos_financieros()
        
        # 5. Consolidar alertas
        resultado['alertas'] = _consolidar_alertas(resultado['secciones'])
        
        # 6. Estado del sistema
        resultado['estado_sistema'] = _verificar_estado_sistema()
        
        resultado['exito'] = True
        
    except Exception as e:
        logger.error(f"Error generando dashboard unificado: {e}")
        resultado['exito'] = False
        resultado['error'] = str(e)
    
    return JsonResponse(resultado)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def resumen_ejecutivo(request):
    """
    GET /api/dashboard/resumen/
    
    Resumen ejecutivo rápido para la vista principal
    """
    try:
        from core.data_integration import data_aggregator
        
        resumen = data_aggregator.get_dashboard_summary()
        
        # Agregar indicadores de confianza de predicción
        try:
            from analytics.services import DemandForecaster
            forecaster = DemandForecaster()
            modelos_entrenados = len(forecaster.get_productos_con_modelo())
            resumen['modelos_ml'] = {
                'productos_con_prediccion': modelos_entrenados,
                'disponible': modelos_entrenados > 0
            }
        except Exception:
            resumen['modelos_ml'] = {'disponible': False}
        
        return JsonResponse({
            'exito': True,
            'resumen': resumen,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando resumen: {e}")
        return JsonResponse({
            'exito': False,
            'error': str(e)
        }, status=500)


@require_GET
def health_check_global(request):
    """
    GET /api/dashboard/health/
    
    Estado de salud de todos los módulos
    """
    modulos = {
        'core': False,
        'analytics': False,
        'ia': False,
        'fiscal': False,
        'base_datos': False
    }
    
    try:
        # Core
        try:
            from core.event_bus import event_bus
            modulos['core'] = event_bus is not None
        except Exception:
            pass
        
        # Analytics
        try:
            from analytics.services import ETLProcessor
            ETLProcessor()
            modulos['analytics'] = True
        except Exception:
            pass
        
        # IA
        try:
            from ia.services import IntelligentChatbot
            IntelligentChatbot()
            modulos['ia'] = True
        except Exception:
            pass
        
        # Fiscal
        try:
            from app.fiscal.models import CuentaContable
            modulos['fiscal'] = True
        except Exception:
            pass
        
        # Base de datos
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            modulos['base_datos'] = True
        except Exception:
            pass
        
        saludables = sum(1 for v in modulos.values() if v)
        total = len(modulos)
        
        return JsonResponse({
            'status': 'healthy' if saludables == total else 'degraded',
            'modulos': modulos,
            'saludables': saludables,
            'total': total,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


def _obtener_datos_core() -> Dict[str, Any]:
    """Obtiene datos del módulo Core"""
    try:
        from core.data_integration import data_aggregator
        from core.event_bus import event_bus
        
        return {
            'kpis': data_aggregator.get_dashboard_summary(),
            'eventos_activos': len(event_bus._subscribers),
            'estado': 'activo'
        }
    except Exception as e:
        return {'error': str(e), 'estado': 'error'}


def _obtener_datos_analytics() -> Dict[str, Any]:
    """Obtiene datos del módulo Analytics"""
    try:
        from analytics.services import AnomalyDetector, InventoryOptimizer
        
        # Anomalías recientes
        detector = AnomalyDetector()
        anomalias = detector.detectar_anomalias_ventas(dias=7)
        
        # Clasificación ABC resumen
        optimizer = InventoryOptimizer()
        abc = optimizer.clasificacion_abc(top_n=50)
        
        return {
            'anomalias': {
                'total': anomalias.get('resumen', {}).get('total_anomalias', 0),
                'criticas': anomalias.get('resumen', {}).get('criticas', 0)
            },
            'productos_abc': {
                'A': abc.get('resumen', {}).get('productos_A', 0),
                'B': abc.get('resumen', {}).get('productos_B', 0),
                'C': abc.get('resumen', {}).get('productos_C', 0)
            },
            'estado': 'activo'
        }
    except Exception as e:
        return {'error': str(e), 'estado': 'error'}


def _obtener_datos_ia() -> Dict[str, Any]:
    """Obtiene datos del módulo IA"""
    try:
        from ia.services import RecommendationEngine
        
        engine = RecommendationEngine()
        recomendaciones = engine.obtener_recomendaciones_completas()
        
        return {
            'productos_reabastecer': recomendaciones.get('resumen', {}).get('productos_reabastecer', 0),
            'productos_liquidar': recomendaciones.get('resumen', {}).get('productos_liquidar', 0),
            'productos_estrella': recomendaciones.get('resumen', {}).get('productos_estrella', 0),
            'chatbot_disponible': True,
            'estado': 'activo'
        }
    except Exception as e:
        return {'error': str(e), 'estado': 'error'}


def _obtener_datos_financieros() -> Dict[str, Any]:
    """Obtiene datos financieros"""
    try:
        from app.services.kpi_service import KPIService
        
        servicio = KPIService()
        
        # Obtener algunos KPIs clave
        periodo = 30  # últimos 30 días
        
        return {
            'margen_estimado': servicio._format_percentage(35.5),  # Placeholder
            'rotacion_inventario': 'Normal',
            'estado': 'activo'
        }
    except Exception as e:
        return {'error': str(e), 'estado': 'error'}


def _consolidar_alertas(secciones: Dict) -> list:
    """Consolida alertas de todos los módulos"""
    alertas = []
    
    # Alertas de Analytics
    analytics = secciones.get('analytics', {})
    if analytics.get('anomalias', {}).get('criticas', 0) > 0:
        alertas.append({
            'tipo': 'CRITICA',
            'modulo': 'Analytics',
            'mensaje': f"{analytics['anomalias']['criticas']} anomalías críticas detectadas",
            'accion': 'Revisar ventas inusuales'
        })
    
    # Alertas de IA (reabastecimiento)
    ia = secciones.get('ia', {})
    if ia.get('productos_reabastecer', 0) > 0:
        alertas.append({
            'tipo': 'ALTA',
            'modulo': 'Inventario',
            'mensaje': f"{ia['productos_reabastecer']} productos necesitan reabastecimiento",
            'accion': 'Generar orden de compra'
        })
    
    if ia.get('productos_liquidar', 0) > 5:
        alertas.append({
            'tipo': 'MEDIA',
            'modulo': 'Inventario',
            'mensaje': f"{ia['productos_liquidar']} productos sin rotación",
            'accion': 'Considerar promoción'
        })
    
    return sorted(alertas, key=lambda x: {'CRITICA': 0, 'ALTA': 1, 'MEDIA': 2}.get(x['tipo'], 3))


def _verificar_estado_sistema() -> Dict[str, Any]:
    """Verifica estado general del sistema"""
    return {
        'uptime': 'Disponible',
        'ultima_sincronizacion': timezone.now().isoformat(),
        'version': '2.0.0-modular'
    }

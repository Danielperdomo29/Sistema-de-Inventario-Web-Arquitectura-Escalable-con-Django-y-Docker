"""
Vistas API del módulo IA

Seguridad:
- Endpoints protegidos por API Token o sesión de usuario
- Rate limiting: 50 req/min para chat, 100 req/min para otros
"""

import logging
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from core.security import api_token_required
from .services import IntelligentChatbot, RecommendationEngine

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
@api_token_required(allow_session=True, rate_limit=50)  # Limit chat requests
def chat(request):
    """
    POST /api/ia/chat/
    
    Endpoint principal del chatbot con RAG
    
    Body JSON:
        mensaje: Mensaje del usuario
        session_id: ID de sesión (opcional)
    """
    try:
        data = json.loads(request.body)
        mensaje = data.get('mensaje', '').strip()
        session_id = data.get('session_id')
        
        if not mensaje:
            return JsonResponse({
                'error': 'El mensaje es requerido'
            }, status=400)
        
        chatbot = IntelligentChatbot()
        resultado = chatbot.procesar_mensaje(
            mensaje=mensaje,
            user_id=request.user.id,
            session_id=session_id
        )
        
        return JsonResponse(resultado)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def historial_chat(request):
    """
    GET /api/ia/historial/
    
    Obtiene historial de chat del usuario
    
    Query params:
        session_id: ID de sesión (opcional)
    """
    try:
        session_id = request.GET.get('session_id')
        
        chatbot = IntelligentChatbot()
        historial = chatbot.obtener_historial(
            user_id=request.user.id,
            session_id=session_id
        )
        
        return JsonResponse({
            'historial': historial,
            'total': len(historial)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_POST
@api_token_required(allow_session=True, rate_limit=50)
def limpiar_historial(request):
    """
    POST /api/ia/limpiar-historial/
    
    Limpia historial de chat
    """
    try:
        chatbot = IntelligentChatbot()
        chatbot.limpiar_historial(user_id=request.user.id)
        
        return JsonResponse({
            'exito': True,
            'mensaje': 'Historial limpiado'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def obtener_recomendaciones(request):
    """
    GET /api/ia/recomendaciones/
    
    Obtiene todas las recomendaciones inteligentes
    """
    try:
        engine = RecommendationEngine()
        resultado = engine.obtener_recomendaciones_completas(
            user_id=request.user.id
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
@api_token_required(allow_session=True, rate_limit=100)
def productos_relacionados(request):
    """
    GET /api/ia/relacionados/
    
    Obtiene productos relacionados (cross-selling)
    
    Query params:
        producto_id: ID del producto (requerido)
        limite: Número máximo de relacionados (default: 5)
    """
    try:
        producto_id = request.GET.get('producto_id')
        limite = int(request.GET.get('limite', 5))
        
        if not producto_id:
            return JsonResponse({
                'error': 'producto_id es requerido'
            }, status=400)
        
        engine = RecommendationEngine()
        resultado = engine.obtener_productos_relacionados(
            int(producto_id), limite
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error obteniendo productos relacionados: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_GET
def health_check(request):
    """
    GET /api/ia/health/
    
    Verificación de salud del módulo IA
    """
    try:
        checks = {
            'chatbot': False,
            'recommendation_engine': False,
            'llm_configurado': False,
            'data_aggregator': False
        }
        
        # Verificar chatbot
        try:
            chatbot = IntelligentChatbot()
            checks['chatbot'] = True
            checks['llm_configurado'] = chatbot.api_key is not None
        except Exception:
            pass
        
        # Verificar recommendation engine
        try:
            engine = RecommendationEngine()
            checks['recommendation_engine'] = True
        except Exception:
            pass
        
        # Verificar DataAggregator
        try:
            from core.data_integration import data_aggregator
            checks['data_aggregator'] = data_aggregator is not None
        except Exception:
            pass
        
        all_ok = checks['chatbot'] and checks['recommendation_engine']
        
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

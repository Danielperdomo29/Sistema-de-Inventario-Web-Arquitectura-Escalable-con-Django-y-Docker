"""
Intelligent Chatbot - Chatbot con patrón RAG

Punto Crítico del Plan:
> Implementar patrón **RAG** (Retrieval-Augmented Generation) para
> optimizar costos y eficiencia de LLMs, enviando solo contexto específico.

Flujo RAG:
1. Usuario hace pregunta
2. Clasificar intención (ventas, inventario, finanzas, etc.)
3. Obtener contexto relevante de DataAggregator
4. Construir prompt con contexto específico
5. Enviar a LLM y obtener respuesta
6. Guardar en historial

Integración LLM:
- OpenRouter como gateway
- DeepSeek para análisis de datos
- ChatGPT para interacción conversacional
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import re

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class IntelligentChatbot:
    """
    Chatbot inteligente con patrón RAG
    
    Usa DataAggregator para obtener contexto relevante antes de
    enviar consultas al LLM, optimizando costos y precisión.
    """
    
    # Configuración
    MAX_CONTEXT_CHARS = 4000  # Límite de contexto para LLM
    CACHE_TTL_SECONDS = 300  # 5 minutos
    MAX_HISTORY_MESSAGES = 10
    
    # Clasificación de intenciones
    INTENCIONES = {
        'VENTAS': ['venta', 'vendido', 'factura', 'ingreso', 'cliente', 'cotizacion'],
        'INVENTARIO': ['stock', 'producto', 'inventario', 'existencia', 'agotado', 'minimo'],
        'COMPRAS': ['compra', 'proveedor', 'pedido', 'orden', 'costo'],
        'FINANZAS': ['ganancia', 'utilidad', 'margen', 'rentabilidad', 'contabilidad', 'balance'],
        'PREDICCION': ['predecir', 'pronostico', 'tendencia', 'futuro', 'proyeccion'],
        'ANOMALIAS': ['problema', 'bajo', 'alerta', 'unusual', 'raro', 'anomalia'],
        'GENERAL': []  # Fallback
    }
    
    # Templates de prompt por intención
    PROMPT_TEMPLATES = {
        'VENTAS': """Eres un asistente de análisis de ventas. Responde basándote en los siguientes datos:

DATOS DE VENTAS:
{contexto}

PREGUNTA DEL USUARIO: {pregunta}

Responde de forma clara y concisa, usando los datos proporcionados. Si no tienes información suficiente, indícalo.""",

        'INVENTARIO': """Eres un asistente de gestión de inventario. Analiza los siguientes datos:

DATOS DE INVENTARIO:
{contexto}

PREGUNTA DEL USUARIO: {pregunta}

Proporciona recomendaciones específicas basadas en los datos. Menciona productos con stock bajo si es relevante.""",

        'FINANZAS': """Eres un asistente financiero. Analiza los siguientes KPIs y métricas:

DATOS FINANCIEROS:
{contexto}

PREGUNTA DEL USUARIO: {pregunta}

Proporciona análisis claro con números específicos cuando estén disponibles.""",

        'PREDICCION': """Eres un asistente de análisis predictivo. Revisa las siguientes proyecciones:

DATOS DE PREDICCIÓN:
{contexto}

PREGUNTA DEL USUARIO: {pregunta}

IMPORTANTE: Incluye el nivel de confianza e intervalo de error en tu respuesta.""",

        'GENERAL': """Eres un asistente de gestión empresarial. Contexto del negocio:

{contexto}

PREGUNTA DEL USUARIO: {pregunta}

Responde de forma útil y profesional."""
    }
    
    def __init__(self):
        self.llm_client = None
        self._inicializar_cliente_llm()
    
    def _inicializar_cliente_llm(self):
        """Inicializa cliente para OpenRouter/DeepSeek"""
        try:
            import httpx
            
            self.api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
            if not self.api_key:
                self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
            
            self.api_url = getattr(
                settings, 
                'OPENROUTER_API_URL', 
                'https://openrouter.ai/api/v1/chat/completions'
            )
            
            self.model = getattr(
                settings,
                'LLM_MODEL',
                'deepseek/deepseek-chat'  # Económico y eficiente
            )
            
            if self.api_key:
                self.llm_client = httpx.Client(timeout=30.0)
                logger.info(f"Cliente LLM inicializado: {self.model}")
            else:
                logger.warning("API key para LLM no configurada")
                
        except ImportError:
            logger.warning("httpx no disponible, usando respuestas locales")
    
    def procesar_mensaje(
        self, 
        mensaje: str,
        user_id: int = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario usando patrón RAG
        
        Args:
            mensaje: Mensaje del usuario
            user_id: ID del usuario (para historial)
            session_id: ID de sesión
            
        Returns:
            dict con respuesta, intención detectada y contexto usado
        """
        try:
            # 1. Clasificar intención
            intencion = self._clasificar_intencion(mensaje)
            logger.debug(f"Intención detectada: {intencion}")
            
            # 2. Obtener contexto RAG
            contexto = self._obtener_contexto_rag(intencion, mensaje)
            
            # 3. Generar respuesta
            if self.llm_client and self.api_key:
                respuesta = self._consultar_llm(mensaje, contexto, intencion)
            else:
                respuesta = self._generar_respuesta_local(mensaje, contexto, intencion)
            
            # 4. Guardar en historial
            self._guardar_historial(user_id, session_id, mensaje, respuesta, intencion)
            
            return {
                'exito': True,
                'respuesta': respuesta,
                'intencion': intencion,
                'contexto_usado': self._resumir_contexto(contexto),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                'exito': False,
                'error': str(e),
                'respuesta': self._respuesta_error()
            }
    
    def _clasificar_intencion(self, mensaje: str) -> str:
        """Clasifica la intención del mensaje"""
        mensaje_lower = mensaje.lower()
        
        # Buscar palabras clave por intención
        scores = {}
        for intencion, keywords in self.INTENCIONES.items():
            if intencion == 'GENERAL':
                continue
            score = sum(1 for kw in keywords if kw in mensaje_lower)
            if score > 0:
                scores[intencion] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'GENERAL'
    
    def _obtener_contexto_rag(self, intencion: str, mensaje: str) -> Dict[str, Any]:
        """
        Obtiene contexto relevante usando DataAggregator
        
        Este es el corazón del patrón RAG: solo enviamos al LLM
        la información relevante para la pregunta específica.
        """
        try:
            from core.data_integration import data_aggregator
            
            # Obtener contexto específico según intención
            contexto = data_aggregator.obtener_contexto_para_consulta(intencion)
            
            # Enriquecer con datos de Analytics si es predicción
            if intencion == 'PREDICCION':
                contexto = self._enriquecer_con_predicciones(contexto, mensaje)
            
            # Limitar tamaño del contexto
            contexto_str = json.dumps(contexto, default=str, ensure_ascii=False)
            if len(contexto_str) > self.MAX_CONTEXT_CHARS:
                contexto = self._reducir_contexto(contexto)
            
            return contexto
            
        except Exception as e:
            logger.warning(f"Error obteniendo contexto RAG: {e}")
            return {'info': 'Contexto no disponible', 'error': str(e)}
    
    def _enriquecer_con_predicciones(self, contexto: Dict, mensaje: str) -> Dict:
        """Enriquece contexto con datos de predicción si es relevante"""
        try:
            from analytics.services import DemandForecaster, AnomalyDetector
            
            # Buscar si menciona un producto específico
            producto_id = self._extraer_producto_id(mensaje)
            
            if producto_id:
                forecaster = DemandForecaster()
                prediccion = forecaster.predecir_demanda(producto_id, dias_futuros=14)
                
                if prediccion['exito']:
                    contexto['prediccion'] = {
                        'producto_id': producto_id,
                        'total_predicho': prediccion['resumen']['total_periodo'],
                        'promedio_diario': prediccion['resumen']['promedio_diario'],
                        'confianza': prediccion['confianza'],
                        'modelo': prediccion['modelo']['tipo']
                    }
            
            # Agregar anomalías recientes
            detector = AnomalyDetector()
            anomalias = detector.detectar_anomalias_ventas(dias=7)
            
            if anomalias['exito'] and anomalias['anomalias']:
                contexto['anomalias_recientes'] = anomalias['anomalias'][:3]
            
        except Exception as e:
            logger.debug(f"No se pudo enriquecer con predicciones: {e}")
        
        return contexto
    
    def _consultar_llm(
        self, 
        mensaje: str, 
        contexto: Dict, 
        intencion: str
    ) -> str:
        """Consulta al LLM con contexto RAG"""
        try:
            # Construir prompt
            template = self.PROMPT_TEMPLATES.get(intencion, self.PROMPT_TEMPLATES['GENERAL'])
            contexto_str = self._formatear_contexto(contexto)
            
            prompt = template.format(
                contexto=contexto_str,
                pregunta=mensaje
            )
            
            # Llamar a la API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://inventory-system.local',
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 500
            }
            
            response = self.llm_client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"Error LLM API: {response.status_code}")
                return self._generar_respuesta_local(mensaje, contexto, intencion)
                
        except Exception as e:
            logger.error(f"Error consultando LLM: {e}")
            return self._generar_respuesta_local(mensaje, contexto, intencion)
    
    def _generar_respuesta_local(
        self, 
        mensaje: str, 
        contexto: Dict, 
        intencion: str
    ) -> str:
        """
        Genera respuesta local cuando LLM no está disponible
        
        Usa los datos del contexto para construir una respuesta útil.
        """
        datos = contexto.get('datos', contexto)
        
        if intencion == 'VENTAS':
            return self._respuesta_ventas(datos)
        elif intencion == 'INVENTARIO':
            return self._respuesta_inventario(datos)
        elif intencion == 'FINANZAS':
            return self._respuesta_finanzas(datos)
        elif intencion == 'PREDICCION':
            return self._respuesta_prediccion(datos, contexto)
        else:
            return self._respuesta_general(datos)
    
    def _respuesta_ventas(self, datos: Dict) -> str:
        """Genera respuesta sobre ventas"""
        try:
            ventas_recientes = datos.get('ventas_recientes', {})
            total = ventas_recientes.get('total', 0)
            cantidad = ventas_recientes.get('cantidad', 0)
            
            return f"""📊 **Resumen de Ventas**

• Total ventas recientes: **${total:,.0f}**
• Número de transacciones: **{cantidad}**
• Ticket promedio: **${total/cantidad:,.0f}** (si hay ventas)

Para más detalles, puedes consultar el módulo de Analytics o el dashboard principal."""
        except:
            return "No hay datos de ventas disponibles. Por favor, verifica que haya transacciones registradas."
    
    def _respuesta_inventario(self, datos: Dict) -> str:
        """Genera respuesta sobre inventario"""
        try:
            inventario = datos.get('inventario', datos)
            productos_bajo_stock = datos.get('alertas', {}).get('productos_bajo_stock', [])
            
            resp = "📦 **Estado del Inventario**\n\n"
            
            if productos_bajo_stock:
                resp += f"⚠️ **{len(productos_bajo_stock)} producto(s) con stock bajo:**\n"
                for p in productos_bajo_stock[:5]:
                    nombre = p.get('nombre', p.get('producto_nombre', 'Producto'))
                    stock = p.get('stock', p.get('stock_actual', 0))
                    resp += f"• {nombre}: {stock} unidades\n"
            else:
                resp += "✅ No hay productos con stock bajo actualmente.\n"
            
            return resp
        except:
            return "No se pudo obtener información del inventario."
    
    def _respuesta_finanzas(self, datos: Dict) -> str:
        """Genera respuesta sobre finanzas"""
        try:
            kpis = datos.get('kpis', {})
            
            resp = "💰 **Indicadores Financieros**\n\n"
            
            if 'ticket_promedio' in kpis:
                resp += f"• Ticket promedio: ${kpis['ticket_promedio']:,.0f}\n"
            if 'margen_bruto' in kpis:
                resp += f"• Margen bruto: {kpis['margen_bruto']:.1f}%\n"
            if 'ventas_totales' in kpis:
                resp += f"• Ventas totales: ${kpis['ventas_totales']:,.0f}\n"
            
            if not kpis:
                resp += "Los KPIs se calcularán cuando haya más datos de ventas."
            
            return resp
        except:
            return "No se pudieron obtener los indicadores financieros."
    
    def _respuesta_prediccion(self, datos: Dict, contexto: Dict) -> str:
        """Genera respuesta sobre predicciones"""
        try:
            prediccion = contexto.get('prediccion', {})
            
            if prediccion:
                confianza = prediccion.get('confianza', 0) * 100
                return f"""🔮 **Predicción de Demanda**

• Total predicho (14 días): **{prediccion.get('total_predicho', 0):.0f}** unidades
• Promedio diario: **{prediccion.get('promedio_diario', 0):.1f}** unidades
• Nivel de confianza: **{confianza:.0f}%**
• Modelo utilizado: {prediccion.get('modelo', 'N/A')}

⚠️ Recuerda que estas son estimaciones basadas en datos históricos."""
            else:
                return "Para obtener predicciones, especifica el ID del producto. Ejemplo: 'predecir demanda producto 5'"
        except:
            return "No se pudo generar la predicción. Verifica que haya suficientes datos históricos."
    
    def _respuesta_general(self, datos: Dict) -> str:
        """Respuesta general de fallback"""
        return """👋 **Asistente de Gestión**

Puedo ayudarte con:
• **Ventas**: "¿Cuánto vendimos hoy?" o "resumen de ventas"
• **Inventario**: "¿Qué productos tienen stock bajo?"
• **Finanzas**: "¿Cuál es el margen de ganancia?"
• **Predicciones**: "predecir demanda producto 5"

¿En qué puedo ayudarte?"""
    
    def _respuesta_error(self) -> str:
        """Respuesta cuando hay un error"""
        return "Lo siento, hubo un problema procesando tu consulta. Por favor, intenta de nuevo o reformula tu pregunta."
    
    def _formatear_contexto(self, contexto: Dict) -> str:
        """Formatea el contexto para incluir en el prompt"""
        try:
            # Formatear de forma legible para el LLM
            partes = []
            
            for key, value in contexto.items():
                if isinstance(value, dict):
                    partes.append(f"{key.upper()}:")
                    for k, v in value.items():
                        partes.append(f"  - {k}: {v}")
                elif isinstance(value, list):
                    partes.append(f"{key.upper()}: {len(value)} items")
                else:
                    partes.append(f"{key.upper()}: {value}")
            
            resultado = "\n".join(partes)
            
            # Limitar longitud
            if len(resultado) > self.MAX_CONTEXT_CHARS:
                resultado = resultado[:self.MAX_CONTEXT_CHARS] + "..."
            
            return resultado
            
        except Exception as e:
            return json.dumps(contexto, default=str)[:self.MAX_CONTEXT_CHARS]
    
    def _reducir_contexto(self, contexto: Dict) -> Dict:
        """Reduce el tamaño del contexto manteniendo lo esencial"""
        # Mantener solo campos principales
        reducido = {}
        
        prioridades = ['resumen', 'kpis', 'alertas', 'estadisticas']
        
        for key in prioridades:
            if key in contexto:
                reducido[key] = contexto[key]
                if len(json.dumps(reducido, default=str)) > self.MAX_CONTEXT_CHARS:
                    break
        
        return reducido if reducido else {'info': 'Contexto reducido'}
    
    def _resumir_contexto(self, contexto: Dict) -> Dict[str, Any]:
        """Resumen del contexto usado para la respuesta"""
        return {
            'campos': list(contexto.keys()),
            'tamaño_bytes': len(json.dumps(contexto, default=str))
        }
    
    def _extraer_producto_id(self, mensaje: str) -> Optional[int]:
        """Extrae ID de producto del mensaje si existe"""
        # Buscar patrones como "producto 5", "id 123", etc.
        patterns = [
            r'producto\s*(\d+)',
            r'id\s*(\d+)',
            r'#(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, mensaje.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _guardar_historial(
        self, 
        user_id: int, 
        session_id: str,
        mensaje: str, 
        respuesta: str, 
        intencion: str
    ):
        """Guarda mensaje en historial (cache)"""
        try:
            if not user_id:
                return
            
            cache_key = f"chat_history_{user_id}_{session_id or 'default'}"
            historial = cache.get(cache_key, [])
            
            historial.append({
                'timestamp': timezone.now().isoformat(),
                'mensaje': mensaje[:200],  # Limitar
                'respuesta': respuesta[:500],
                'intencion': intencion
            })
            
            # Mantener últimos N mensajes
            historial = historial[-self.MAX_HISTORY_MESSAGES:]
            
            cache.set(cache_key, historial, self.CACHE_TTL_SECONDS * 6)  # 30 min
            
        except Exception as e:
            logger.debug(f"No se pudo guardar historial: {e}")
    
    def obtener_historial(self, user_id: int, session_id: str = None) -> List[Dict]:
        """Obtiene historial de chat del usuario"""
        try:
            cache_key = f"chat_history_{user_id}_{session_id or 'default'}"
            return cache.get(cache_key, [])
        except:
            return []
    
    def limpiar_historial(self, user_id: int, session_id: str = None):
        """Limpia historial de chat"""
        try:
            cache_key = f"chat_history_{user_id}_{session_id or 'default'}"
            cache.delete(cache_key)
        except:
            pass

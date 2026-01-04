"""
Servicio de IA para análisis avanzado usando OpenRouter API.
Incluye sistema de FAILOVER automático entre modelos gratuitos.

Características:
- Cadena de failover: Si un modelo falla, prueba el siguiente automáticamente
- Detección de errores: Rate limits, tokens agotados, provider errors
- Reintentos inteligentes: Máximo N intentos con backoff exponencial
- Logging de errores para monitoreo
"""

import json
import logging
import os
import time
from typing import Any, Optional

import requests
from dotenv import load_dotenv

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(override=True)


class OpenRouterService:
    """
    Servicio de IA usando OpenRouter API con failover automático.
    
    El sistema intenta usar el modelo principal y, si falla,
    automáticamente prueba los siguientes modelos en la cadena.
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Cadena de failover ordenada por prioridad y estabilidad
    # El sistema probará cada modelo en orden si el anterior falla
    FAILOVER_CHAIN = [
        "meta-llama/llama-3.3-70b-instruct:free",     # Más estable
        "meta-llama/llama-3.2-3b-instruct:free",      # Rápido
        "mistralai/mistral-7b-instruct:free",         # Ligero
        "google/gemini-2.0-flash-exp:free",           # Google
        "qwen/qwen2.5-vl-7b-instruct:free",           # Alternativo
        "nousresearch/hermes-3-llama-3.1-405b:free",  # Potente
    ]
    
    # Errores que activan failover (no reintenar con mismo modelo)
    FAILOVER_ERRORS = [
        "rate limit",
        "rate_limit",
        "quota exceeded",
        "no endpoints",
        "provider returned error",
        "model not available",
        "capacity",
        "overloaded",
        "503",
        "429",
        "402",  # Payment required
    ]
    
    # Errores que requieren reintento (mismo modelo)
    RETRY_ERRORS = [
        "timeout",
        "connection",
        "temporary",
        "502",
        "504",
    ]
    
    # Configuración de reintentos
    MAX_RETRIES = 2  # Reintentos por modelo antes de failover
    RETRY_DELAY = 1  # Segundos entre reintentos
    REQUEST_TIMEOUT = 60  # Timeout por request

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY no está configurada. "
                "Por favor, configura tu API key en el archivo .env"
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Sistema de Inventario",
        }
        # Tracking de modelos fallidos para evitar reintentos innecesarios
        self._failed_models: set = set()
        self._last_successful_model: Optional[str] = None

    def _should_failover(self, error_message: str) -> bool:
        """Determina si el error requiere cambiar a otro modelo."""
        error_lower = error_message.lower()
        return any(err in error_lower for err in self.FAILOVER_ERRORS)
    
    def _should_retry(self, error_message: str) -> bool:
        """Determina si el error es temporal y se puede reintentar."""
        error_lower = error_message.lower()
        return any(err in error_lower for err in self.RETRY_ERRORS)

    def _get_next_model(self, current_model: str) -> Optional[str]:
        """Obtiene el siguiente modelo en la cadena de failover."""
        try:
            current_idx = self.FAILOVER_CHAIN.index(current_model)
            for next_model in self.FAILOVER_CHAIN[current_idx + 1:]:
                if next_model not in self._failed_models:
                    return next_model
        except ValueError:
            pass
        
        # Si el modelo actual no está en la cadena, buscar cualquiera disponible
        for model in self.FAILOVER_CHAIN:
            if model not in self._failed_models:
                return model
        
        return None

    def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Realiza una petición a la API de OpenRouter."""
        response = requests.post(
            f"{self.BASE_URL}{endpoint}",
            headers=self.headers,
            json=payload,
            timeout=self.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def _extract_error_message(self, exception: Exception) -> str:
        """Extrae mensaje de error legible de una excepción."""
        if hasattr(exception, 'response'):
            try:
                error_json = exception.response.json()
                return error_json.get("error", {}).get("message", str(exception))
            except:
                pass
        return str(exception)

    def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Envía una consulta al modelo de chat con failover automático.
        
        Args:
            messages: Lista de mensajes
            model: Modelo inicial (opcional)
            temperature: Creatividad (0.0 - 1.0)
            max_tokens: Máximo de tokens en respuesta
            
        Returns:
            Texto de respuesta del modelo
            
        Raises:
            Exception: Si todos los modelos fallan
        """
        # Usar último modelo exitoso si está disponible
        if model is None:
            model = self._last_successful_model or self.FAILOVER_CHAIN[0]
        
        current_model = model
        errors_log = []
        
        while current_model:
            retry_count = 0
            
            while retry_count <= self.MAX_RETRIES:
                try:
                    payload = {
                        "model": current_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    
                    result = self._make_request("/chat/completions", payload)
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        # Éxito - guardar modelo para futuras consultas
                        self._last_successful_model = current_model
                        # Limpiar modelos fallidos (pueden haberse recuperado)
                        self._failed_models.clear()
                        
                        logger.info(f"OpenRouter: Respuesta exitosa de {current_model}")
                        return result["choices"][0]["message"]["content"]
                    
                    raise Exception("Respuesta vacía del modelo")
                    
                except requests.exceptions.Timeout:
                    error_msg = f"Timeout en {current_model}"
                    errors_log.append(error_msg)
                    logger.warning(error_msg)
                    retry_count += 1
                    if retry_count <= self.MAX_RETRIES:
                        time.sleep(self.RETRY_DELAY * retry_count)
                    
                except requests.exceptions.HTTPError as e:
                    error_msg = self._extract_error_message(e)
                    errors_log.append(f"{current_model}: {error_msg}")
                    logger.warning(f"OpenRouter HTTPError: {error_msg}")
                    
                    if self._should_failover(error_msg):
                        # Marcar modelo como fallido y cambiar
                        self._failed_models.add(current_model)
                        break  # Salir del retry loop, ir a failover
                    elif self._should_retry(error_msg):
                        retry_count += 1
                        if retry_count <= self.MAX_RETRIES:
                            time.sleep(self.RETRY_DELAY * retry_count)
                    else:
                        # Error desconocido, intentar failover
                        self._failed_models.add(current_model)
                        break
                        
                except requests.exceptions.RequestException as e:
                    error_msg = str(e)
                    errors_log.append(f"{current_model}: {error_msg}")
                    logger.warning(f"OpenRouter RequestException: {error_msg}")
                    retry_count += 1
                    if retry_count <= self.MAX_RETRIES:
                        time.sleep(self.RETRY_DELAY * retry_count)
                        
                except Exception as e:
                    error_msg = str(e)
                    errors_log.append(f"{current_model}: {error_msg}")
                    logger.warning(f"OpenRouter Exception: {error_msg}")
                    self._failed_models.add(current_model)
                    break
            
            # Intentar siguiente modelo en cadena
            next_model = self._get_next_model(current_model)
            if next_model:
                logger.info(f"OpenRouter: Failover de {current_model} a {next_model}")
                current_model = next_model
            else:
                current_model = None
        
        # Todos los modelos fallaron
        all_errors = "; ".join(errors_log[-5:])  # Últimos 5 errores
        raise Exception(
            f"Todos los modelos IA fallaron. Últimos errores: {all_errors}"
        )

    def generate_summary(self, data: dict, context: str = "") -> str:
        """Genera un resumen ejecutivo de datos con failover automático."""
        prompt = f"""Eres un analista de negocios experto. Analiza los siguientes datos y genera un resumen ejecutivo breve y profesional en español.

Contexto: {context}

Datos para analizar:
{json.dumps(data, indent=2, ensure_ascii=False, default=str)}

Genera un resumen que incluya:
1. Hallazgos principales (máximo 3 puntos)
2. Tendencias importantes
3. Recomendación de acción (si aplica)

Mantén el resumen conciso (máximo 150 palabras)."""

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature=0.5)

    def natural_language_to_insight(self, question: str, available_data: dict) -> str:
        """Responde preguntas en lenguaje natural con failover automático."""
        prompt = f"""Eres un asistente de análisis de inventario. Responde la siguiente pregunta basándote únicamente en los datos proporcionados.

Pregunta del usuario: {question}

Datos disponibles:
{json.dumps(available_data, indent=2, ensure_ascii=False, default=str)}

Instrucciones:
- Responde de forma clara y concisa en español
- Si los datos no son suficientes para responder, indícalo
- Incluye números específicos cuando sea relevante
- No inventes datos que no estén en la información proporcionada"""

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature=0.3)

    def get_status(self) -> dict:
        """Retorna el estado actual del servicio para monitoreo."""
        return {
            "last_successful_model": self._last_successful_model,
            "failed_models": list(self._failed_models),
            "available_models": [m for m in self.FAILOVER_CHAIN if m not in self._failed_models],
        }


# Instancia singleton para mantener estado de failover
_service_instance: Optional[OpenRouterService] = None


def get_ai_service() -> OpenRouterService:
    """
    Obtiene instancia singleton del servicio de IA.
    Usa singleton para mantener el estado de failover entre requests.
    """
    global _service_instance
    if _service_instance is None:
        load_dotenv(override=True)
        _service_instance = OpenRouterService()
    return _service_instance


def reset_ai_service():
    """Resetea el servicio (útil para testing o reinicio manual)."""
    global _service_instance
    _service_instance = None

"""
Servicio de IA para análisis avanzado usando DeepSeek API.
Proporciona conexión con los modelos deepseek-chat y deepseek-reasoner.
"""

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

# Cargar variables de entorno (override=True para forzar recarga)
load_dotenv(override=True)


class DeepSeekService:
    """Servicio de IA usando DeepSeek API"""

    BASE_URL = "https://api.deepseek.com"
    
    # Modelos disponibles
    MODEL_CHAT = "deepseek-chat"  # Para generación de texto general
    MODEL_REASONER = "deepseek-reasoner"  # Para análisis lógico y razonamiento

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY no está configurada. "
                "Por favor, configura tu API key en el archivo .env"
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Realiza una petición a la API de DeepSeek."""
        try:
            response = requests.post(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("Timeout al conectar con DeepSeek API")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con DeepSeek API: {str(e)}")

    def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Envía una consulta al modelo de chat.
        
        Args:
            messages: Lista de mensajes [{"role": "user/assistant/system", "content": "..."}]
            model: Modelo a usar (deepseek-chat o deepseek-reasoner)
            temperature: Creatividad (0.0 - 1.0)
            max_tokens: Máximo de tokens en respuesta
            
        Returns:
            Texto de respuesta del modelo
        """
        if model is None:
            model = self.MODEL_CHAT

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        result = self._make_request("/chat/completions", payload)
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        
        raise Exception("Respuesta inesperada de DeepSeek API")

    def reason(self, messages: list[dict], max_tokens: int = 4096) -> str:
        """
        Usa deepseek-reasoner para análisis lógico y razonamiento complejo.
        Ideal para generar consultas SQL, análisis de datos, etc.
        
        Args:
            messages: Lista de mensajes
            max_tokens: Máximo de tokens (reasoner puede generar más)
            
        Returns:
            Texto de respuesta del modelo
        """
        return self.chat(
            messages=messages,
            model=self.MODEL_REASONER,
            temperature=0.0,  # Más determinístico para razonamiento
            max_tokens=max_tokens,
        )

    def generate_summary(self, data: dict, context: str = "") -> str:
        """
        Genera un resumen ejecutivo de datos.
        
        Args:
            data: Diccionario con datos a analizar
            context: Contexto adicional (fecha, período, etc.)
            
        Returns:
            Resumen en español
        """
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
        """
        Responde preguntas en lenguaje natural sobre los datos disponibles.
        
        Args:
            question: Pregunta del usuario
            available_data: Datos disponibles para responder
            
        Returns:
            Respuesta basada en los datos
        """
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


# Singleton para reutilizar la conexión
_deepseek_instance = None


def get_deepseek_service() -> DeepSeekService:
    """Obtiene una nueva instancia del servicio DeepSeek."""
    # Recargar variables de entorno para asegurar que tenemos la última versión
    load_dotenv(override=True)
    return DeepSeekService()

"""
Módulo IA - Inteligencia Artificial con RAG

Componentes:
- IntelligentChatbot: Chatbot con contexto RAG via DataAggregator
- RecommendationEngine: Motor de recomendaciones personalizadas

Patrón RAG (Retrieval-Augmented Generation):
- Usa DataAggregator de core para obtener contexto específico
- Envía solo información relevante al LLM
- Optimiza costos y mejora precisión de respuestas

Estrategia LLM Híbrida:
- DeepSeek: Procesos automatizados, análisis de datos
- ChatGPT: Interacción con usuario, respuestas conversacionales
- Claude: Contabilidad y análisis complejo (futuro)
"""

default_app_config = 'ia.apps.IAConfig'

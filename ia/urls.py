"""
URLs del módulo IA
"""

from django.urls import path
from . import views

app_name = 'ia'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Chatbot con RAG
    path('chat/', views.chat, name='chat'),
    path('historial/', views.historial_chat, name='historial'),
    path('limpiar-historial/', views.limpiar_historial, name='limpiar_historial'),
    
    # Recomendaciones
    path('recomendaciones/', views.obtener_recomendaciones, name='recomendaciones'),
    path('relacionados/', views.productos_relacionados, name='relacionados'),
]

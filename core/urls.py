"""
Core URLs - Endpoints de API para el módulo Core
"""

from django.urls import path
from . import views
from . import views_dashboard

app_name = 'core'

urlpatterns = [
    # Health Check
    path('health/', views.health_check, name='health_check'),
    
    # Eventos
    path('eventos/', views.list_event_types, name='event_types'),
    path('test-evento/', views.publish_test_event, name='test_event'),
    
    # Dashboard consolidado (Core)
    path('dashboard/', views.get_dashboard, name='get_dashboard'),
    
    # Contexto para IA (RAG)
    path('contexto-ia/', views.get_context_for_ai, name='context_for_ai'),
    
    # Dashboard Unificado (Fase 5 - Integra todos los módulos)
    path('dashboard-unificado/', views_dashboard.dashboard_unificado, name='dashboard_unificado'),
    path('resumen/', views_dashboard.resumen_ejecutivo, name='resumen_ejecutivo'),
    path('health-global/', views_dashboard.health_check_global, name='health_global'),
]


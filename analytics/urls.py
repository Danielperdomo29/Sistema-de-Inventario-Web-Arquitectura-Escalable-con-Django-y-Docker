"""
URLs del módulo Analytics
"""

from django.urls import path
from . import views

app_name = 'analytics_ml'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Predicción de demanda
    path('prediccion/', views.predecir_demanda, name='prediccion'),
    path('entrenar/', views.entrenar_modelo, name='entrenar'),
    
    # Optimización de inventario
    path('optimizacion/', views.optimizar_inventario, name='optimizacion'),
    path('abc/', views.clasificacion_abc, name='abc'),
    
    # Detección de anomalías
    path('anomalias/', views.detectar_anomalias, name='anomalias'),
    path('sin-movimiento/', views.productos_sin_movimiento, name='sin_movimiento'),
]

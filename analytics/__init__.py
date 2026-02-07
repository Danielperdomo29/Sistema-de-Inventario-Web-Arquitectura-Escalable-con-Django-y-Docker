"""
Módulo Analytics - Predicción y Optimización de Inventario

Componentes:
- ETLProcessor: Limpieza y preparación de datos
- DemandForecaster: Predicción de demanda con sklearn
- InventoryOptimizer: Optimización de niveles de stock
- AnomalyDetector: Detección de anomalías en ventas/inventario

Integración:
- Usa DataAggregator de core para obtener datos
- Publica eventos al EventBus cuando detecta anomalías
"""

default_app_config = 'analytics.apps.AnalyticsConfig'

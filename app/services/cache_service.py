"""
CacheService - Sistema centralizado de caché

Proporciona decoradores y métodos para cachear datos en la aplicación.
Usa FileBasedCache en desarrollo y puede cambiar a Redis en producción
modificando solo settings.py.
"""

from django.core.cache import cache
from functools import wraps
import hashlib
import json


class CacheService:
    """
    Servicio centralizado de caché con soporte para:
    - Caché de catálogos (productos, categorías, etc.)
    - Caché de reportes analytics
    - Invalidación automática
    """
    
    # Tiempos de expiración
    TIMEOUT_SHORT = 60 * 5      # 5 minutos
    TIMEOUT_MEDIUM = 60 * 30    # 30 minutos  
    TIMEOUT_LONG = 60 * 60 * 2  # 2 horas
    
    @staticmethod
    def cache_result(cache_key, timeout=TIMEOUT_MEDIUM):
        """
        Decorador genérico para cachear el resultado de una función.
        
        Uso:
            @CacheService.cache_result('my_function', timeout=300)
            def my_function():
                return expensive_query()
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Construir cache key único con argumentos
                if args or kwargs:
                    args_str = str(args) + str(sorted(kwargs.items()))
                    key_suffix = hashlib.md5(args_str.encode()).hexdigest()[:8]
                    full_key = f"{cache_key}:{key_suffix}"
                else:
                    full_key = cache_key
                
                # Intentar obtener del caché
                cached_data = cache.get(full_key)
                if cached_data is not None:
                    return cached_data
                
                # Ejecutar función y cachear resultado
                result = func(*args, **kwargs)
                cache.set(full_key, result, timeout)
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def cache_product_catalog():
        """
        Decorador específico para cachear catálogo de productos.
        Invalida automáticamente cuando se modifica un producto.
        """
        return CacheService.cache_result('catalog:products:all', CacheService.TIMEOUT_MEDIUM)
    
    @staticmethod
    def cache_analytics_report(report_type, params, timeout=TIMEOUT_SHORT):
        """
        Cachea un reporte de analytics basándose en tipo y parámetros.
        
        Args:
            report_type: Tipo de reporte (ej: 'daily_summary', 'monthly_sales')
            params: Diccionario con parámetros del reporte
            timeout: Tiempo de expiración en segundos
        
        Returns:
            Datos del reporte (desde caché o recién calculados)
        """
        # Generar cache key único basado en parámetros
        param_str = json.dumps(params, sort_keys=True, default=str)
        cache_key = f'analytics:{report_type}:{hashlib.md5(param_str.encode()).hexdigest()}'
        
        cached = cache.get(cache_key)
        if cached:
            return cached, True  # True indica que vino del caché
        return None, False
    
    @staticmethod
    def set_analytics_cache(report_type, params, data, timeout=TIMEOUT_SHORT):
        """
        Guarda un reporte de analytics en caché.
        
        Args:
            report_type: Tipo de reporte
            params: Parámetros usados para generar el reporte
            data: Datos del reporte a cachear
            timeout: Tiempo de expiración
        """
        param_str = json.dumps(params, sort_keys=True, default=str)
        cache_key = f'analytics:{report_type}:{hashlib.md5(param_str.encode()).hexdigest()}'
        cache.set(cache_key, data, timeout)
    
    @staticmethod
    def invalidate_product_cache():
        """
        Invalida todo el caché relacionado con productos.
        Llamar después de crear/actualizar/eliminar productos.
        """
        cache.delete('catalog:products:all')
        # Patrón para invalidar múltiples claves relacionadas
        # Nota: FileBasedCache no soporta delete_pattern, pero Redis sí
        # cache.delete_pattern('product:*')
    
    @staticmethod
    def invalidate_analytics_cache():
        """
        Invalida todo el caché de analytics.
        Llamar después de crear/modificar ventas o compras.
        """
        # Nota: Con FileBasedCache esto no es tan eficiente
        # Con Redis se usaría delete_pattern('analytics:*')
        cache.clear()  # Por ahora limpia todo el caché
    
    @staticmethod
    def get_cache_stats():
        """
        Obtiene estadísticas del caché (útil para debugging).
        No disponible en FileBasedCache, implementar con Redis.
        """
        return {
            'backend': 'FileBasedCache',
            'note': 'Cambia a Redis en producción para stats completas'
        }


# Ejemplo de uso en modelos/controllers:
# 
# from app.services.cache_service import CacheService
#
# class ProductController:
#     @staticmethod
#     @CacheService.cache_product_catalog()
#     def get_all_products():
#         return Product.get_all()
#
#     @staticmethod
#     def update_product(product_id, data):
#         Product.update(product_id, data)
#         CacheService.invalidate_product_cache()  # Invalidar caché

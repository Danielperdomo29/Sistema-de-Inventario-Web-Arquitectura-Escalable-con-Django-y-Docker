"""
Recommendation Engine - Motor de recomendaciones inteligentes

Genera recomendaciones personalizadas basándose en:
- Historial de ventas
- Patrones de compra
- Productos relacionados
- Clasificación ABC
- Predicciones de demanda
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.utils import timezone
from django.db.models import Sum, Count, F, Q

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Motor de recomendaciones para el sistema de inventario
    
    Tipos de recomendaciones:
    - Productos frecuentemente comprados juntos
    - Productos a reabastecer
    - Optimizaciones de inventario
    - Ofertas y promociones sugeridas
    """
    
    # Configuración
    MIN_COMPRAS_JUNTAS = 3  # Mínimo de co-ocurrencias
    DIAS_ANALISIS = 90
    MAX_RECOMENDACIONES = 10
    
    def __init__(self):
        pass
    
    def obtener_recomendaciones_completas(
        self, 
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Genera todas las recomendaciones disponibles
        
        Args:
            user_id: ID del usuario (para personalización)
            
        Returns:
            dict con todas las recomendaciones categorizadas
        """
        recomendaciones = {
            'timestamp': timezone.now().isoformat(),
            'resumen': {},
            'categorias': {}
        }
        
        try:
            # 1. Productos a reabastecer
            reabastecimiento = self.recomendar_reabastecimiento()
            recomendaciones['categorias']['reabastecimiento'] = reabastecimiento
            
            # 2. Productos sin rotación
            sin_rotacion = self.recomendar_liquidacion()
            recomendaciones['categorias']['liquidacion'] = sin_rotacion
            
            # 3. Productos estrella
            estrellas = self.identificar_productos_estrella()
            recomendaciones['categorias']['productos_estrella'] = estrellas
            
            # 4. Optimización de precios
            precios = self.sugerir_ajustes_precio()
            recomendaciones['categorias']['precios'] = precios
            
            # Resumen
            recomendaciones['resumen'] = {
                'productos_reabastecer': len(reabastecimiento.get('productos', [])),
                'productos_liquidar': len(sin_rotacion.get('productos', [])),
                'productos_estrella': len(estrellas.get('productos', [])),
                'ajustes_precio': len(precios.get('sugerencias', []))
            }
            
            recomendaciones['exito'] = True
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            recomendaciones['exito'] = False
            recomendaciones['error'] = str(e)
        
        return recomendaciones
    
    def recomendar_reabastecimiento(self) -> Dict[str, Any]:
        """
        Recomienda productos que necesitan reabastecimiento
        
        Criterios:
        - Stock bajo o próximo a agotarse
        - Demanda predicha alta
        - Lead time del proveedor
        """
        try:
            from app.models import Product
            from analytics.services import DemandForecaster, InventoryOptimizer
            
            productos_bajo_stock = Product.objects.filter(
                Q(stock_actual__lte=F('stock_minimo')) | Q(stock_actual__lte=5)
            ).values('id', 'nombre', 'codigo', 'stock_actual', 'stock_minimo')[:20]
            
            recomendaciones = []
            optimizer = InventoryOptimizer()
            
            for prod in productos_bajo_stock:
                try:
                    opt = optimizer.optimizar_producto(prod['id'])
                    
                    if opt['exito']:
                        cantidad_pedir = opt['optimizacion']['eoq']
                        urgencia = 'ALTA' if prod['stock_actual'] == 0 else 'MEDIA'
                    else:
                        cantidad_pedir = (prod['stock_minimo'] or 10) * 2
                        urgencia = 'MEDIA'
                    
                    recomendaciones.append({
                        'producto_id': prod['id'],
                        'nombre': prod['nombre'],
                        'codigo': prod['codigo'],
                        'stock_actual': prod['stock_actual'],
                        'stock_minimo': prod['stock_minimo'],
                        'cantidad_sugerida': round(cantidad_pedir),
                        'urgencia': urgencia,
                        'razon': 'Stock bajo o agotado'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error optimizando producto {prod['id']}: {e}")
            
            # Ordenar por urgencia
            recomendaciones.sort(key=lambda x: 0 if x['urgencia'] == 'ALTA' else 1)
            
            return {
                'productos': recomendaciones[:self.MAX_RECOMENDACIONES],
                'total': len(recomendaciones),
                'accion': 'Generar orden de compra'
            }
            
        except Exception as e:
            logger.error(f"Error en recomendaciones de reabastecimiento: {e}")
            return {'productos': [], 'error': str(e)}
    
    def recomendar_liquidacion(self) -> Dict[str, Any]:
        """
        Recomienda productos para liquidación o promoción
        
        Criterios:
        - Sin ventas en X días
        - Stock alto sin rotación
        - Productos obsoletos
        """
        try:
            from app.models import Product, SaleDetail
            
            fecha_corte = date.today() - timedelta(days=self.DIAS_ANALISIS)
            
            # Productos con ventas recientes
            productos_con_ventas = SaleDetail.objects.filter(
                venta__fecha__gte=fecha_corte
            ).values_list('producto_id', flat=True).distinct()
            
            # Productos sin ventas con stock
            sin_rotacion = Product.objects.filter(
                stock_actual__gt=10  # Al menos 10 unidades
            ).exclude(
                id__in=productos_con_ventas
            ).values(
                'id', 'nombre', 'codigo', 'stock_actual', 'precio_compra', 'precio_venta'
            )[:20]
            
            recomendaciones = []
            
            for prod in sin_rotacion:
                costo_almacen = float(prod['precio_compra'] or 0) * prod['stock_actual']
                descuento_sugerido = 15 if costo_almacen < 500000 else 25
                
                recomendaciones.append({
                    'producto_id': prod['id'],
                    'nombre': prod['nombre'],
                    'codigo': prod['codigo'],
                    'stock': prod['stock_actual'],
                    'valor_inventario': round(costo_almacen, 2),
                    'dias_sin_venta': self.DIAS_ANALISIS,
                    'descuento_sugerido': f'{descuento_sugerido}%',
                    'razon': 'Sin ventas en 90+ dias'
                })
            
            return {
                'productos': recomendaciones[:self.MAX_RECOMENDACIONES],
                'total': len(recomendaciones),
                'accion': 'Considerar promoción o liquidación'
            }
            
        except Exception as e:
            logger.error(f"Error en recomendaciones de liquidación: {e}")
            return {'productos': [], 'error': str(e)}
    
    def identificar_productos_estrella(self) -> Dict[str, Any]:
        """
        Identifica productos más rentables (estrella)
        
        Criterios:
        - Alto volumen de ventas
        - Buen margen
        - Demanda constante
        """
        try:
            from app.models import SaleDetail
            
            fecha_inicio = date.today() - timedelta(days=30)
            
            # Top productos por valor vendido
            top_productos = SaleDetail.objects.filter(
                venta__fecha__gte=fecha_inicio
            ).values(
                'producto_id', 'producto__nombre'
            ).annotate(
                cantidad_vendida=Sum('cantidad'),
                valor_total=Sum(F('cantidad') * F('precio_unitario')),
                transacciones=Count('id')
            ).order_by('-valor_total')[:10]
            
            productos_estrella = []
            
            for prod in top_productos:
                ticket_promedio = float(prod['valor_total']) / prod['transacciones'] if prod['transacciones'] > 0 else 0
                
                productos_estrella.append({
                    'producto_id': prod['producto_id'],
                    'nombre': prod['producto__nombre'],
                    'cantidad_vendida': prod['cantidad_vendida'],
                    'valor_ventas': round(float(prod['valor_total']), 2),
                    'transacciones': prod['transacciones'],
                    'ticket_promedio': round(ticket_promedio, 2),
                    'clasificacion': 'ESTRELLA'
                })
            
            return {
                'productos': productos_estrella,
                'periodo': '30 días',
                'accion': 'Mantener stock adecuado, promocionar'
            }
            
        except Exception as e:
            logger.error(f"Error identificando productos estrella: {e}")
            return {'productos': [], 'error': str(e)}
    
    def sugerir_ajustes_precio(self) -> Dict[str, Any]:
        """
        Sugiere ajustes de precio basados en análisis
        
        Criterios:
        - Margen muy bajo o muy alto
        - Competitividad estimada
        - Elasticidad observada
        """
        try:
            from app.models import Product, SaleDetail
            
            fecha_inicio = date.today() - timedelta(days=30)
            
            # Productos vendidos con información de margen
            productos_analizados = SaleDetail.objects.filter(
                sale__fecha__gte=fecha_inicio
            ).values(
                'product_id', 'product__nombre', 
                'product__precio_compra', 'product__precio_venta'
            ).annotate(
                cantidad_vendida=Sum('cantidad')
            )[:30]
            
            sugerencias = []
            
            for prod in productos_analizados:
                precio_compra = float(prod['product__precio_compra'] or 0)
                precio_venta = float(prod['product__precio_venta'] or 0)
                
                if precio_compra <= 0 or precio_venta <= 0:
                    continue
                
                margen = ((precio_venta - precio_compra) / precio_compra) * 100
                
                # Analizar margen
                if margen < 15:
                    sugerencias.append({
                        'producto_id': prod['product_id'],
                        'nombre': prod['product__nombre'],
                        'precio_actual': precio_venta,
                        'margen_actual': f'{margen:.1f}%',
                        'sugerencia': 'Considerar aumento de precio',
                        'precio_sugerido': round(precio_compra * 1.25, 2),  # 25% margen
                        'razon': 'Margen bajo (<15%)'
                    })
                elif margen > 100:
                    cantidad = prod['cantidad_vendida']
                    if cantidad < 5:  # Baja rotación con margen alto
                        sugerencias.append({
                            'producto_id': prod['product_id'],
                            'nombre': prod['product__nombre'],
                            'precio_actual': precio_venta,
                            'margen_actual': f'{margen:.1f}%',
                            'sugerencia': 'Considerar reducción para aumentar rotación',
                            'precio_sugerido': round(precio_compra * 1.5, 2),  # 50% margen
                            'razon': 'Margen muy alto con baja rotación'
                        })
            
            return {
                'sugerencias': sugerencias[:self.MAX_RECOMENDACIONES],
                'total_analizados': len(productos_analizados),
                'accion': 'Revisar precios sugeridos'
            }
            
        except Exception as e:
            logger.error(f"Error analizando precios: {e}")
            return {'sugerencias': [], 'error': str(e)}
    
    def obtener_productos_relacionados(
        self, 
        producto_id: int,
        limite: int = 5
    ) -> Dict[str, Any]:
        """
        Encuentra productos frecuentemente comprados junto con otro
        
        Útil para sugerencias de cross-selling.
        """
        try:
            from app.models import SaleDetail
            
            # Obtener ventas que incluyen el producto
            ventas_con_producto = SaleDetail.objects.filter(
                producto_id=producto_id
            ).values_list('venta_id', flat=True)
            
            # Encontrar otros productos en esas ventas
            productos_relacionados = SaleDetail.objects.filter(
                venta_id__in=ventas_con_producto
            ).exclude(
                producto_id=producto_id
            ).values(
                'producto_id', 'producto__nombre'
            ).annotate(
                frecuencia=Count('id')
            ).filter(
                frecuencia__gte=self.MIN_COMPRAS_JUNTAS
            ).order_by('-frecuencia')[:limite]
            
            return {
                'producto_id': producto_id,
                'relacionados': [
                    {
                        'producto_id': p['producto_id'],
                        'nombre': p['producto__nombre'],
                        'frecuencia': p['frecuencia']
                    }
                    for p in productos_relacionados
                ],
                'sugerencia': 'Considerar para promociones cruzadas'
            }
            
        except Exception as e:
            logger.error(f"Error buscando productos relacionados: {e}")
            return {'producto_id': producto_id, 'relacionados': [], 'error': str(e)}

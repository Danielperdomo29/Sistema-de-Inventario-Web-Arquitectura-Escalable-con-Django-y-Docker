"""
Inventory Optimizer - Optimización de niveles de stock

Funcionalidades:
- Calcular punto de reorden óptimo
- Calcular stock de seguridad
- Recomendar cantidad económica de pedido (EOQ)
- Clasificación ABC de productos
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
import math

from django.utils import timezone
from django.db.models import Sum, Avg, Count, F

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """
    Optimizador de inventario
    
    Calcula niveles óptimos de stock basado en:
    - Demanda predicha (DemandForecaster)
    - Costos de almacenamiento
    - Lead time de proveedores
    - Nivel de servicio deseado
    """
    
    # Configuración por defecto
    DEFAULT_NIVEL_SERVICIO = 0.95  # 95%
    DEFAULT_LEAD_TIME_DIAS = 7  # Días de entrega proveedor
    DEFAULT_COSTO_ALMACEN_ANUAL = 0.20  # 20% del costo del producto
    DEFAULT_COSTO_PEDIDO = 50000  # COP por orden
    
    # Factores Z para nivel de servicio
    Z_FACTORS = {
        0.90: 1.28,
        0.95: 1.65,
        0.99: 2.33
    }
    
    def __init__(self):
        from .demand_forecasting import DemandForecaster
        from .etl_processor import ETLProcessor
        
        self.forecaster = DemandForecaster()
        self.etl = ETLProcessor()
    
    def optimizar_producto(
        self, 
        producto_id: int,
        nivel_servicio: float = None,
        lead_time_dias: int = None,
        costo_pedido: float = None
    ) -> Dict[str, Any]:
        """
        Calcula parámetros óptimos de inventario para un producto
        
        Args:
            producto_id: ID del producto
            nivel_servicio: Probabilidad de no tener stockout (0.90-0.99)
            lead_time_dias: Días de entrega del proveedor
            costo_pedido: Costo por hacer un pedido
            
        Returns:
            dict con punto de reorden, EOQ, stock seguridad
        """
        nivel_servicio = nivel_servicio or self.DEFAULT_NIVEL_SERVICIO
        lead_time_dias = lead_time_dias or self.DEFAULT_LEAD_TIME_DIAS
        costo_pedido = costo_pedido or self.DEFAULT_COSTO_PEDIDO
        
        try:
            # Obtener datos del producto
            from app.models import Product
            
            producto = Product.objects.get(id=producto_id)
            
            # Obtener predicción de demanda
            prediccion = self.forecaster.predecir_demanda(producto_id, dias_futuros=30)
            
            if not prediccion['exito']:
                return {
                    'exito': False,
                    'mensaje': 'No se pudo predecir demanda',
                    'producto_id': producto_id
                }
            
            demanda_diaria = prediccion['resumen']['promedio_diario']
            confianza = prediccion['confianza']
            intervalo_error = prediccion['intervalo_error']['valor']
            
            if demanda_diaria <= 0:
                return {
                    'exito': False,
                    'mensaje': 'Demanda predicha es cero o negativa',
                    'producto_id': producto_id
                }
            
            # Calcular demanda anual
            demanda_anual = demanda_diaria * 365
            
            # Costo del producto
            costo_unitario = float(producto.precio_compra or producto.precio_venta or 0)
            if costo_unitario <= 0:
                costo_unitario = 1  # Evitar división por cero
            
            # Costo de almacenamiento por unidad
            costo_almacen = costo_unitario * self.DEFAULT_COSTO_ALMACEN_ANUAL
            
            # Calcular EOQ (Cantidad Económica de Pedido)
            eoq = self._calcular_eoq(
                demanda_anual, costo_pedido, costo_almacen
            )
            
            # Factor Z para nivel de servicio
            z = self._get_z_factor(nivel_servicio)
            
            # Stock de seguridad
            stock_seguridad = self._calcular_stock_seguridad(
                demanda_diaria, intervalo_error, lead_time_dias, z
            )
            
            # Punto de reorden
            punto_reorden = self._calcular_punto_reorden(
                demanda_diaria, lead_time_dias, stock_seguridad
            )
            
            # Comparar con stock actual
            stock_actual = producto.stock_actual or 0
            stock_minimo_actual = producto.stock_minimo or 0
            
            # Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(
                stock_actual, punto_reorden, eoq, stock_minimo_actual
            )
            
            return {
                'exito': True,
                'producto_id': producto_id,
                'producto_nombre': producto.nombre,
                'stock_actual': stock_actual,
                
                'optimizacion': {
                    'punto_reorden': round(punto_reorden),
                    'stock_seguridad': round(stock_seguridad),
                    'eoq': round(eoq),
                    'demanda_diaria': round(demanda_diaria, 1)
                },
                
                'actual_vs_optimo': {
                    'stock_minimo_actual': stock_minimo_actual,
                    'stock_minimo_recomendado': round(punto_reorden),
                    'diferencia': round(punto_reorden - stock_minimo_actual)
                },
                
                'parametros': {
                    'nivel_servicio': nivel_servicio,
                    'lead_time_dias': lead_time_dias,
                    'costo_pedido': costo_pedido,
                    'costo_almacen_anual': self.DEFAULT_COSTO_ALMACEN_ANUAL
                },
                
                'confianza': confianza,
                'recomendaciones': recomendaciones,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizando producto {producto_id}: {e}")
            return {
                'exito': False,
                'mensaje': str(e),
                'producto_id': producto_id
            }
    
    def clasificacion_abc(self, top_n: int = 100) -> Dict[str, Any]:
        """
        Clasifica productos según análisis ABC
        
        - A: 20% productos que representan 80% ventas (críticos)
        - B: 30% siguiente (importante)
        - C: 50% restante (bajo impacto)
        """
        try:
            from app.models import SaleDetail
            from datetime import timedelta
            
            # Ventas de últimos 90 días
            fecha_inicio = date.today() - timedelta(days=90)
            
            ventas = SaleDetail.objects.filter(
                venta__fecha__gte=fecha_inicio
            ).values('producto_id', 'producto__nombre').annotate(
                cantidad_total=Sum('cantidad'),
                valor_total=Sum(F('cantidad') * F('precio_unitario'))
            ).order_by('-valor_total')[:top_n]
            
            if not ventas:
                return {'exito': False, 'mensaje': 'Sin datos de ventas'}
            
            # Calcular totales
            valor_total_general = sum(v['valor_total'] or 0 for v in ventas)
            
            if valor_total_general <= 0:
                return {'exito': False, 'mensaje': 'Valor total es cero'}
            
            # Clasificar
            clasificacion = {'A': [], 'B': [], 'C': []}
            acumulado = 0
            
            for v in ventas:
                valor = float(v['valor_total'] or 0)
                porcentaje = valor / valor_total_general * 100
                acumulado += porcentaje
                
                item = {
                    'producto_id': v['producto_id'],
                    'nombre': v['producto__nombre'],
                    'cantidad_vendida': v['cantidad_total'],
                    'valor_ventas': round(valor, 2),
                    'porcentaje': round(porcentaje, 2),
                    'acumulado': round(acumulado, 2)
                }
                
                if acumulado <= 80:
                    item['clase'] = 'A'
                    clasificacion['A'].append(item)
                elif acumulado <= 95:
                    item['clase'] = 'B'
                    clasificacion['B'].append(item)
                else:
                    item['clase'] = 'C'
                    clasificacion['C'].append(item)
            
            return {
                'exito': True,
                'clasificacion': clasificacion,
                'resumen': {
                    'total_productos': len(ventas),
                    'productos_A': len(clasificacion['A']),
                    'productos_B': len(clasificacion['B']),
                    'productos_C': len(clasificacion['C']),
                    'valor_total': round(valor_total_general, 2)
                },
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': date.today().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error en clasificación ABC: {e}")
            return {'exito': False, 'mensaje': str(e)}
    
    def _calcular_eoq(
        self, 
        demanda_anual: float,
        costo_pedido: float,
        costo_almacen: float
    ) -> float:
        """
        Cantidad Económica de Pedido (EOQ)
        
        EOQ = sqrt(2 * D * S / H)
        D = Demanda anual
        S = Costo por pedido
        H = Costo de almacenamiento por unidad
        """
        if costo_almacen <= 0:
            costo_almacen = 1
        
        eoq = math.sqrt((2 * demanda_anual * costo_pedido) / costo_almacen)
        return max(1, eoq)
    
    def _calcular_stock_seguridad(
        self,
        demanda_diaria: float,
        desviacion: float,
        lead_time_dias: int,
        z: float
    ) -> float:
        """
        Stock de Seguridad
        
        SS = Z * σ * sqrt(L)
        Z = Factor de nivel de servicio
        σ = Desviación estándar de demanda
        L = Lead time
        """
        return z * desviacion * math.sqrt(lead_time_dias)
    
    def _calcular_punto_reorden(
        self,
        demanda_diaria: float,
        lead_time_dias: int,
        stock_seguridad: float
    ) -> float:
        """
        Punto de Reorden
        
        ROP = (D * L) + SS
        D = Demanda diaria
        L = Lead time
        SS = Stock de seguridad
        """
        return (demanda_diaria * lead_time_dias) + stock_seguridad
    
    def _get_z_factor(self, nivel_servicio: float) -> float:
        """Obtiene factor Z para nivel de servicio"""
        if nivel_servicio >= 0.99:
            return self.Z_FACTORS[0.99]
        elif nivel_servicio >= 0.95:
            return self.Z_FACTORS[0.95]
        else:
            return self.Z_FACTORS[0.90]
    
    def _generar_recomendaciones(
        self,
        stock_actual: int,
        punto_reorden: float,
        eoq: float,
        stock_minimo_actual: int
    ) -> List[str]:
        """Genera recomendaciones basadas en análisis"""
        recomendaciones = []
        
        if stock_actual < punto_reorden:
            recomendaciones.append(
                f"⚠️ Stock actual ({stock_actual}) está por debajo del punto de reorden ({round(punto_reorden)}). "
                f"Se recomienda pedir {round(eoq)} unidades."
            )
        
        if stock_minimo_actual < punto_reorden * 0.5:
            recomendaciones.append(
                f"📊 El stock mínimo configurado ({stock_minimo_actual}) está muy bajo. "
                f"Considere aumentarlo a {round(punto_reorden)}."
            )
        
        if stock_actual > punto_reorden * 3:
            recomendaciones.append(
                f"📦 Posible exceso de inventario. Stock actual ({stock_actual}) "
                f"excede significativamente el punto de reorden."
            )
        
        if not recomendaciones:
            recomendaciones.append("✅ Los niveles de inventario están dentro de los parámetros óptimos.")
        
        return recomendaciones

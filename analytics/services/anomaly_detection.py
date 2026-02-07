"""
Anomaly Detector - Detección de anomalías en ventas e inventario

Detecta:
- Ventas inusualmente altas/bajas
- Cambios bruscos en patrones
- Posible fraude o error de registro
- Productos con comportamiento atípico

Integración:
- Publica eventos al EventBus cuando detecta anomalías
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detector de anomalías en datos de ventas e inventario
    
    Métodos:
    - Z-Score para detección de outliers
    - IQR para rango intercuartil
    - Análisis de tendencias
    """
    
    # Configuración
    Z_SCORE_THRESHOLD = 3.0  # 3 desviaciones estándar
    IQR_FACTOR = 1.5
    MIN_DATOS_PARA_ANALISIS = 10
    
    TIPOS_ANOMALIA = {
        'VENTA_ALTA': 'Venta inusualmente alta',
        'VENTA_BAJA': 'Venta inusualmente baja',
        'CAMBIO_PATRON': 'Cambio brusco en patrón',
        'SIN_MOVIMIENTO': 'Producto sin movimiento',
        'STOCK_NEGATIVO': 'Stock negativo detectado',
        'PRECIO_ANOMALO': 'Precio fuera de rango',
    }
    
    def __init__(self):
        from .etl_processor import ETLProcessor
        self.etl = ETLProcessor()
    
    def detectar_anomalias_ventas(
        self, 
        dias: int = 30,
        umbral_z: float = None
    ) -> Dict[str, Any]:
        """
        Detecta anomalías en ventas recientes
        
        Args:
            dias: Días a analizar
            umbral_z: Z-score threshold (default: 3.0)
            
        Returns:
            dict con anomalías detectadas y severidad
        """
        umbral_z = umbral_z or self.Z_SCORE_THRESHOLD
        
        try:
            # Obtener ventas
            ventas = self.etl.extract_ventas_historicas(dias=dias)
            
            if len(ventas) < self.MIN_DATOS_PARA_ANALISIS:
                return {
                    'exito': False,
                    'mensaje': f'Insuficientes datos: {len(ventas)}',
                    'anomalias': []
                }
            
            # Agrupar por fecha
            ventas_diarias = defaultdict(lambda: {'cantidad': 0, 'total': 0})
            for v in ventas:
                fecha = v['fecha']
                ventas_diarias[fecha]['cantidad'] += v['cantidad']
                ventas_diarias[fecha]['total'] += v['total']
            
            if len(ventas_diarias) < 5:
                return {
                    'exito': False,
                    'mensaje': 'Insuficientes días con ventas',
                    'anomalias': []
                }
            
            # Calcular estadísticas
            totales = [v['total'] for v in ventas_diarias.values()]
            media = statistics.mean(totales)
            desviacion = statistics.stdev(totales) if len(totales) > 1 else 1
            
            anomalias = []
            
            for fecha, datos in ventas_diarias.items():
                total = datos['total']
                
                # Calcular Z-score
                z_score = (total - media) / desviacion if desviacion > 0 else 0
                
                if abs(z_score) > umbral_z:
                    tipo = 'VENTA_ALTA' if z_score > 0 else 'VENTA_BAJA'
                    severidad = self._calcular_severidad(abs(z_score))
                    
                    anomalias.append({
                        'tipo': tipo,
                        'descripcion': self.TIPOS_ANOMALIA[tipo],
                        'fecha': fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha),
                        'valor': round(total, 2),
                        'valor_esperado': round(media, 2),
                        'z_score': round(z_score, 2),
                        'desviacion_porcentaje': round(abs(z_score) * 100 / umbral_z, 1),
                        'severidad': severidad
                    })
            
            # Publicar al EventBus si hay anomalías críticas
            anomalias_criticas = [a for a in anomalias if a['severidad'] == 'CRITICA']
            if anomalias_criticas:
                self._publicar_anomalias(anomalias_criticas)
            
            return {
                'exito': True,
                'anomalias': sorted(anomalias, key=lambda x: -abs(x['z_score'])),
                'estadisticas': {
                    'media_diaria': round(media, 2),
                    'desviacion': round(desviacion, 2),
                    'dias_analizados': len(ventas_diarias),
                    'umbral_z': umbral_z
                },
                'resumen': {
                    'total_anomalias': len(anomalias),
                    'criticas': len([a for a in anomalias if a['severidad'] == 'CRITICA']),
                    'altas': len([a for a in anomalias if a['severidad'] == 'ALTA']),
                    'medias': len([a for a in anomalias if a['severidad'] == 'MEDIA'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error detectando anomalías: {e}")
            return {
                'exito': False,
                'mensaje': str(e),
                'anomalias': []
            }
    
    def detectar_productos_sin_movimiento(
        self, 
        dias_sin_venta: int = 30
    ) -> Dict[str, Any]:
        """
        Detecta productos sin movimiento reciente
        """
        try:
            from app.models import Product, SaleDetail
            from datetime import timedelta
            
            fecha_corte = date.today() - timedelta(days=dias_sin_venta)
            
            # Productos con ventas recientes
            productos_con_ventas = SaleDetail.objects.filter(
                venta__fecha__gte=fecha_corte
            ).values_list('producto_id', flat=True).distinct()
            
            # Productos sin ventas
            productos_sin_movimiento = Product.objects.filter(
                stock_actual__gt=0  # Con stock
            ).exclude(
                id__in=productos_con_ventas
            ).values('id', 'nombre', 'codigo', 'stock_actual', 'precio_compra')[:50]
            
            anomalias = []
            valor_inmovilizado = 0
            
            for p in productos_sin_movimiento:
                costo = float(p['precio_compra'] or 0) * (p['stock_actual'] or 0)
                valor_inmovilizado += costo
                
                anomalias.append({
                    'tipo': 'SIN_MOVIMIENTO',
                    'descripcion': self.TIPOS_ANOMALIA['SIN_MOVIMIENTO'],
                    'producto_id': p['id'],
                    'nombre': p['nombre'],
                    'codigo': p['codigo'],
                    'stock': p['stock_actual'],
                    'valor_inmovilizado': round(costo, 2),
                    'dias_sin_venta': dias_sin_venta,
                    'severidad': 'MEDIA' if costo < 500000 else 'ALTA'
                })
            
            return {
                'exito': True,
                'anomalias': anomalias,
                'resumen': {
                    'productos_sin_movimiento': len(anomalias),
                    'valor_total_inmovilizado': round(valor_inmovilizado, 2),
                    'dias_analizados': dias_sin_venta
                }
            }
            
        except Exception as e:
            logger.error(f"Error detectando productos sin movimiento: {e}")
            return {'exito': False, 'mensaje': str(e), 'anomalias': []}
    
    def detectar_anomalias_producto(
        self, 
        producto_id: int,
        dias: int = 90
    ) -> Dict[str, Any]:
        """
        Analiza anomalías específicas de un producto
        """
        try:
            ventas = self.etl.extract_ventas_historicas(
                dias=dias,
                producto_id=producto_id
            )
            
            if len(ventas) < self.MIN_DATOS_PARA_ANALISIS:
                return {
                    'exito': False,
                    'mensaje': f'Insuficientes ventas: {len(ventas)}',
                    'producto_id': producto_id
                }
            
            # Agrupar por semana para análisis de tendencia
            ventas_semanales = defaultdict(lambda: 0)
            for v in ventas:
                semana = v['fecha'] - timedelta(days=v['fecha'].weekday())
                ventas_semanales[semana] += v['cantidad']
            
            semanas = sorted(ventas_semanales.keys())
            cantidades = [ventas_semanales[s] for s in semanas]
            
            if len(cantidades) < 4:
                return {
                    'exito': False,
                    'mensaje': 'Insuficientes semanas de datos',
                    'producto_id': producto_id
                }
            
            # Detectar tendencia
            tendencia = self._detectar_tendencia(cantidades)
            
            # Detectar cambios bruscos
            cambios_bruscos = self._detectar_cambios_bruscos(cantidades, semanas)
            
            # Detectar estacionalidad básica
            estacionalidad = self._detectar_estacionalidad(ventas)
            
            return {
                'exito': True,
                'producto_id': producto_id,
                'analisis': {
                    'tendencia': tendencia,
                    'cambios_bruscos': cambios_bruscos,
                    'estacionalidad': estacionalidad
                },
                'estadisticas': {
                    'semanas_analizadas': len(cantidades),
                    'promedio_semanal': round(statistics.mean(cantidades), 1),
                    'desviacion': round(statistics.stdev(cantidades), 1) if len(cantidades) > 1 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analizando producto {producto_id}: {e}")
            return {'exito': False, 'mensaje': str(e), 'producto_id': producto_id}
    
    def _calcular_severidad(self, z_score: float) -> str:
        """Calcula severidad basada en Z-score"""
        if z_score > 4.0:
            return 'CRITICA'
        elif z_score > 3.5:
            return 'ALTA'
        else:
            return 'MEDIA'
    
    def _detectar_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Detecta tendencia en serie temporal"""
        if len(valores) < 4:
            return {'tipo': 'INSUFICIENTES_DATOS'}
        
        # Comparar primera y segunda mitad
        mitad = len(valores) // 2
        primera_mitad = statistics.mean(valores[:mitad])
        segunda_mitad = statistics.mean(valores[mitad:])
        
        cambio_porcentual = ((segunda_mitad - primera_mitad) / primera_mitad * 100) if primera_mitad > 0 else 0
        
        if cambio_porcentual > 20:
            tipo = 'CRECIENTE'
        elif cambio_porcentual < -20:
            tipo = 'DECRECIENTE'
        else:
            tipo = 'ESTABLE'
        
        return {
            'tipo': tipo,
            'cambio_porcentual': round(cambio_porcentual, 1),
            'promedio_inicio': round(primera_mitad, 1),
            'promedio_fin': round(segunda_mitad, 1)
        }
    
    def _detectar_cambios_bruscos(
        self, 
        valores: List[float],
        fechas: List
    ) -> List[Dict[str, Any]]:
        """Detecta cambios bruscos semana a semana"""
        cambios = []
        
        for i in range(1, len(valores)):
            anterior = valores[i-1]
            actual = valores[i]
            
            if anterior > 0:
                cambio = ((actual - anterior) / anterior) * 100
                
                if abs(cambio) > 50:  # Más de 50% de cambio
                    cambios.append({
                        'fecha': fechas[i].isoformat() if hasattr(fechas[i], 'isoformat') else str(fechas[i]),
                        'cambio_porcentual': round(cambio, 1),
                        'valor_anterior': round(anterior, 1),
                        'valor_actual': round(actual, 1),
                        'tipo': 'INCREMENTO' if cambio > 0 else 'DECREMENTO'
                    })
        
        return cambios
    
    def _detectar_estacionalidad(self, ventas: List[Dict]) -> Dict[str, Any]:
        """Detecta patrones estacionales básicos"""
        # Agrupar por día de la semana
        por_dia = defaultdict(list)
        for v in ventas:
            dia = v['fecha'].weekday()
            por_dia[dia].append(v['cantidad'])
        
        dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        promedios = {}
        
        for dia, cantidades in por_dia.items():
            promedios[dias_nombres[dia]] = round(statistics.mean(cantidades), 1) if cantidades else 0
        
        # Encontrar día más alto y más bajo
        if promedios:
            dia_alto = max(promedios, key=promedios.get)
            dia_bajo = min(promedios, key=promedios.get)
        else:
            dia_alto = dia_bajo = 'N/A'
        
        return {
            'por_dia_semana': promedios,
            'dia_mas_ventas': dia_alto,
            'dia_menos_ventas': dia_bajo
        }
    
    def _publicar_anomalias(self, anomalias: List[Dict]):
        """Publica anomalías críticas al EventBus"""
        try:
            from core.event_bus import event_bus, EventTypes
            
            event_bus.publish(EventTypes.ANOMALIA_DETECTADA, {
                'cantidad': len(anomalias),
                'anomalias': anomalias[:5],  # Limitar a 5
                'timestamp': timezone.now().isoformat()
            })
            
            logger.info(f"Publicadas {len(anomalias)} anomalías al EventBus")
            
        except Exception as e:
            logger.warning(f"No se pudieron publicar anomalías: {e}")

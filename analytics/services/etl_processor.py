"""
ETL Processor - Limpieza y preparación de datos para modelos ML

Punto Crítico del Plan:
> Los modelos de ML necesitan **datos limpios**. Este proceso ETL
> (Extract, Transform, Load) limpia y prepara datos históricos
> antes de enviarlos a DemandForecaster.

Funciones:
- Extracción de ventas históricas
- Limpieza de outliers
- Manejo de valores nulos
- Normalización de datos
- Agregación de features (día_semana, mes, festivo)
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q, Min, Max

logger = logging.getLogger(__name__)


class ETLProcessor:
    """
    Procesador ETL para preparación de datos de Analytics
    
    Limpia, transforma y prepara datos para modelos de ML.
    """
    
    # Configuración
    DEFAULT_DIAS_HISTORICO = 365
    OUTLIER_IQR_FACTOR = 1.5
    MIN_VENTAS_PARA_ANALISIS = 10
    
    # Festivos Colombia (simplificado - idealmente cargar de DB)
    FESTIVOS_COLOMBIA_2026 = [
        date(2026, 1, 1),   # Año Nuevo
        date(2026, 1, 6),   # Reyes Magos
        date(2026, 3, 23),  # San José
        date(2026, 4, 9),   # Jueves Santo
        date(2026, 4, 10),  # Viernes Santo
        date(2026, 5, 1),   # Día del Trabajo
        date(2026, 5, 25),  # Ascensión
        date(2026, 6, 15),  # Corpus Christi
        date(2026, 6, 22),  # Sagrado Corazón
        date(2026, 6, 29),  # San Pedro y San Pablo
        date(2026, 7, 20),  # Independencia
        date(2026, 8, 7),   # Batalla de Boyacá
        date(2026, 8, 17),  # Asunción
        date(2026, 10, 12), # Día de la Raza
        date(2026, 11, 2),  # Todos los Santos
        date(2026, 11, 16), # Independencia Cartagena
        date(2026, 12, 8),  # Inmaculada
        date(2026, 12, 25), # Navidad
    ]
    
    def __init__(self):
        self._cache = {}
    
    # =========================================================================
    # EXTRACT - Extracción de datos
    # =========================================================================
    
    def extract_ventas_historicas(
        self, 
        dias: int = None,
        fecha_inicio: date = None,
        fecha_fin: date = None,
        producto_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Extrae ventas históricas del período especificado
        
        Args:
            dias: Días hacia atrás desde hoy
            fecha_inicio: Fecha inicio específica
            fecha_fin: Fecha fin específica
            producto_id: Filtrar por producto específico
            
        Returns:
            Lista de ventas con campos normalizados
        """
        try:
            from app.models import Sale, SaleDetail
            
            if dias is None and fecha_inicio is None:
                dias = self.DEFAULT_DIAS_HISTORICO
            
            if fecha_inicio is None:
                fecha_inicio = timezone.now().date() - timedelta(days=dias)
            
            if fecha_fin is None:
                fecha_fin = timezone.now().date()
            
            # Query base
            ventas_qs = SaleDetail.objects.filter(
                sale__fecha__range=[fecha_inicio, fecha_fin]
            ).exclude(
                sale__estado__in=['ANULADA', 'CANCELADA']
            ).select_related('sale', 'product')
            
            # Filtrar por producto si se especifica
            if producto_id:
                ventas_qs = ventas_qs.filter(product_id=producto_id)
            
            # Extraer datos
            ventas = []
            for detalle in ventas_qs.iterator():
                ventas.append({
                    'fecha': detalle.sale.fecha.date() if hasattr(detalle.sale.fecha, 'date') else detalle.sale.fecha,
                    'producto_id': detalle.product_id,
                    'producto_nombre': detalle.product.nombre,
                    'cantidad': float(detalle.cantidad),
                    'precio_unitario': float(detalle.precio_unitario) if detalle.precio_unitario else 0,
                    'total': float(detalle.cantidad * (detalle.precio_unitario or 0)),
                    'venta_id': detalle.sale_id,
                })
            
            logger.info(f"Extraídas {len(ventas)} ventas del período {fecha_inicio} a {fecha_fin}")
            return ventas
            
        except ImportError:
            logger.error("Modelos de ventas no disponibles")
            return []
        except Exception as e:
            logger.error(f"Error extrayendo ventas: {e}")
            return []
    
    def extract_inventario_actual(self) -> List[Dict[str, Any]]:
        """Extrae estado actual del inventario"""
        try:
            from app.models import Product
            
            productos = Product.objects.all().values(
                'id', 'nombre', 'codigo', 'stock', 'stock_minimo',
                'precio_compra', 'precio_venta', 'categoria_id'
            )
            
            return [
                {
                    'producto_id': p['id'],
                    'nombre': p['nombre'],
                    'codigo': p['codigo'],
                    'stock_actual': p['stock'] or 0,
                    'stock_minimo': p['stock_minimo'] or 0,
                    'precio_compra': float(p['precio_compra'] or 0),
                    'precio_venta': float(p['precio_venta'] or 0),
                    'categoria_id': p['categoria_id']
                }
                for p in productos
            ]
            
        except Exception as e:
            logger.error(f"Error extrayendo inventario: {e}")
            return []
    
    # =========================================================================
    # TRANSFORM - Transformación y limpieza
    # =========================================================================
    
    def transform_para_forecasting(
        self, 
        ventas_raw: List[Dict[str, Any]],
        agregacion: str = 'diaria'
    ) -> Dict[str, Any]:
        """
        Limpia y transforma datos para modelos de predicción
        
        Operaciones:
        - Eliminar outliers usando IQR
        - Manejar valores nulos
        - Agregar features temporales
        - Normalizar formatos
        
        Args:
            ventas_raw: Ventas sin procesar
            agregacion: 'diaria', 'semanal', 'mensual'
            
        Returns:
            Dataset listo para sklearn
        """
        if not ventas_raw:
            return {'datos': [], 'features': [], 'estadisticas': {}}
        
        # 1. Agrupar por fecha y producto
        agrupado = self._agrupar_ventas(ventas_raw, agregacion)
        
        # 2. Detectar y remover outliers
        datos_limpios = self._remover_outliers(agrupado)
        
        # 3. Agregar features temporales
        datos_features = self._agregar_features_temporales(datos_limpios)
        
        # 4. Calcular estadísticas
        estadisticas = self._calcular_estadisticas(datos_features)
        
        logger.info(f"Transformación completa: {len(ventas_raw)} -> {len(datos_features)} registros")
        
        return {
            'datos': datos_features,
            'features': ['dia_semana', 'mes', 'es_festivo', 'es_fin_semana', 'semana_mes'],
            'estadisticas': estadisticas,
            'outliers_removidos': len(agrupado) - len(datos_limpios),
            'agregacion': agregacion
        }
    
    def _agrupar_ventas(
        self, 
        ventas: List[Dict], 
        agregacion: str
    ) -> List[Dict[str, Any]]:
        """Agrupa ventas por período"""
        agrupado = defaultdict(lambda: defaultdict(lambda: {
            'cantidad': 0, 'total': 0, 'transacciones': 0
        }))
        
        for v in ventas:
            fecha = v['fecha']
            producto_id = v['producto_id']
            
            # Determinar clave de período
            if agregacion == 'diaria':
                periodo = fecha
            elif agregacion == 'semanal':
                periodo = fecha - timedelta(days=fecha.weekday())
            else:  # mensual
                periodo = fecha.replace(day=1)
            
            agrupado[producto_id][periodo]['cantidad'] += v['cantidad']
            agrupado[producto_id][periodo]['total'] += v['total']
            agrupado[producto_id][periodo]['transacciones'] += 1
        
        # Convertir a lista
        resultado = []
        for producto_id, periodos in agrupado.items():
            for fecha, datos in periodos.items():
                resultado.append({
                    'producto_id': producto_id,
                    'fecha': fecha,
                    'cantidad': datos['cantidad'],
                    'total': datos['total'],
                    'transacciones': datos['transacciones'],
                    'ticket_promedio': datos['total'] / datos['transacciones'] if datos['transacciones'] > 0 else 0
                })
        
        return resultado
    
    def _remover_outliers(self, datos: List[Dict]) -> List[Dict]:
        """
        Remueve outliers usando método IQR
        
        Outlier = valor fuera de [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
        """
        if len(datos) < 10:
            return datos
        
        # Agrupar por producto
        por_producto = defaultdict(list)
        for d in datos:
            por_producto[d['producto_id']].append(d)
        
        resultado = []
        
        for producto_id, ventas_prod in por_producto.items():
            if len(ventas_prod) < 5:
                resultado.extend(ventas_prod)
                continue
            
            # Calcular IQR para cantidad
            cantidades = sorted([v['cantidad'] for v in ventas_prod])
            q1_idx = len(cantidades) // 4
            q3_idx = (3 * len(cantidades)) // 4
            q1 = cantidades[q1_idx]
            q3 = cantidades[q3_idx]
            iqr = q3 - q1
            
            limite_inferior = q1 - self.OUTLIER_IQR_FACTOR * iqr
            limite_superior = q3 + self.OUTLIER_IQR_FACTOR * iqr
            
            # Filtrar outliers
            for v in ventas_prod:
                if limite_inferior <= v['cantidad'] <= limite_superior:
                    resultado.append(v)
        
        return resultado
    
    def _agregar_features_temporales(self, datos: List[Dict]) -> List[Dict]:
        """Agrega features temporales para ML"""
        for d in datos:
            fecha = d['fecha']
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            
            d['dia_semana'] = fecha.weekday()  # 0=Lunes, 6=Domingo
            d['mes'] = fecha.month
            d['dia_mes'] = fecha.day
            d['semana_mes'] = (fecha.day - 1) // 7 + 1
            d['es_fin_semana'] = 1 if fecha.weekday() >= 5 else 0
            d['es_festivo'] = 1 if fecha in self.FESTIVOS_COLOMBIA_2026 else 0
            d['trimestre'] = (fecha.month - 1) // 3 + 1
        
        return datos
    
    def _calcular_estadisticas(self, datos: List[Dict]) -> Dict[str, Any]:
        """Calcula estadísticas descriptivas"""
        if not datos:
            return {}
        
        cantidades = [d['cantidad'] for d in datos]
        totales = [d['total'] for d in datos]
        
        return {
            'registros': len(datos),
            'cantidad': {
                'min': min(cantidades),
                'max': max(cantidades),
                'promedio': sum(cantidades) / len(cantidades),
                'suma': sum(cantidades)
            },
            'total': {
                'min': min(totales),
                'max': max(totales),
                'promedio': sum(totales) / len(totales),
                'suma': sum(totales)
            },
            'productos_unicos': len(set(d['producto_id'] for d in datos)),
            'fechas': {
                'inicio': min(d['fecha'] for d in datos).isoformat(),
                'fin': max(d['fecha'] for d in datos).isoformat()
            }
        }
    
    # =========================================================================
    # LOAD - Preparación para modelos
    # =========================================================================
    
    def load_dataset_entrenamiento(
        self, 
        producto_id: int = None,
        dias: int = 365
    ) -> Dict[str, Any]:
        """
        Retorna dataset listo para sklearn
        
        Args:
            producto_id: ID del producto (None = todos)
            dias: Días de historia a usar
            
        Returns:
            dict con X (features), y (target), metadata
        """
        # Extract
        ventas_raw = self.extract_ventas_historicas(
            dias=dias,
            producto_id=producto_id
        )
        
        if len(ventas_raw) < self.MIN_VENTAS_PARA_ANALISIS:
            return {
                'exito': False,
                'mensaje': f'Insuficientes datos: {len(ventas_raw)} < {self.MIN_VENTAS_PARA_ANALISIS}',
                'X': [],
                'y': []
            }
        
        # Transform
        resultado = self.transform_para_forecasting(ventas_raw, 'diaria')
        datos = resultado['datos']
        
        if not datos:
            return {
                'exito': False,
                'mensaje': 'No hay datos después de limpieza',
                'X': [],
                'y': []
            }
        
        # Preparar X e y
        feature_names = ['dia_semana', 'mes', 'dia_mes', 'semana_mes', 'es_fin_semana', 'es_festivo', 'trimestre']
        
        X = []
        y = []
        
        for d in datos:
            X.append([d[f] for f in feature_names])
            y.append(d['cantidad'])
        
        return {
            'exito': True,
            'X': X,
            'y': y,
            'feature_names': feature_names,
            'estadisticas': resultado['estadisticas'],
            'outliers_removidos': resultado['outliers_removidos'],
            'producto_id': producto_id
        }
    
    def get_datos_para_prediccion(
        self, 
        fecha_inicio: date,
        fecha_fin: date
    ) -> List[Dict[str, Any]]:
        """
        Genera features para fechas futuras (predicción)
        
        Args:
            fecha_inicio: Primera fecha a predecir
            fecha_fin: Última fecha a predecir
            
        Returns:
            Lista de features para cada fecha
        """
        resultado = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            resultado.append({
                'fecha': fecha_actual,
                'dia_semana': fecha_actual.weekday(),
                'mes': fecha_actual.month,
                'dia_mes': fecha_actual.day,
                'semana_mes': (fecha_actual.day - 1) // 7 + 1,
                'es_fin_semana': 1 if fecha_actual.weekday() >= 5 else 0,
                'es_festivo': 1 if fecha_actual in self.FESTIVOS_COLOMBIA_2026 else 0,
                'trimestre': (fecha_actual.month - 1) // 3 + 1
            })
            fecha_actual += timedelta(days=1)
        
        return resultado

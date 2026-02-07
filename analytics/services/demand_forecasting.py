"""
Demand Forecaster - Predicción de demanda con Machine Learning

Punto Crítico del Plan:
> Las predicciones deben incluir **nivel de confianza** e **intervalo de error**
> para evitar malas decisiones basadas en datos sin contexto.

Modelo: RandomForest para robustez y capacidad de explicar features importantes.
Fallback: Promedio móvil si no hay suficientes datos.
"""

import logging
import pickle
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class DemandForecaster:
    """
    Predictor de demanda usando RandomForest
    
    Características:
    - Entrenamiento con datos limpios del ETL
    - Predicciones con nivel de confianza
    - Fallback a promedio móvil si insuficientes datos
    - Persistencia de modelos entrenados
    """
    
    MIN_DATOS_ENTRENAMIENTO = 30
    DIAS_PROMEDIO_MOVIL = 30
    
    def __init__(self):
        from .etl_processor import ETLProcessor
        
        self.etl = ETLProcessor()
        self.modelos = {}  # Cache de modelos entrenados
        self.model_path = Path(settings.BASE_DIR) / 'analytics' / 'trained_models'
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    def entrenar_modelo(
        self, 
        producto_id: int = None,
        dias_historico: int = 365,
        forzar: bool = False
    ) -> Dict[str, Any]:
        """
        Entrena modelo de predicción para un producto
        
        Args:
            producto_id: ID del producto (None = modelo general)
            dias_historico: Días de historia para entrenamiento
            forzar: Forzar reentrenamiento aunque exista modelo
            
        Returns:
            dict con métricas de entrenamiento y confianza
        """
        cache_key = f'producto_{producto_id}' if producto_id else 'general'
        
        # Verificar si ya existe modelo
        if not forzar and cache_key in self.modelos:
            return {
                'exito': True,
                'mensaje': 'Modelo ya existe en cache',
                'desde_cache': True
            }
        
        # Obtener datos del ETL
        dataset = self.etl.load_dataset_entrenamiento(
            producto_id=producto_id,
            dias=dias_historico
        )
        
        if not dataset['exito']:
            logger.warning(f"Datos insuficientes para producto {producto_id}: {dataset['mensaje']}")
            return {
                'exito': False,
                'mensaje': dataset['mensaje'],
                'usar_fallback': True
            }
        
        X = dataset['X']
        y = dataset['y']
        
        if len(X) < self.MIN_DATOS_ENTRENAMIENTO:
            return {
                'exito': False,
                'mensaje': f'Insuficientes datos: {len(X)} < {self.MIN_DATOS_ENTRENAMIENTO}',
                'usar_fallback': True
            }
        
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.metrics import mean_absolute_error, r2_score
            import numpy as np
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Entrenar modelo
            modelo = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            
            modelo.fit(X_train, y_train)
            
            # Evaluar
            y_pred = modelo.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation para confianza
            cv_scores = cross_val_score(modelo, X, y, cv=5, scoring='r2')
            confianza = max(0, min(1, cv_scores.mean()))  # Normalizar 0-1
            
            # Calcular intervalo de error
            errores = np.abs(np.array(y_test) - y_pred)
            error_percentil_90 = np.percentile(errores, 90)
            
            # Feature importance
            feature_importance = dict(zip(
                dataset['feature_names'],
                modelo.feature_importances_
            ))
            
            # Guardar modelo
            self.modelos[cache_key] = {
                'modelo': modelo,
                'feature_names': dataset['feature_names'],
                'metricas': {
                    'mae': mae,
                    'r2': r2,
                    'confianza': confianza,
                    'error_percentil_90': error_percentil_90
                },
                'fecha_entrenamiento': timezone.now(),
                'registros_entrenamiento': len(X)
            }
            
            # Persistir modelo
            self._guardar_modelo(cache_key)
            
            logger.info(f"Modelo {cache_key} entrenado: R²={r2:.3f}, Confianza={confianza:.2%}")
            
            return {
                'exito': True,
                'metricas': {
                    'mae': float(mae),
                    'r2': float(r2),
                    'confianza': float(confianza),
                    'error_percentil_90': float(error_percentil_90)
                },
                'feature_importance': {k: float(v) for k, v in feature_importance.items()},
                'registros_entrenamiento': len(X),
                'producto_id': producto_id
            }
            
        except ImportError as e:
            logger.error(f"sklearn no disponible: {e}")
            return {
                'exito': False,
                'mensaje': 'sklearn no instalado',
                'usar_fallback': True
            }
        except Exception as e:
            logger.error(f"Error entrenando modelo: {e}")
            return {
                'exito': False,
                'mensaje': str(e),
                'usar_fallback': True
            }
    
    def predecir_demanda(
        self, 
        producto_id: int,
        dias_futuros: int = 30
    ) -> Dict[str, Any]:
        """
        Predice demanda para un producto
        
        Args:
            producto_id: ID del producto
            dias_futuros: Número de días a predecir
            
        Returns:
            dict con predicciones, confianza e intervalo de error
        """
        cache_key = f'producto_{producto_id}'
        
        # Intentar usar modelo específico, luego general
        if cache_key not in self.modelos:
            # Intentar entrenar
            resultado_entrenamiento = self.entrenar_modelo(producto_id)
            
            if not resultado_entrenamiento['exito']:
                # Usar fallback: promedio móvil
                return self._predecir_promedio_movil(producto_id, dias_futuros)
        
        modelo_info = self.modelos.get(cache_key)
        if not modelo_info:
            return self._predecir_promedio_movil(producto_id, dias_futuros)
        
        try:
            modelo = modelo_info['modelo']
            feature_names = modelo_info['feature_names']
            metricas = modelo_info['metricas']
            
            # Generar features para fechas futuras
            fecha_inicio = date.today() + timedelta(days=1)
            fecha_fin = fecha_inicio + timedelta(days=dias_futuros - 1)
            
            datos_prediccion = self.etl.get_datos_para_prediccion(fecha_inicio, fecha_fin)
            
            # Preparar X para predicción
            X_pred = []
            for d in datos_prediccion:
                X_pred.append([d[f] for f in feature_names])
            
            # Predecir
            predicciones_raw = modelo.predict(X_pred)
            
            # Calcular intervalos de confianza
            error_base = metricas['error_percentil_90']
            
            predicciones = []
            for i, d in enumerate(datos_prediccion):
                pred = max(0, predicciones_raw[i])  # No permitir negativos
                predicciones.append({
                    'fecha': d['fecha'].isoformat(),
                    'cantidad_predicha': round(pred, 1),
                    'intervalo_min': round(max(0, pred - error_base), 1),
                    'intervalo_max': round(pred + error_base, 1),
                    'es_fin_semana': d['es_fin_semana'] == 1,
                    'es_festivo': d['es_festivo'] == 1
                })
            
            # Resumen
            total_predicho = sum(p['cantidad_predicha'] for p in predicciones)
            promedio_diario = total_predicho / len(predicciones) if predicciones else 0
            
            return {
                'exito': True,
                'producto_id': producto_id,
                'predicciones': predicciones,
                'resumen': {
                    'total_periodo': round(total_predicho, 1),
                    'promedio_diario': round(promedio_diario, 1),
                    'dias_predichos': len(predicciones)
                },
                'confianza': metricas['confianza'],
                'intervalo_error': {
                    'tipo': 'percentil_90',
                    'valor': round(error_base, 1)
                },
                'modelo': {
                    'tipo': 'RandomForest',
                    'r2': metricas['r2'],
                    'fecha_entrenamiento': modelo_info['fecha_entrenamiento'].isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo demanda: {e}")
            return self._predecir_promedio_movil(producto_id, dias_futuros)
    
    def _predecir_promedio_movil(
        self, 
        producto_id: int,
        dias_futuros: int
    ) -> Dict[str, Any]:
        """
        Fallback: Predicción usando promedio móvil simple
        
        Se usa cuando no hay suficientes datos para ML.
        """
        logger.info(f"Usando fallback promedio móvil para producto {producto_id}")
        
        try:
            # Obtener ventas recientes
            ventas = self.etl.extract_ventas_historicas(
                dias=self.DIAS_PROMEDIO_MOVIL,
                producto_id=producto_id
            )
            
            if not ventas:
                return {
                    'exito': False,
                    'mensaje': 'Sin datos históricos',
                    'producto_id': producto_id
                }
            
            # Calcular promedio diario
            total_cantidad = sum(v['cantidad'] for v in ventas)
            dias_con_datos = len(set(v['fecha'] for v in ventas))
            promedio_diario = total_cantidad / dias_con_datos if dias_con_datos > 0 else 0
            
            # Desviación para intervalo
            cantidades_diarias = {}
            for v in ventas:
                fecha = v['fecha']
                if fecha not in cantidades_diarias:
                    cantidades_diarias[fecha] = 0
                cantidades_diarias[fecha] += v['cantidad']
            
            valores = list(cantidades_diarias.values())
            if len(valores) > 1:
                import statistics
                desviacion = statistics.stdev(valores)
            else:
                desviacion = promedio_diario * 0.3  # 30% como estimado
            
            # Generar predicciones
            predicciones = []
            fecha_actual = date.today() + timedelta(days=1)
            
            for i in range(dias_futuros):
                fecha = fecha_actual + timedelta(days=i)
                predicciones.append({
                    'fecha': fecha.isoformat(),
                    'cantidad_predicha': round(promedio_diario, 1),
                    'intervalo_min': round(max(0, promedio_diario - desviacion), 1),
                    'intervalo_max': round(promedio_diario + desviacion, 1)
                })
            
            return {
                'exito': True,
                'producto_id': producto_id,
                'predicciones': predicciones,
                'resumen': {
                    'total_periodo': round(promedio_diario * dias_futuros, 1),
                    'promedio_diario': round(promedio_diario, 1),
                    'dias_predichos': dias_futuros
                },
                'confianza': 0.5,  # Confianza baja para promedio móvil
                'intervalo_error': {
                    'tipo': 'desviacion_estandar',
                    'valor': round(desviacion, 1)
                },
                'modelo': {
                    'tipo': 'PromedioMovil',
                    'dias_base': self.DIAS_PROMEDIO_MOVIL,
                    'nota': 'Fallback por insuficientes datos para ML'
                }
            }
            
        except Exception as e:
            logger.error(f"Error en promedio móvil: {e}")
            return {
                'exito': False,
                'mensaje': str(e),
                'producto_id': producto_id
            }
    
    def _guardar_modelo(self, cache_key: str):
        """Persiste modelo a disco"""
        try:
            modelo_info = self.modelos.get(cache_key)
            if modelo_info:
                filepath = self.model_path / f'{cache_key}.pkl'
                with open(filepath, 'wb') as f:
                    pickle.dump(modelo_info, f)
                logger.debug(f"Modelo guardado: {filepath}")
        except Exception as e:
            logger.warning(f"No se pudo guardar modelo: {e}")
    
    def _cargar_modelo(self, cache_key: str) -> bool:
        """Carga modelo desde disco"""
        try:
            filepath = self.model_path / f'{cache_key}.pkl'
            if filepath.exists():
                with open(filepath, 'rb') as f:
                    self.modelos[cache_key] = pickle.load(f)
                logger.debug(f"Modelo cargado: {filepath}")
                return True
        except Exception as e:
            logger.warning(f"No se pudo cargar modelo: {e}")
        return False
    
    def get_productos_con_modelo(self) -> List[int]:
        """Lista productos que tienen modelo entrenado"""
        modelos_en_disco = list(self.model_path.glob('producto_*.pkl'))
        return [
            int(p.stem.replace('producto_', ''))
            for p in modelos_en_disco
        ]

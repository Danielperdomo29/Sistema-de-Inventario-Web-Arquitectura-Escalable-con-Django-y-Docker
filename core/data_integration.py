"""
Data Integration - Agregador de datos de todos los módulos

Proporciona datos consolidados para:
- Dashboard unificado
- Contexto para LLMs (patrón RAG)
- Analytics y predicciones

Integración segura con servicios existentes:
- KPIService (existente)
- Sistema de alertas (existente)
- Facturación (existente)
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

from django.db.models import Sum, Avg, Count, F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Agrega datos de todos los módulos para Analytics e IA
    
    Diseñado para integrarse con código existente sin romper funcionalidad.
    Usa try/except para manejar errores de módulos no disponibles.
    """
    
    def __init__(self):
        self._kpi_service = None
        self._cache_timeout = 300  # 5 minutos
    
    @property
    def kpi_service(self):
        """Obtiene KPIService existente de forma diferida"""
        if self._kpi_service is None:
            try:
                from app.services.kpi_service import KPIService
                self._kpi_service = KPIService
            except ImportError:
                logger.warning("KPIService no disponible")
                self._kpi_service = None
        return self._kpi_service
    
    def obtener_dashboard_completo(
        self, 
        fecha_inicio: Optional[str] = None, 
        fecha_fin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene datos consolidados para dashboard
        
        Integra con KPIService existente sin romper funcionalidad.
        En caso de error, retorna datos parciales en lugar de fallar.
        
        Args:
            fecha_inicio: Fecha inicio en formato ISO (opcional)
            fecha_fin: Fecha fin en formato ISO (opcional)
            
        Returns:
            dict: Dashboard consolidado con kpis, analytics, alertas, etc.
        """
        # Parsear fechas o usar últimos 30 días
        if fecha_inicio:
            try:
                from datetime import datetime
                fecha_inicio = datetime.fromisoformat(fecha_inicio)
            except ValueError:
                fecha_inicio = timezone.now() - timedelta(days=30)
        else:
            fecha_inicio = timezone.now() - timedelta(days=30)
        
        if fecha_fin:
            try:
                from datetime import datetime
                fecha_fin = datetime.fromisoformat(fecha_fin)
            except ValueError:
                fecha_fin = timezone.now()
        else:
            fecha_fin = timezone.now()
        
        dashboard = {
            'periodo': {
                'inicio': fecha_inicio.isoformat() if hasattr(fecha_inicio, 'isoformat') else str(fecha_inicio),
                'fin': fecha_fin.isoformat() if hasattr(fecha_fin, 'isoformat') else str(fecha_fin),
                'generado': timezone.now().isoformat()
            },
            'modo_fallback': False
        }
        
        # 1. Obtener KPIs existentes (integración segura)
        dashboard['kpis'] = self._obtener_kpis_seguros()
        
        # 2. Obtener datos para Analytics
        dashboard['analytics'] = self._obtener_datos_analytics(fecha_inicio, fecha_fin)
        
        # 3. Obtener alertas existentes
        dashboard['alertas'] = self._obtener_alertas_urgentes()
        
        # 4. Estadísticas de integración
        dashboard['estadisticas'] = {
            'total_kpis': len(dashboard['kpis']) if isinstance(dashboard['kpis'], dict) else 0,
            'total_alertas': len(dashboard['alertas']),
            'ventas_periodo': dashboard['analytics'].get('ventas_periodo', {}).get('total', 0)
        }
        
        logger.info(
            f"Dashboard generado: {dashboard['estadisticas']['total_kpis']} KPIs, "
            f"{dashboard['estadisticas']['total_alertas']} alertas"
        )
        
        return dashboard
    
    def _obtener_kpis_seguros(self) -> Dict[str, Any]:
        """Obtiene KPIs del servicio existente de forma segura"""
        try:
            if self.kpi_service:
                # Intentar diferentes métodos del KPIService
                kpis = {}
                
                # Margen bruto
                try:
                    kpis['margen_bruto'] = self.kpi_service.get_margen_bruto()
                except Exception:
                    pass
                
                # Ticket promedio
                try:
                    kpis['ticket_promedio'] = self.kpi_service.get_ticket_promedio()
                except Exception:
                    pass
                
                # Stock bajo
                try:
                    kpis['stock_bajo'] = self.kpi_service.get_stock_bajo()
                except Exception:
                    pass
                
                # Ventas evolución
                try:
                    kpis['ventas_evolucion'] = self.kpi_service.get_ventas_evolucion()
                except Exception:
                    pass
                
                return kpis
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo KPIs: {e}")
            return {}
    
    def _obtener_datos_analytics(
        self, 
        fecha_inicio, 
        fecha_fin
    ) -> Dict[str, Any]:
        """Obtiene datos estructurados para módulo Analytics"""
        try:
            from app.models import Sale, Product
            
            # Datos de ventas del período
            ventas = Sale.objects.filter(
                fecha__range=[fecha_inicio, fecha_fin]
            ).exclude(
                estado__in=['ANULADA', 'CANCELADA']
            )
            
            # Agregaciones
            ventas_agg = ventas.aggregate(
                total=Sum('total'),
                cantidad=Count('id'),
                promedio=Avg('total')
            )
            
            # Ventas por día
            ventas_por_dia = list(
                ventas.values('fecha__date')
                .annotate(total=Sum('total'), cantidad=Count('id'))
                .order_by('fecha__date')[:30]  # Limitar a 30 días
            )
            
            # Top productos vendidos
            top_productos = self._obtener_top_productos(fecha_inicio, fecha_fin, limit=10)
            
            # Estadísticas de inventario
            stats_inventario = self._obtener_stats_inventario()
            
            return {
                'ventas_periodo': {
                    'total': float(ventas_agg['total'] or 0),
                    'cantidad': ventas_agg['cantidad'] or 0,
                    'ticket_promedio': float(ventas_agg['promedio'] or 0)
                },
                'ventas_por_dia': [
                    {
                        'fecha': str(v['fecha__date']),
                        'total': float(v['total'] or 0),
                        'cantidad': v['cantidad']
                    }
                    for v in ventas_por_dia
                ],
                'top_productos': top_productos,
                'inventario': stats_inventario
            }
            
        except ImportError:
            logger.warning("Modelos de app no disponibles")
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo datos analytics: {e}")
            return {}
    
    def _obtener_top_productos(
        self, 
        fecha_inicio, 
        fecha_fin, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene productos más vendidos en el período"""
        try:
            from app.models import Product, SaleDetail
            
            # Productos con ventas en el período
            productos = Product.objects.filter(
                saledetail__sale__fecha__range=[fecha_inicio, fecha_fin]
            ).annotate(
                cantidad_vendida=Sum('saledetail__cantidad'),
                ingresos=Sum(F('saledetail__cantidad') * F('saledetail__precio_unitario'))
            ).order_by('-cantidad_vendida')[:limit]
            
            return [
                {
                    'id': p.id,
                    'codigo': getattr(p, 'codigo', ''),
                    'nombre': p.nombre,
                    'cantidad_vendida': p.cantidad_vendida or 0,
                    'ingresos': float(p.ingresos or 0)
                }
                for p in productos
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo top productos: {e}")
            return []
    
    def _obtener_stats_inventario(self) -> Dict[str, Any]:
        """Estadísticas básicas de inventario"""
        try:
            from app.models import Product
            
            total = Product.objects.count()
            bajo_stock = Product.objects.filter(
                stock__lte=F('stock_minimo')
            ).count()
            sin_stock = Product.objects.filter(stock=0).count()
            
            return {
                'total_productos': total,
                'bajo_stock': bajo_stock,
                'sin_stock': sin_stock,
                'porcentaje_critico': round((bajo_stock / total * 100), 1) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo stats inventario: {e}")
            return {'total_productos': 0, 'bajo_stock': 0, 'sin_stock': 0}
    
    def _obtener_alertas_urgentes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene alertas del sistema existente"""
        try:
            from app.models import AlertaAutomatica
            
            alertas = AlertaAutomatica.objects.filter(
                resuelta=False
            ).order_by('-fecha_creacion')[:limit]
            
            return [
                {
                    'id': a.id,
                    'titulo': getattr(a, 'titulo', a.tipo),
                    'mensaje': a.mensaje,
                    'tipo': a.tipo,
                    'fecha': a.fecha_creacion.isoformat(),
                    'producto_id': a.producto_id
                }
                for a in alertas
            ]
            
        except ImportError:
            logger.debug("Modelo AlertaAutomatica no disponible")
            return []
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {e}")
            return []
    
    # =========================================================================
    # Métodos para patrón RAG (Retrieval-Augmented Generation)
    # =========================================================================
    
    def obtener_contexto_para_consulta(
        self, 
        intencion: str, 
        usuario_id: Optional[int] = None,
        limite: int = 5
    ) -> Dict[str, Any]:
        """
        Prepara contexto estructurado para LLMs (patrón RAG)
        
        Retorna SOLO datos relevantes, NO toda la historia.
        Esto reduce costos de API y mejora precisión.
        
        Args:
            intencion: Tipo de consulta (VENTAS, INVENTARIO, FINANCIERO, etc.)
            usuario_id: ID del usuario para personalización
            limite: Máximo de registros por categoría
            
        Returns:
            dict: Contexto estructurado para enviar al LLM
        """
        contexto = {
            'intencion': intencion,
            'timestamp': timezone.now().isoformat(),
            'datos': {}
        }
        
        hoy = timezone.now()
        
        if intencion == 'VENTAS':
            contexto['datos'] = self._contexto_ventas(hoy, limite)
            
        elif intencion == 'INVENTARIO':
            contexto['datos'] = self._contexto_inventario(limite)
            
        elif intencion == 'FINANCIERO':
            contexto['datos'] = self._contexto_financiero(hoy)
            
        elif intencion == 'PREDICCION':
            contexto['datos'] = self._contexto_prediccion(hoy, limite)
            
        else:
            # Contexto general
            contexto['datos'] = {
                'resumen_ventas': self._contexto_ventas(hoy, 3),
                'resumen_inventario': self._contexto_inventario(3)
            }
        
        logger.debug(f"Contexto RAG generado para intención: {intencion}")
        return contexto
    
    def _contexto_ventas(self, fecha: Any, limite: int) -> Dict[str, Any]:
        """Contexto de ventas para RAG"""
        try:
            from app.models import Sale
            
            inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Ventas de hoy
            ventas_hoy = Sale.objects.filter(
                fecha__gte=inicio_dia
            ).exclude(estado='ANULADA').order_by('-fecha')[:limite]
            
            # Resumen
            total_hoy = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
            
            return {
                'ventas_hoy': [
                    {
                        'id': v.id,
                        'cliente': str(v.cliente) if v.cliente else 'Sin cliente',
                        'total': float(v.total),
                        'fecha': v.fecha.isoformat()
                    }
                    for v in ventas_hoy
                ],
                'resumen': {
                    'total_ventas_hoy': float(total_hoy),
                    'cantidad_hoy': ventas_hoy.count()
                }
            }
        except Exception as e:
            logger.error(f"Error en contexto ventas: {e}")
            return {}
    
    def _contexto_inventario(self, limite: int) -> Dict[str, Any]:
        """Contexto de inventario para RAG"""
        try:
            from app.models import Product
            
            # Productos con stock bajo
            bajo_stock = Product.objects.filter(
                stock__lte=F('stock_minimo')
            ).order_by('stock')[:limite]
            
            # Productos sin stock
            sin_stock = Product.objects.filter(stock=0).count()
            
            return {
                'productos_criticos': [
                    {
                        'id': p.id,
                        'nombre': p.nombre,
                        'stock_actual': p.stock,
                        'stock_minimo': p.stock_minimo,
                        'diferencia': p.stock_minimo - p.stock
                    }
                    for p in bajo_stock
                ],
                'resumen': {
                    'productos_bajo_stock': bajo_stock.count(),
                    'productos_sin_stock': sin_stock
                }
            }
        except Exception as e:
            logger.error(f"Error en contexto inventario: {e}")
            return {}
    
    def _contexto_financiero(self, fecha: Any) -> Dict[str, Any]:
        """Contexto financiero para RAG"""
        try:
            from app.models import Sale
            
            inicio_mes = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            ventas_mes = Sale.objects.filter(
                fecha__gte=inicio_mes
            ).exclude(estado='ANULADA').aggregate(
                total=Sum('total'),
                cantidad=Count('id')
            )
            
            return {
                'ventas_mes': {
                    'total': float(ventas_mes['total'] or 0),
                    'cantidad': ventas_mes['cantidad'] or 0
                },
                'nota': 'Datos de contabilidad estarán disponibles en Fase 2'
            }
        except Exception as e:
            logger.error(f"Error en contexto financiero: {e}")
            return {}
    
    def _contexto_prediccion(self, fecha: Any, limite: int) -> Dict[str, Any]:
        """Contexto para predicciones"""
        return {
            'nota': 'Predicciones estarán disponibles en Fase 3 (Analytics)',
            'fecha_consulta': fecha.isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica estado del DataAggregator"""
        checks = {
            'kpi_service': False,
            'sale_model': False,
            'product_model': False,
            'alert_model': False
        }
        
        try:
            if self.kpi_service:
                checks['kpi_service'] = True
        except Exception:
            pass
        
        try:
            from app.models import Sale
            Sale.objects.exists()
            checks['sale_model'] = True
        except Exception:
            pass
        
        try:
            from app.models import Product
            Product.objects.exists()
            checks['product_model'] = True
        except Exception:
            pass
        
        try:
            from app.models import AlertaAutomatica
            AlertaAutomatica.objects.exists()
            checks['alert_model'] = True
        except Exception:
            pass
        
        all_ok = all(checks.values())
        
        return {
            'status': 'healthy' if all_ok else 'degraded',
            'checks': checks,
            'timestamp': timezone.now().isoformat()
        }


# Singleton global
data_aggregator = DataAggregator()

"""
Servicio de análisis con IA para el sistema de inventario.
Proporciona resúmenes ejecutivos y consultas en lenguaje natural usando DeepSeek.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Sum, Count, Avg
from django.utils import timezone


class AnalyticsService:
    """Servicio de análisis inteligente del inventario"""

    def __init__(self):
        self._deepseek = None

    @property
    def ai_service(self):
        """Lazy load del servicio de IA (OpenRouter)"""
        if self._deepseek is None:
            from app.services.openrouter_service import get_ai_service
            self._deepseek = get_ai_service()
        return self._deepseek

    def _get_models(self):
        """Lazy import de modelos Django"""
        from app.models.product import Product
        from app.models.sale import Sale, SaleDetail
        from app.models.purchase import Purchase
        from app.models.category import Category
        from app.models.client import Client
        
        return {
            "Product": Product,
            "Sale": Sale,
            "SaleDetail": SaleDetail,
            "Purchase": Purchase,
            "Category": Category,
            "Client": Client,
        }

    def _decimal_to_float(self, obj):
        """Convierte Decimals a float para JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._decimal_to_float(item) for item in obj]
        return obj

    def get_sales_data(self, date: datetime = None) -> dict:
        """
        Obtiene datos de ventas para una fecha específica.
        
        Args:
            date: Fecha a consultar (default: hoy)
            
        Returns:
            Diccionario con estadísticas de ventas
        """
        models = self._get_models()
        Sale = models["Sale"]
        SaleDetail = models["SaleDetail"]
        
        if date is None:
            date = timezone.localtime(timezone.now()).date()

        # Ventas del día
        sales_today = Sale.objects.filter(
            fecha__date=date,
            estado="completada"
        )
        
        # Ventas del día anterior para comparación
        yesterday = date - timedelta(days=1)
        sales_yesterday = Sale.objects.filter(
            fecha__date=yesterday,
            estado="completada"
        )

        # Estadísticas del día
        today_stats = sales_today.aggregate(
            suma_total=Sum("total"),
            num_ventas=Count("id")
        )
        
        # Calcular promedio manualmente para evitar conflictos
        promedio_hoy = 0
        if today_stats["num_ventas"] and today_stats["num_ventas"] > 0:
            promedio_hoy = (today_stats["suma_total"] or 0) / today_stats["num_ventas"]
        
        yesterday_stats = sales_yesterday.aggregate(
            suma_total=Sum("total"),
            num_ventas=Count("id")
        )

        # Productos más vendidos del día
        top_products = SaleDetail.objects.filter(
            venta__fecha__date=date,
            venta__estado="completada"
        ).values(
            "producto__nombre"
        ).annotate(
            cantidad_total=Sum("cantidad"),
            ingresos=Sum("subtotal")
        ).order_by("-cantidad_total")[:5]

        # Clientes del día
        clients_today = sales_today.values(
            "cliente__nombre"
        ).annotate(
            total_compras=Sum("total")
        ).order_by("-total_compras")[:5]

        return self._decimal_to_float({
            "fecha": str(date),
            "ventas_hoy": {
                "total": today_stats["suma_total"] or 0,
                "cantidad": today_stats["num_ventas"] or 0,
                "promedio": promedio_hoy,
            },
            "ventas_ayer": {
                "total": yesterday_stats["suma_total"] or 0,
                "cantidad": yesterday_stats["num_ventas"] or 0,
            },
            "productos_mas_vendidos": list(top_products),
            "mejores_clientes": list(clients_today),
        })

    def get_inventory_summary(self) -> dict:
        """Obtiene resumen del estado del inventario"""
        models = self._get_models()
        Product = models["Product"]
        Category = models["Category"]

        products = Product.objects.all()
        
        # Productos con stock bajo
        low_stock = products.filter(stock_actual__lt=10).values(
            "nombre", "stock_actual", "stock_minimo"
        )[:10]
        
        # Productos sin stock
        out_of_stock = products.filter(stock_actual=0).count()
        
        # Valor total del inventario
        inventory_value = sum(
            (p.stock_actual or 0) * float(p.precio_venta or 0)
            for p in products
        )
        
        # Por categoría
        by_category = products.values(
            "categoria__nombre"
        ).annotate(
            cantidad=Count("id"),
            stock_total=Sum("stock_actual")
        ).order_by("-cantidad")[:5]

        return self._decimal_to_float({
            "total_productos": products.count(),
            "productos_sin_stock": out_of_stock,
            "productos_stock_bajo": list(low_stock),
            "valor_inventario": inventory_value,
            "por_categoria": list(by_category),
        })

    def generate_daily_summary(self, date: datetime = None) -> str:
        """
        Genera un resumen ejecutivo diario usando IA.
        
        Args:
            date: Fecha del resumen (default: hoy)
            
        Returns:
            Resumen en texto generado por IA
        """
        if date is None:
            date = timezone.localtime(timezone.now()).date()

        # Obtener datos
        sales_data = self.get_sales_data(date)
        inventory_data = self.get_inventory_summary()

        combined_data = {
            "ventas": sales_data,
            "inventario": inventory_data,
        }

        context = f"Resumen del día {date.strftime('%d/%m/%Y')} para el Sistema de Inventario"
        
        try:
            return self.ai_service.generate_summary(combined_data, context)
        except Exception as e:
            return f"Error al generar resumen: {str(e)}"

    def answer_question(self, question: str) -> str:
        """
        Responde una pregunta en lenguaje natural sobre el negocio.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Respuesta generada por IA
        """
        # Detectar qué datos necesitamos según la pregunta
        question_lower = question.lower()
        
        data = {}
        
        # Siempre incluir datos básicos
        if any(word in question_lower for word in ["venta", "vendido", "vendieron", "ingresos", "factur"]):
            data["ventas"] = self.get_sales_data()
            
        if any(word in question_lower for word in ["producto", "stock", "inventario", "existencia"]):
            data["inventario"] = self.get_inventory_summary()
            
        # Si no detectamos nada específico, incluir todo
        if not data:
            data = {
                "ventas": self.get_sales_data(),
                "inventario": self.get_inventory_summary(),
            }

        try:
            return self.ai_service.natural_language_to_insight(question, data)
        except Exception as e:
            return f"Error al procesar la consulta: {str(e)}"

    def get_quick_stats(self) -> dict:
        """
        Obtiene estadísticas rápidas para mostrar en el dashboard.
        No requiere IA.
        """
        models = self._get_models()
        Sale = models["Sale"]
        Product = models["Product"]
        
        today = timezone.localtime(timezone.now()).date()
        
        # Ventas de hoy
        today_sales = Sale.objects.filter(
            fecha__date=today,
            estado="completada"
        ).aggregate(
            suma_total=Sum("total"),
            num_ventas=Count("id")
        )
        
        # Productos con alerta
        low_stock_count = Product.objects.filter(stock_actual__lt=10).count()
        
        return self._decimal_to_float({
            "ventas_hoy_total": today_sales["suma_total"] or 0,
            "ventas_hoy_cantidad": today_sales["num_ventas"] or 0,
            "productos_stock_bajo": low_stock_count,
            "fecha": str(today),
        })


# Singleton
_analytics_instance = None


def get_analytics_service() -> AnalyticsService:
    """Obtiene instancia singleton del servicio de analytics."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AnalyticsService()
    return _analytics_instance

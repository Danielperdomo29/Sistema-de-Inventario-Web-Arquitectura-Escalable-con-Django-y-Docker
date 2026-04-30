class MetricsService:
    @staticmethod
    def get_metrics():
        from app.models.client import Client
        from app.models.product import Product
        from app.models.sale import Sale
        from app.models.warehouse import Warehouse

        metrics = {
            "clientes_totales": 0,
            "productos_totales": 0,
            "stock_bajo": 0,
            "almacenes": 0,
            "ventas_totales": 0,
            "ingresos_totales": 0,
        }

        try:
            metrics["clientes_totales"] = len(Client.get_all())
        except Exception:
            pass

        try:
            products = Product.get_all()
            metrics["productos_totales"] = len(products)
            metrics["stock_bajo"] = len([p for p in products if p.get("stock_actual", 0) < 10])
        except Exception:
            pass

        try:
            metrics["almacenes"] = len(Warehouse.get_all())
        except Exception:
            pass

        try:
            sales = Sale.get_all()
            metrics["ventas_totales"] = len(sales)
            metrics["ingresos_totales"] = sum(float(s.get("total", 0) or 0) for s in sales)
        except Exception:
            pass

        return metrics

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect

from app.models.category import Category
from app.models.client import Client
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user import User
from app.models.warehouse import Warehouse
from app.views.dashboard_view import DashboardView


class DashboardController:
    """Controlador del Dashboard"""

    @staticmethod
    def index(request):
        """Muestra el dashboard"""
        # Usar autenticación nativa de Django (compatible con AuthController)
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # KPIs Profesionales para Contadores (Fase 5)
        from app.services.kpi_service import KPIService

        # Capturar y validar periodo (días)
        PERIODOS_PERMITIDOS = [7, 30, 90, 180, 365]
        try:
            periodo_dias = int(request.GET.get("periodo", 180))
            if periodo_dias not in PERIODOS_PERMITIDOS:
                periodo_dias = 180  # Fallback a default
        except (ValueError, TypeError):
            periodo_dias = 180

        # Estadísticas generales (no dependen de periodo)
        stats = {
            "total_productos": Product.count(),
            "total_categorias": Category.count(),  # Kept from original, not in diff's new stats
            "total_clientes": Client.count(),
            "total_proveedores": Supplier.count(),  # Kept from original, not in diff's new stats
            "total_almacenes": Warehouse.count(),  # Kept from original, not in diff's new stats
            "ventas_mes": Sale.total_ventas_mes(),
            "compras_mes": Purchase.total_compras_mes(),
            "total_ventas": Sale.count(),
            "total_compras": Purchase.count(),
            "total_movimientos": InventoryMovement.count(),
        }

        # Calcular KPIs con periodo dinámico
        try:
            # Primero calcular ventas_evolucion con el periodo seleccionado
            ventas_evol = KPIService.get_ventas_evolucion(periodo_dias)

            # Para la gráfica "Mes Actual", siempre usar 30 días (agrupación diaria)
            ventas_mes_data = KPIService.get_ventas_evolucion(30)

            kpis = {
                # FASE 1: KPIs con periodo dinámico (ya actualizados)
                "margen_bruto": KPIService.get_margen_bruto(periodo_dias),
                "ticket_promedio": KPIService.get_ticket_promedio(periodo_dias),
                "top_productos": KPIService.get_top_productos(periodo_dias, 3),
                "stock_bajo": KPIService.get_stock_bajo(),  # No depende de fecha
                "ventas_evolucion": ventas_evol,
                # Gráfica "Mes Actual": siempre últimos 30 días con agrupación diaria
                "ventas_mes": {
                    "total_mes": stats["ventas_mes"],
                    "labels": ventas_mes_data["labels"],  # Formato: dd/mm (días)
                    "data": ventas_mes_data["data"],
                },
                # FASE 2: Gráficas Avanzadas (con parámetros correctos)
                "flujo_caja": KPIService.get_flujo_caja_mensual(meses=6),
                "rotacion_inventario": KPIService.get_rotacion_inventario_por_categoria(top_n=10),
                "concentracion_clientes": KPIService.get_concentracion_clientes(top_n=20, meses=6),
            }
            print("[OK] KPIs calculados correctamente:", list(kpis.keys()))
        except Exception as e:
            # Fallback si hay error en KPIs
            print(f"[ERROR] en KPIs: {type(e).__name__}: {str(e)}")
            import traceback

            traceback.print_exc()
            kpis = None

        # Obtener productos con stock bajo (menos de 10 unidades)
        productos_bajo_stock = Product.get_low_stock(limit=10)

        # Obtener últimas ventas
        ultimas_ventas = Sale.get_all(limit=5)

        # Obtener últimas compras
        ultimas_compras = Purchase.get_all(limit=5)

        # Retornar la vista del dashboard CON periodo
        return DashboardView.index(
            request, user, stats, productos_bajo_stock, ultimas_ventas, ultimas_compras, kpis, periodo_dias
        )

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

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
    @login_required(login_url="/login/")
    def index(request):
        """Muestra el dashboard"""
        # Obtenemos el usuario directamente del request (autenticación Django)
        user = request.user

        # Obtener estadísticas principales
        # Nota: Los modelos serán refactorizados a ORM, asegurando que estos métodos
        # sigan existiendo o se adapten.
        stats = {
            "total_productos": Product.count(),
            "total_categorias": Category.count(),
            "total_clientes": Client.count(),
            "total_proveedores": Supplier.count(),
            "total_almacenes": Warehouse.count(),
            "ventas_mes": Sale.total_ventas_mes(),
            "compras_mes": Purchase.total_compras_mes(),
            "total_ventas": Sale.count(),
            "total_compras": Purchase.count(),
            "total_movimientos": InventoryMovement.count(),
        }

        # KPIs Profesionales para Contadores (Fase 5)
        from app.services.kpi_service import KPIService
        
        try:
            kpis = {
                'margen_bruto': KPIService.get_margen_bruto_hoy(),
                'ticket_promedio': KPIService.get_ticket_promedio(),
                'top_productos': KPIService.get_top_productos_semana(3),
                'stock_bajo': KPIService.get_stock_bajo(),
                'ventas_mes': KPIService.get_ventas_mes_evolucion()
            }
            print("✅ KPIs calculados correctamente:", list(kpis.keys()))
        except Exception as e:
            # Fallback si hay error en KPIs
            print(f"❌ ERROR en KPIs: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            kpis = None

        # Obtener productos con stock bajo (menos de 10 unidades)
        productos_bajo_stock = Product.get_low_stock(limit=10)

        # Obtener últimas ventas
        ultimas_ventas = Sale.get_all(limit=5)

        # Obtener últimas compras
        ultimas_compras = Purchase.get_all(limit=5)

        # Renderizar dashboard
        return HttpResponse(
            DashboardView.index(
                user, request.path, stats, productos_bajo_stock, ultimas_ventas, ultimas_compras, kpis
            )
        )

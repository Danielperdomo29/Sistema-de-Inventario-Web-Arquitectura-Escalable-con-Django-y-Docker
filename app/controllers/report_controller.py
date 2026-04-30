from django.http import HttpResponse
from django.shortcuts import redirect

from app.models.report import Report
from app.models.user import User
from app.views.report_view import ReportView


class ReportController:
    @staticmethod
    def index(request):
        """Muestra el dashboard de reportes"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # Obtener datos para reportes
        data = {
            "resumen": Report.resumen_general(),
            "ventas_mes": Report.ventas_por_mes(),
            "productos_top": Report.productos_mas_vendidos(5),
            "ventas_estado": Report.ventas_por_estado(),
            "clientes_top": Report.clientes_frecuentes(5),
            "stock_bajo": Report.inventario_bajo_stock(10),
        }

        # Renderizar la vista
        return HttpResponse(ReportView.index(user, data))

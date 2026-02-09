import json

from django.shortcuts import render


class DashboardView:
    """Vista del Dashboard"""

    @staticmethod
    def index(request, user, stats, productos_bajo_stock, ultimas_ventas, ultimas_compras, kpis=None, periodo_dias=180):
        """Vista principal del dashboard mejorada CON filtro de periodo"""

        # Mapeo de periodo a texto legible
        periodo_labels = {
            7: "Últimos 7 días",
            30: "Últimos 30 días",
            90: "Últimos 3 meses",
            180: "Últimos 6 meses",
            365: "Último año",
        }
        periodo_text = periodo_labels.get(periodo_dias, f"Últimos {periodo_dias} días")

        # productos_bajo_stock puede ser lista de objetos o de dicts
        # Convertir a dicts si son objetos
        productos_stock_data = []
        for producto in productos_bajo_stock:
            if isinstance(producto, dict):
                productos_stock_data.append(producto)
            else:
                productos_stock_data.append(
                    {
                        "id": producto.id,
                        "nombre": producto.nombre,
                        "categoria": (
                            producto.categoria.nombre
                            if hasattr(producto, "categoria") and producto.categoria
                            else "N/A"
                        ),
                        "stock_actual": producto.stock_actual if hasattr(producto, "stock_actual") else 0,
                    }
                )

        # ultimas_ventas ya viene como lista de dicts desde Sale.get_all()
        # ultimas_compras ya viene como lista de dicts desde Purchase.get_all()

        context = {
            "user": user,
            "stats": stats,
            "productos_bajo_stock": productos_stock_data,
            "ultimas_ventas": ultimas_ventas,  # Already dicts from Sale.get_all()
            "ultimas_compras": ultimas_compras,  # Already dicts from Purchase.get_all()
            "kpis": kpis,
            "periodo_dias": periodo_dias,
            "periodo_text": periodo_text,
        }

        return render(request, "dashboard/index.html", context)

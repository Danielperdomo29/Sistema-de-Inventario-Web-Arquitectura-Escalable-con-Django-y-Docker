from typing import Any, Dict

from django.db.models import Q

from app.models.sale import Sale


class SaleFilterService:
    """Servicio para filtrar ventas"""

    @staticmethod
    def filter_sales(queryset, filters: Dict[str, Any]):
        """
        Filtra un queryset de ventas basado en un diccionario de filtros via GET params.

        Args:
            queryset: QuerySet inicial de ventas
            filters: Diccionario con parametros de filtrado (request.GET)

        Returns:
            QuerySet filtrado
        """
        q = Q()

        # Filtrar por rango de fechas
        fecha_desde = filters.get("fecha_desde")
        fecha_hasta = filters.get("fecha_hasta")

        if fecha_desde:
            q &= Q(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            q &= Q(fecha__date__lte=fecha_hasta)

        # Filtrar por cliente
        cliente = filters.get("cliente")
        if cliente:
            q &= Q(cliente__nombre__icontains=cliente) | Q(cliente__documento__icontains=cliente)

        # Filtrar por número de factura
        factura = filters.get("factura")
        if factura:
            q &= Q(numero_factura__icontains=factura)

        # Filtrar por producto (requiere join con items/details)
        producto = filters.get("producto")
        if producto:
            # Filtrar por items (relación 'detalles')
            q &= Q(detalles__producto__nombre__icontains=producto) | Q(detalles__producto__codigo__icontains=producto)

        return queryset.filter(q).distinct()

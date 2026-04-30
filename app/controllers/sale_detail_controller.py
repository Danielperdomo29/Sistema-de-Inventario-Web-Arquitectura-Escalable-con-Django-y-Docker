import csv

from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.product import Product
from app.models.sale import Sale, SaleDetail
from app.models.user import User
from app.views.sale_detail_view import SaleDetailView

# Ordering options allowed
ALLOWED_ORDERINGS = {
    "producto": "producto__nombre",
    "-producto": "-producto__nombre",
    "cliente": "venta__cliente__nombre",
    "-cliente": "-venta__cliente__nombre",
    "fecha": "venta__fecha",
    "-fecha": "-venta__fecha",
    "subtotal": "subtotal",
    "-subtotal": "-subtotal",
    "factura": "venta__numero_factura",
    "-factura": "-venta__numero_factura",
}


class SaleDetailController:
    @staticmethod
    def _build_queryset(request):
        """Build filtered and ordered queryset from request params"""
        qs = SaleDetail.objects.select_related("producto", "venta", "venta__cliente")

        # Search filter
        q = request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(producto__nombre__icontains=q)
                | Q(venta__cliente__nombre__icontains=q)
                | Q(venta__numero_factura__icontains=q)
            )

        # Ordering
        ordering = request.GET.get("order", "-fecha")
        order_field = ALLOWED_ORDERINGS.get(ordering, "-venta__fecha")
        qs = qs.order_by(order_field, "-id")

        return qs, q, ordering

    @staticmethod
    def index(request):
        """Mostrar lista de todos los detalles de ventas con búsqueda y paginación"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        qs, q, ordering = SaleDetailController._build_queryset(request)

        # Stats
        total_count = qs.count()
        total_subtotal = qs.aggregate(total=Sum("subtotal"))["total"] or 0

        # Pagination
        paginator = Paginator(qs, 20)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        details = []
        for d in page_obj:
            estado = d.venta.estado if d.venta.estado else "completada"
            details.append(
                {
                    "id": d.id,
                    "venta_id": d.venta_id,
                    "producto_id": d.producto_id,
                    "cantidad": d.cantidad,
                    "precio_unitario": float(d.precio_unitario),
                    "subtotal": float(d.subtotal),
                    "producto_nombre": d.producto.nombre,
                    "numero_factura": d.venta.numero_factura,
                    "fecha_venta": d.venta.fecha,
                    "cliente_nombre": d.venta.cliente.nombre,
                    "venta_estado": estado,
                }
            )

        context = {
            "q": q,
            "ordering": ordering,
            "total_count": total_count,
            "total_subtotal": float(total_subtotal),
            "page_obj": page_obj,
        }

        return HttpResponse(SaleDetailView.index(user, details, request, context))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo detalle de venta"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            try:
                venta_id = request.POST.get("venta_id")
                producto_id = request.POST.get("producto_id")
                cantidad = int(request.POST.get("cantidad", 0))
                precio_unitario = float(request.POST.get("precio_unitario", 0))

                if not venta_id or not producto_id:
                    raise ValueError("La venta y el producto son requeridos")

                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")

                if precio_unitario < 0:
                    raise ValueError("El precio unitario no puede ser negativo")

                # Transaction atomic para garantizar consistencia
                from django.db import transaction

                with transaction.atomic():
                    subtotal = cantidad * precio_unitario

                    # 1. Crear Detalle
                    SaleDetail.objects.create(
                        venta_id=venta_id,
                        producto_id=producto_id,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                    )

                    # 2. Recalcular Total Venta (ORM aggregation)
                    new_total = (
                        SaleDetail.objects.filter(venta_id=venta_id).aggregate(total=models.Sum("subtotal"))["total"]
                        or 0
                    )

                    Sale.objects.filter(id=venta_id).update(total=new_total)

                return HttpResponseRedirect("/items-venta/")

            except Exception as e:
                sales = Sale.get_all()
                products = Product.get_all()
                error_message = f"Error al crear el detalle: {str(e)}"
                return HttpResponse(SaleDetailView.create(user, sales, products, request, error_message))

        # GET request
        sales = Sale.get_all()
        products = Product.get_all()
        return HttpResponse(SaleDetailView.create(user, sales, products, request))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, detail_id):
        """Editar un detalle de venta existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener detalle via ORM
        try:
            d_obj = SaleDetail.objects.select_related("venta", "producto").get(id=detail_id)
        except SaleDetail.DoesNotExist:
            return HttpResponseRedirect("/items-venta/")

        # Diccionario para vista
        detail_dict = {
            "id": d_obj.id,
            "venta_id": d_obj.venta_id,
            "producto_id": d_obj.producto_id,
            "cantidad": d_obj.cantidad,
            "precio_unitario": float(d_obj.precio_unitario),
            "subtotal": float(d_obj.subtotal),
            "numero_factura": d_obj.venta.numero_factura,
            "producto_nombre": d_obj.producto.nombre,
        }

        if request.method == "POST":
            try:
                cantidad = int(request.POST.get("cantidad", 0))
                precio_unitario = float(request.POST.get("precio_unitario", 0))

                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")

                if precio_unitario < 0:
                    raise ValueError("El precio unitario no puede ser negativo")

                from django.db import models, transaction

                with transaction.atomic():
                    subtotal = cantidad * precio_unitario

                    # Actualizar objeto
                    d_obj.cantidad = cantidad
                    d_obj.precio_unitario = precio_unitario
                    d_obj.subtotal = subtotal
                    d_obj.save()

                    # Actualizar total venta
                    new_total = (
                        SaleDetail.objects.filter(venta_id=d_obj.venta_id).aggregate(total=models.Sum("subtotal"))[
                            "total"
                        ]
                        or 0
                    )

                    Sale.objects.filter(id=d_obj.venta_id).update(total=new_total)

                return HttpResponseRedirect("/items-venta/")

            except Exception as e:
                products = Product.get_all()
                error_message = f"Error al actualizar el detalle: {str(e)}"
                return HttpResponse(SaleDetailView.edit(user, detail_dict, products, request, error_message))

        # GET request
        products = Product.get_all()
        return HttpResponse(SaleDetailView.edit(user, detail_dict, products, request))

    @staticmethod
    def delete(request, detail_id):
        """Eliminar un detalle de venta"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            try:
                from django.db import models, transaction

                with transaction.atomic():
                    try:
                        d_obj = SaleDetail.objects.get(id=detail_id)
                        venta_id = d_obj.venta_id

                        # Eliminar
                        d_obj.delete()

                        # Actualizar total venta
                        new_total = (
                            SaleDetail.objects.filter(venta_id=venta_id).aggregate(total=models.Sum("subtotal"))[
                                "total"
                            ]
                            or 0
                        )

                        Sale.objects.filter(id=venta_id).update(total=new_total)

                    except SaleDetail.DoesNotExist:
                        pass  # Ya no existe, ignorar

            except Exception as e:
                print(f"Error al eliminar detalle: {str(e)}")

        return HttpResponseRedirect("/items-venta/")

    @staticmethod
    def view(request, detail_id):
        """Ver detalle de una venta específica con vista previa de factura"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        try:
            d = SaleDetail.objects.select_related("venta", "venta__cliente", "producto").get(id=detail_id)

            # Get all items from this same sale for invoice preview
            sale_items = SaleDetail.objects.select_related("producto").filter(venta_id=d.venta_id).order_by("id")

            items_list = []
            for item in sale_items:
                items_list.append(
                    {
                        "producto_nombre": item.producto.nombre,
                        "cantidad": item.cantidad,
                        "precio_unitario": float(item.precio_unitario),
                        "subtotal": float(item.subtotal),
                    }
                )

            detail = {
                "id": d.id,
                "venta_id": d.venta_id,
                "producto_id": d.producto_id,
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario),
                "subtotal": float(d.subtotal),
                "producto_nombre": d.producto.nombre,
                "producto_precio": float(d.producto.precio_venta),
                "numero_factura": d.venta.numero_factura,
                "fecha_venta": d.venta.fecha,
                "venta_total": float(d.venta.total),
                "venta_subtotal": float(d.venta.subtotal or 0),
                "venta_iva": float(d.venta.iva_total or 0),
                "venta_estado": d.venta.estado,
                "tipo_pago": d.venta.tipo_pago,
                "cliente_nombre": d.venta.cliente.nombre,
                "cliente_documento": d.venta.cliente.documento,
                "venta_notas": d.venta.notas or "",
                "venta_items": items_list,
            }
            return HttpResponse(SaleDetailView.view(user, detail))

        except SaleDetail.DoesNotExist:
            return HttpResponseRedirect("/items-venta/")

    @staticmethod
    def export_csv(request):
        """Exportar items de venta filtrados a CSV"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        qs, q, ordering = SaleDetailController._build_queryset(request)

        response = HttpResponse(content_type="text/csv")
        timestamp = timezone.now().strftime("%Y%m%d_%H%M")
        filename = f"items_venta_{timestamp}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(
            ["N° Factura", "Cliente", "Fecha", "Producto", "Cantidad", "Precio Unit.", "Subtotal", "Estado"]
        )

        for d in qs:
            writer.writerow(
                [
                    d.venta.numero_factura,
                    d.venta.cliente.nombre,
                    d.venta.fecha.strftime("%Y-%m-%d") if d.venta.fecha else "",
                    d.producto.nombre,
                    d.cantidad,
                    f"{float(d.precio_unitario):.2f}",
                    f"{float(d.subtotal):.2f}",
                    d.venta.estado or "completada",
                ]
            )

        return response

from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.product import Product
from app.models.sale import Sale, SaleDetail
from app.models.user import User
from app.views.sale_detail_view import SaleDetailView


class SaleDetailController:
    @staticmethod
    def index(request):
        """Mostrar lista de todos los detalles de ventas"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        # Obtener todos los detalles usando ORM
        # Usamos select_related para traer datos de producto, venta y cliente en una sola query eficiente
        details_qs = (
            SaleDetail.objects.select_related("producto", "venta", "venta__cliente")
            .order_by("-venta__fecha", "-id")
            .all()
        )

        details = []
        for d in details_qs:
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
                }
            )

        return HttpResponse(SaleDetailView.index(user, details, request))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo detalle de venta"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

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
                        SaleDetail.objects.filter(venta_id=venta_id).aggregate(
                            total=models.Sum("subtotal")
                        )["total"]
                        or 0
                    )

                    Sale.objects.filter(id=venta_id).update(total=new_total)

                return HttpResponseRedirect("/items-venta/")

            except Exception as e:
                sales = Sale.get_all()
                products = Product.get_all()
                error_message = f"Error al crear el detalle: {str(e)}"
                return HttpResponse(
                    SaleDetailView.create(user, sales, products, request, error_message)
                )

        # GET request
        sales = Sale.get_all()
        products = Product.get_all()
        return HttpResponse(SaleDetailView.create(user, sales, products, request))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, detail_id):
        """Editar un detalle de venta existente"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

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
                        SaleDetail.objects.filter(venta_id=d_obj.venta_id).aggregate(
                            total=models.Sum("subtotal")
                        )["total"]
                        or 0
                    )

                    Sale.objects.filter(id=d_obj.venta_id).update(total=new_total)

                return HttpResponseRedirect("/items-venta/")

            except Exception as e:
                products = Product.get_all()
                error_message = f"Error al actualizar el detalle: {str(e)}"
                return HttpResponse(
                    SaleDetailView.edit(user, detail_dict, products, request, error_message)
                )

        # GET request
        products = Product.get_all()
        return HttpResponse(SaleDetailView.edit(user, detail_dict, products, request))

    @staticmethod
    def delete(request, detail_id):
        """Eliminar un detalle de venta"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

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
                            SaleDetail.objects.filter(venta_id=venta_id).aggregate(
                                total=models.Sum("subtotal")
                            )["total"]
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
        """Ver detalle de una venta específica"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        try:
            d = SaleDetail.objects.select_related("venta", "venta__cliente", "producto").get(
                id=detail_id
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
                "venta_estado": d.venta.estado,
                "tipo_pago": d.venta.tipo_pago,
                "cliente_nombre": d.venta.cliente.nombre,
                "cliente_documento": d.venta.cliente.documento,
            }
            return HttpResponse(SaleDetailView.view(user, detail))

        except SaleDetail.DoesNotExist:
            return HttpResponseRedirect("/items-venta/")

import datetime as dt
import json
from datetime import date
from decimal import Decimal

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.client import Client
from app.models.product import Product
from app.models.sale import Sale, SaleDetail
from app.models.user import User
from app.services.sale_filter_service import SaleFilterService
from app.views.sale_view import SaleView


class SaleController:
    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Muestra el listado de ventas con filtros"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # 1. Base QuerySet
        queryset = Sale.objects.select_related("cliente", "usuario", "factura_electronica").order_by("-fecha", "-id")

        # 2. Aplicar filtros
        params = request.GET.dict()
        queryset = SaleFilterService.filter_sales(queryset, params)

        # 3. Convertir a dicts (Presentation Layer Data)
        sales_data = []
        for s in queryset:
            sales_data.append(
                {
                    "id": s.id,
                    "numero_factura": s.numero_factura,
                    "fecha": s.fecha,
                    "subtotal": s.subtotal or 0,
                    "iva": s.iva_total or 0,
                    "total": s.total,
                    "estado": s.estado,
                    "tipo_pago": s.tipo_pago,
                    "cliente_nombre": s.cliente.nombre,
                    "cliente_documento": s.cliente.documento,
                    "vendedor": s.usuario.username,
                    "factura_dian": getattr(s, "factura_electronica", None),
                }
            )

        # 4. Respuesta AJAX (solo filas) o Completa
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(SaleView.render_rows(user, sales_data, request))

        # Renderizar la vista completa
        return HttpResponse(SaleView.index(user, sales_data, request))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear una nueva venta"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            clients = Client.get_all()
            products = Product.get_all()
            return HttpResponse(SaleView.create(user, clients, products, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                details_json = request.POST.get("details", "[]")
                details = json.loads(details_json)

                if not details:
                    clients = Client.get_all()
                    products = Product.get_all()
                    return HttpResponse(
                        SaleView.create(
                            user,
                            clients,
                            products,
                            request,
                            error="Debe agregar al menos un producto",
                        )
                    )

                # Calcular total
                total = sum(float(d["subtotal"]) for d in details)

                # Generar número de factura
                from datetime import datetime

                numero_factura = f"F-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                # Convert date string to timezone-aware datetime
                from django.utils import timezone as tz

                fecha_str = request.POST.get("fecha", str(date.today()))
                fecha_naive = dt.datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_aware = tz.make_aware(fecha_naive, tz.get_current_timezone())

                data = {
                    "numero_factura": numero_factura,
                    "cliente_id": request.POST.get("cliente_id"),
                    "usuario_id": user.id,
                    "fecha": fecha_aware,
                    "total": total,
                    "estado": request.POST.get("estado", "completada"),
                    "tipo_pago": request.POST.get("tipo_pago", "efectivo"),
                    "notas": request.POST.get("notas", ""),
                }

                # Validaciones
                if not data["cliente_id"]:
                    clients = Client.get_all()
                    products = Product.get_all()
                    return HttpResponse(
                        SaleView.create(user, clients, products, request, error="Debe seleccionar un cliente")
                    )

                # Crear la venta (PENDIENTE para evitar trigger de factura)
                venta = Sale.objects.create(
                    numero_factura=data["numero_factura"],
                    cliente_id=data["cliente_id"],
                    usuario_id=user.id,
                    fecha=data["fecha"],
                    total=Decimal("0"),  # Se calcula después
                    estado="pendiente",  # Temporal
                    tipo_pago=data.get("tipo_pago", "efectivo"),
                    notas=data.get("notas", ""),
                )

                # Crear detalles con cálculo de IVA
                created_details = []  # Lista temporal para cálculo seguro
                for detail in details:
                    precio_unit = Decimal(str(detail.get("precio_unitario", 0)))
                    cantidad = int(detail.get("cantidad", 1))
                    iva_tasa = Decimal(str(detail.get("iva_tasa", "19.00")))

                    # Calcular IVA
                    subtotal_sin_iva = precio_unit * cantidad
                    iva_valor = subtotal_sin_iva * (iva_tasa / Decimal("100"))
                    subtotal_con_iva = subtotal_sin_iva + iva_valor

                    new_detail = SaleDetail.objects.create(
                        venta=venta,
                        producto_id=detail["producto_id"],
                        cantidad=cantidad,
                        precio_unitario=precio_unit,
                        iva_tasa=iva_tasa,
                        subtotal_sin_iva=subtotal_sin_iva,
                        iva_valor=iva_valor,
                        subtotal=subtotal_con_iva,
                    )
                    created_details.append(new_detail)

                # Calcular totales explícitamente para asegurar persistencia antes del signal
                total_subtotal = Decimal("0")
                total_iva = Decimal("0")
                total_venta = Decimal("0")

                for d in created_details:  # Usar lista local de detalles creados
                    total_subtotal += d.subtotal_sin_iva
                    total_iva += d.iva_valor
                    total_venta += d.subtotal

                venta.subtotal = total_subtotal
                venta.iva_total = total_iva
                venta.total = total_venta

                # Actualizar estado final
                venta.estado = data.get("estado", "completada")
                venta.save()

                # Redireccionar a la lista
                return HttpResponseRedirect("/ventas/")

            except Exception as e:
                clients = Client.get_all()
                products = Product.get_all()
                return HttpResponse(
                    SaleView.create(user, clients, products, request, error=f"Error al crear venta: {str(e)}")
                )

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, sale_id):
        """Editar una venta existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener la venta
        # Obtener la venta
        from django.shortcuts import get_object_or_404

        s = get_object_or_404(Sale.objects.select_related("cliente", "usuario"), id=sale_id)

        sale = {
            "id": s.id,
            "numero_factura": s.numero_factura,
            "cliente_id": s.cliente_id,
            "fecha": s.fecha,
            "total": s.total,
            "iva_total": getattr(s, "iva_total", 0),
            "estado": s.estado,
            "tipo_pago": s.tipo_pago,
            "notas": s.notas,
            "cliente_nombre": s.cliente.nombre,
            "cliente_documento": s.cliente.documento,
        }

        # Obtener detalles de la venta
        details = Sale.get_details(sale_id)

        # Si es GET, mostrar formulario
        if request.method == "GET":
            clients = Client.get_all()
            products = Product.get_all()
            return HttpResponse(SaleView.edit(user, sale, details, clients, products, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                details_json = request.POST.get("details", "[]")
                new_details = json.loads(details_json)

                if not new_details:
                    clients = Client.get_all()
                    products = Product.get_all()
                    return HttpResponse(
                        SaleView.edit(
                            user,
                            sale,
                            details,
                            clients,
                            products,
                            request,
                            error="Debe agregar al menos un producto",
                        )
                    )

                # Calcular total
                total = sum(float(d["subtotal"]) for d in new_details)

                # Convert date string to timezone-aware datetime
                from django.utils import timezone as tz

                fecha_str = request.POST.get("fecha", str(date.today()))
                fecha_naive = dt.datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_aware = tz.make_aware(fecha_naive, tz.get_current_timezone())

                data = {
                    "numero_factura": request.POST.get("numero_factura"),
                    "cliente_id": request.POST.get("cliente_id"),
                    "fecha": fecha_aware,
                    "total": total,
                    "estado": request.POST.get("estado", "completada"),
                    "tipo_pago": request.POST.get("tipo_pago", "efectivo"),
                    "notas": request.POST.get("notas", ""),
                }

                # Validaciones
                if not data["cliente_id"]:
                    clients = Client.get_all()
                    products = Product.get_all()
                    return HttpResponse(
                        SaleView.edit(
                            user,
                            sale,
                            details,
                            clients,
                            products,
                            request,
                            error="Debe seleccionar un cliente",
                        )
                    )

                # Actualizar la venta
                Sale.objects.filter(id=sale_id).update(
                    numero_factura=data["numero_factura"],
                    cliente_id=data["cliente_id"],
                    fecha=data["fecha"],
                    total=total,
                    estado=data.get("estado", "completada"),
                    tipo_pago=data.get("tipo_pago", "efectivo"),
                    notas=data.get("notas", ""),
                )

                # Eliminar detalles anteriores
                SaleDetail.objects.filter(venta_id=sale_id).delete()

                # Insertar nuevos detalles con cálculo de IVA
                from decimal import Decimal

                for detail in new_details:
                    precio_unit = Decimal(str(detail.get("precio_unitario", 0)))
                    cantidad = int(detail.get("cantidad", 1))
                    iva_tasa = Decimal(str(detail.get("iva_tasa", "19.00")))

                    # Calcular IVA
                    subtotal_sin_iva = precio_unit * cantidad
                    iva_valor = subtotal_sin_iva * (iva_tasa / Decimal("100"))
                    subtotal_con_iva = subtotal_sin_iva + iva_valor

                    SaleDetail.objects.create(
                        venta_id=sale_id,
                        producto_id=detail["producto_id"],
                        cantidad=cantidad,
                        precio_unitario=precio_unit,
                        iva_tasa=iva_tasa,
                        subtotal_sin_iva=subtotal_sin_iva,
                        iva_valor=iva_valor,
                        subtotal=subtotal_con_iva,
                    )

                # Recalcular totales
                sale_obj = Sale.objects.get(id=sale_id)
                sale_obj.calculate_totals()
                sale_obj.save()

                # Redireccionar a la lista
                return HttpResponseRedirect("/ventas/")

            except Exception as e:
                clients = Client.get_all()
                products = Product.get_all()
                return HttpResponse(
                    SaleView.edit(
                        user,
                        sale,
                        details,
                        clients,
                        products,
                        request,
                        error=f"Error al actualizar venta: {str(e)}",
                    )
                )

    @staticmethod
    @ensure_csrf_cookie
    def delete(request, sale_id):
        """Eliminar una venta"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            # Verificar si tiene factura DIAN asociada
            sale = Sale.objects.get(id=sale_id)
            if hasattr(sale, "factura_dian"):
                # Anulación lógica
                sale.estado = "anulada"
                sale.save()
            else:
                # Eliminar la venta física
                try:
                    Sale.delete(sale_id)
                except Exception:
                    sale.estado = "cancelada"
                    sale.save()

        # Redireccionar a la lista siempre
        return HttpResponseRedirect("/ventas/")

    @staticmethod
    def view(request, sale_id):
        """Ver detalle de una venta"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener la venta
        sale = Sale.get_by_id(sale_id)
        if not sale:
            return HttpResponseRedirect("/ventas/")

        # Obtener detalles de la venta
        details = Sale.get_details(sale_id)

        return HttpResponse(SaleView.view(user, sale, details))

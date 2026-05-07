from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.middleware.auth_middleware import AuthMiddleware
from app.models.category import Category
from app.models.product import Product
from app.views.product_view import ProductView


class ProductController:
    """Controlador de Productos"""

    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Lista de productos"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener parámetros de búsqueda (FASE 4)
        q = request.GET.get("q", "")
        categoria_id = request.GET.get("categoria", "")

        # Obtener productos
        from django.db.models import Q

        queryset = Product.objects.select_related("categoria").all().order_by("-id")

        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))

        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        # Convertir a lista de dicts (Presentation Layer)
        products = []
        for p in queryset:
            products.append(
                {
                    "id": p.id,
                    "codigo": p.codigo,
                    "nombre": p.nombre,
                    "categoria": p.categoria.nombre if p.categoria else "Sin categoría",
                    "precio_venta": float(p.precio_venta),
                    "iva_porcentaje": float(p.iva_porcentaje),
                    "iva_tipo": p.iva_tipo,
                    "descuento": float(p.descuento),
                    "stock_actual": p.stock_actual,
                }
            )

        categories = Category.get_all()

        return HttpResponse(ProductView.index(user, request, products, categories))

    @staticmethod
    @ensure_csrf_cookie
    @AuthMiddleware.require_active_user
    def create(request):
        """Crear un nuevo producto"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            categories = Category.get_all()
            return HttpResponse(ProductView.create(user, categories, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "codigo": request.POST.get("codigo"),
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                    "categoria_id": request.POST.get("categoria_id"),
                    "precio_compra": request.POST.get("precio_compra"),
                    "precio_venta": request.POST.get("precio_venta"),
                    "stock_minimo": request.POST.get("stock_minimo", 10),
                    "stock_actual": request.POST.get("stock_actual", 0),
                    "codigo_dian": request.POST.get("codigo_dian"),
                    "iva_tipo": request.POST.get("iva_tipo", "GRAVADO"),
                    "iva_porcentaje": request.POST.get("iva_porcentaje", 19.00),
                    "unidad_medida": request.POST.get("unidad_medida", "94"),
                    "impoconsumo": request.POST.get("impoconsumo", 0.00),
                    "descuento": request.POST.get("descuento", 0.00),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["codigo"] or not data["nombre"]:
                    categories = Category.get_all()
                    return HttpResponse(
                        ProductView.create(user, categories, request, error="Código y nombre son obligatorios")
                    )

                # Crear el producto
                Product.create(data)

                # Invalidar caché de productos para reflejar el nuevo producto
                from django.core.cache import cache

                cache.delete("catalog:products:all")

                # Redireccionar a la lista
                return HttpResponseRedirect("/productos/")

            except Exception as e:
                categories = Category.get_all()
                return HttpResponse(
                    ProductView.create(user, categories, request, error=f"Error al crear producto: {str(e)}")
                )

    @staticmethod
    @ensure_csrf_cookie
    @AuthMiddleware.require_active_user
    def edit(request, product_id):
        """Editar un producto existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener el producto
        product = Product.get_by_id(product_id)
        if not product:
            return HttpResponseRedirect("/productos/")

        # Si es GET, mostrar formulario
        if request.method == "GET":
            categories = Category.get_all()
            return HttpResponse(ProductView.edit(user, product, categories, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "codigo": request.POST.get("codigo"),
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                    "categoria_id": request.POST.get("categoria_id"),
                    "precio_compra": request.POST.get("precio_compra"),
                    "precio_venta": request.POST.get("precio_venta"),
                    "stock_minimo": request.POST.get("stock_minimo", 10),
                    "stock_actual": request.POST.get("stock_actual", 0),
                    "codigo_dian": request.POST.get("codigo_dian"),
                    "iva_tipo": request.POST.get("iva_tipo"),
                    "iva_porcentaje": request.POST.get("iva_porcentaje"),
                    "unidad_medida": request.POST.get("unidad_medida"),
                    "impoconsumo": request.POST.get("impoconsumo"),
                    "descuento": request.POST.get("descuento"),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["codigo"] or not data["nombre"]:
                    categories = Category.get_all()
                    return HttpResponse(
                        ProductView.edit(
                            user,
                            product,
                            categories,
                            request,
                            error="Código y nombre son obligatorios",
                        )
                    )

                # Actualizar el producto
                Product.update(product_id, data)

                # Invalidar caché de productos para reflejar cambios
                from django.core.cache import cache

                cache.delete("catalog:products:all")

                # Redireccionar a la lista
                return HttpResponseRedirect("/productos/")

            except Exception as e:
                categories = Category.get_all()
                return HttpResponse(
                    ProductView.edit(
                        user,
                        product,
                        categories,
                        request,
                        error=f"Error al actualizar producto: {str(e)}",
                    )
                )

    @staticmethod
    @AuthMiddleware.require_active_user
    @ensure_csrf_cookie
    def delete(request, product_id):
        """Eliminar un producto"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")



        # Eliminar solo si es POST
        if request.method == "POST":
            Product.delete(product_id)

            # Invalidar caché de productos para reflejar cambios
            from django.core.cache import cache

            cache.delete("catalog:products:all")

        # Redireccionar a la lista
        return HttpResponseRedirect("/productos/")

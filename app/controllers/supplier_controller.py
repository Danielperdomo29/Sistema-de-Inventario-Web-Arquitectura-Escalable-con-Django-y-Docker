from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.middleware.auth_middleware import AuthMiddleware
from app.models.supplier import Supplier
from app.models.user import User
from app.views.supplier_view import SupplierView


class SupplierController:
    @staticmethod
    def index(request):
        """Mostrar lista de proveedores"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        suppliers = Supplier.get_all()
        total = Supplier.count()
        return HttpResponse(SupplierView.index(user, suppliers, total, request))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo proveedor"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            try:
                nombre = request.POST.get("nombre", "").strip()
                nit = request.POST.get("nit", "").strip()
                digito_verificacion = request.POST.get("digito_verificacion", "").strip()
                rut = request.POST.get("rut", "").strip()
                telefono = request.POST.get("telefono", "").strip()
                email = request.POST.get("email", "").strip()
                direccion = request.POST.get("direccion", "").strip()
                ciudad = request.POST.get("ciudad", "").strip()

                if not nombre:
                    raise ValueError("El nombre/razón social es requerido")

                data = {
                    "nombre": nombre,
                    "nit": nit,
                    "digito_verificacion": digito_verificacion,
                    "rut": rut,
                    "telefono": telefono,
                    "email": email,
                    "direccion": direccion,
                    "ciudad": ciudad,
                }

                Supplier.create(data)
                return HttpResponseRedirect("/proveedores/")

            except Exception as e:
                error_message = f"Error al crear el proveedor: {str(e)}"
                return HttpResponse(SupplierView.create(user, request, error_message))

        return HttpResponse(SupplierView.create(user, request))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, supplier_id):
        """Editar un proveedor existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        supplier = Supplier.get_by_id(supplier_id)
        if not supplier:
            return HttpResponseRedirect("/proveedores/")

        if request.method == "POST":
            try:
                nombre = request.POST.get("nombre", "").strip()
                nit = request.POST.get("nit", "").strip()
                digito_verificacion = request.POST.get("digito_verificacion", "").strip()
                rut = request.POST.get("rut", "").strip()
                telefono = request.POST.get("telefono", "").strip()
                email = request.POST.get("email", "").strip()
                direccion = request.POST.get("direccion", "").strip()
                ciudad = request.POST.get("ciudad", "").strip()

                if not nombre:
                    raise ValueError("El nombre/razón social es requerido")

                data = {
                    "nombre": nombre,
                    "nit": nit,
                    "digito_verificacion": digito_verificacion,
                    "rut": rut,
                    "telefono": telefono,
                    "email": email,
                    "direccion": direccion,
                    "ciudad": ciudad,
                }

                Supplier.update(supplier_id, data)
                return HttpResponseRedirect("/proveedores/")

            except Exception as e:
                error_message = f"Error al actualizar el proveedor: {str(e)}"
                return HttpResponse(SupplierView.edit(user, supplier, request, error_message))

        return HttpResponse(SupplierView.edit(user, supplier, request))

    @staticmethod
    def delete(request, supplier_id):
        """Eliminar lógicamente un proveedor"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            try:
                Supplier.delete(supplier_id)
            except Exception as e:
                pass

        return HttpResponseRedirect("/proveedores/")

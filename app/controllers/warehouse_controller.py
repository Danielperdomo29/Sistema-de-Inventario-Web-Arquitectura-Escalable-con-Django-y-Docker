from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.user import User
from app.models.warehouse import Warehouse
from app.views.warehouse_view import WarehouseView


class WarehouseController:
    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Muestra el listado de almacenes"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # Obtener todos los almacenes
        warehouses = Warehouse.get_all()

        # Renderizar la vista
        return HttpResponse(WarehouseView.index(user, warehouses, request))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo almacén"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(WarehouseView.create(user, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "ubicacion": request.POST.get("ubicacion"),
                    "capacidad": request.POST.get("capacidad", 0),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(WarehouseView.create(user, request, error="El nombre es obligatorio"))

                # Crear el almacén
                Warehouse.create(data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/almacenes/")

            except Exception as e:
                return HttpResponse(WarehouseView.create(user, request, error=f"Error al crear almacén: {str(e)}"))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, warehouse_id):
        """Editar un almacén existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener el almacén
        warehouse = Warehouse.get_by_id(warehouse_id)
        if not warehouse:
            return HttpResponseRedirect("/almacenes/")

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(WarehouseView.edit(user, warehouse, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "ubicacion": request.POST.get("ubicacion"),
                    "capacidad": request.POST.get("capacidad", 0),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(WarehouseView.edit(user, warehouse, request, error="El nombre es obligatorio"))

                # Actualizar el almacén
                Warehouse.update(warehouse_id, data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/almacenes/")

            except Exception as e:
                return HttpResponse(
                    WarehouseView.edit(user, warehouse, request, error=f"Error al actualizar almacén: {str(e)}")
                )

    @staticmethod
    @ensure_csrf_cookie
    def delete(request, warehouse_id):
        """Eliminar un almacén"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Eliminar solo si es POST
        if request.method == "POST":
            Warehouse.delete(warehouse_id)

        # Redireccionar a la lista
        return HttpResponseRedirect("/almacenes/")

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.middleware.auth_middleware import AuthMiddleware
from app.models.client import Client
from app.models.user import User
from app.views.client_view import ClientView


class ClientController:
    @staticmethod
    def index(request):
        """Muestra el listado de clientes"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # Obtener todos los clientes

        # Obtener todos los clientes
        clients = Client.get_all()

        # Renderizar la vista
        return HttpResponse(ClientView.index(user, clients))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo cliente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(ClientView.create(user, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "documento": request.POST.get("documento"),
                    "telefono": request.POST.get("telefono"),
                    "email": request.POST.get("email"),
                    "direccion": request.POST.get("direccion"),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(ClientView.create(user, request, error="El nombre es obligatorio"))

                # Crear el cliente
                Client.create(data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/clientes/")

            except Exception as e:
                return HttpResponse(ClientView.create(user, request, error=f"Error al crear cliente: {str(e)}"))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, client_id):
        """Editar un cliente existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener el cliente
        client = Client.get_by_id(client_id)
        if not client:
            return HttpResponseRedirect("/clientes/")

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(ClientView.edit(user, client, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "documento": request.POST.get("documento"),
                    "telefono": request.POST.get("telefono"),
                    "email": request.POST.get("email"),
                    "direccion": request.POST.get("direccion"),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(ClientView.edit(user, client, request, error="El nombre es obligatorio"))

                # Actualizar el cliente
                Client.update(client_id, data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/clientes/")

            except Exception as e:
                return HttpResponse(
                    ClientView.edit(user, client, request, error=f"Error al actualizar cliente: {str(e)}")
                )

    @staticmethod
    def delete(request, client_id):
        """Eliminar un cliente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Eliminar el cliente (soft delete)
        Client.delete(client_id)

        # Redireccionar a la lista
        return HttpResponseRedirect("/clientes/")

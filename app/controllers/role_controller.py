from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.role import Role
from app.models.user import User
from app.views.role_view import RoleView


class RoleController:
    @staticmethod
    def index(request):
        """Muestra el listado de roles"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # Obtener todos los roles
        roles = Role.get_all()

        # Renderizar la vista
        return HttpResponse(RoleView.index(user, roles))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear un nuevo rol"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(RoleView.create(user, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(RoleView.create(user, request, error="El nombre es obligatorio"))

                # Crear el rol
                Role.create(data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/roles/")

            except Exception as e:
                return HttpResponse(RoleView.create(user, request, error=f"Error al crear rol: {str(e)}"))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, role_id):
        """Editar un rol existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener el rol
        role = Role.get_by_id(role_id)
        if not role:
            return HttpResponseRedirect("/roles/")

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(RoleView.edit(user, role, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(RoleView.edit(user, role, request, error="El nombre es obligatorio"))

                # Actualizar el rol
                Role.update(role_id, data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/roles/")

            except Exception as e:
                return HttpResponse(RoleView.edit(user, role, request, error=f"Error al actualizar rol: {str(e)}"))

    @staticmethod
    def delete(request, role_id):
        """Eliminar un rol"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Eliminar el rol
        Role.delete(role_id)

        # Redireccionar a la lista
        return HttpResponseRedirect("/roles/")

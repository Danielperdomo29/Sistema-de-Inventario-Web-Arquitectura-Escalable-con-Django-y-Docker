from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from app.middleware.auth_middleware import AuthMiddleware
from app.models.category import Category
from app.models.user import User
from app.views.category_view import CategoryView


class CategoryController:
    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Muestra el listado de categorías"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return redirect("/login/")

        user = request.user

        # Obtener todas las categorías
        categories = Category.get_all()

        # Renderizar la vista
        return CategoryView.index(user, categories, request)

    @staticmethod
    @ensure_csrf_cookie
    @AuthMiddleware.require_active_user
    def create(request):
        """Crear una nueva categoría"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(CategoryView.create(user, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(CategoryView.create(user, request, error="El nombre es obligatorio"))

                # Crear la categoría
                Category.create(data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/categorias/")

            except Exception as e:
                return HttpResponse(CategoryView.create(user, request, error=f"Error al crear categoría: {str(e)}"))

    @staticmethod
    @ensure_csrf_cookie
    @AuthMiddleware.require_active_user
    def edit(request, category_id):
        """Editar una categoría existente"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        # Obtener la categoría
        category = Category.get_by_id(category_id)
        if not category:
            return HttpResponseRedirect("/categorias/")

        # Si es GET, mostrar formulario
        if request.method == "GET":
            return HttpResponse(CategoryView.edit(user, category, request))

        # Si es POST, procesar el formulario
        if request.method == "POST":
            try:
                # Obtener datos del formulario
                data = {
                    "nombre": request.POST.get("nombre"),
                    "descripcion": request.POST.get("descripcion"),
                    "activo": 1,
                }

                # Validaciones básicas
                if not data["nombre"]:
                    return HttpResponse(CategoryView.edit(user, category, request, error="El nombre es obligatorio"))

                # Actualizar la categoría
                Category.update(category_id, data)

                # Redireccionar a la lista
                return HttpResponseRedirect("/categorias/")

            except Exception as e:
                return HttpResponse(
                    CategoryView.edit(user, category, request, error=f"Error al actualizar categoría: {str(e)}")
                )

    @staticmethod
    @AuthMiddleware.require_active_user
    @ensure_csrf_cookie
    def delete(request, category_id):
        """Eliminar una categoría"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        if request.method == "POST":
            try:
                # Eliminar la categoría (soft delete)
                Category.delete(category_id)
            except Exception as e:
                print(f"Error deleting category {category_id}: {e}")
                # Podríamos pasar un error a la vista usando sessions o params,
                # pero por ahora el redirect es estándar.

        # Redireccionar a la lista
        return HttpResponseRedirect("/categorias/")

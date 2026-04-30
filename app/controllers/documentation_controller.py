from django.http import HttpResponse, HttpResponseRedirect

from app.models.user import User
from app.views.documentation_view import DocumentationView


class DocumentationController:
    """Controlador de Documentación"""

    @staticmethod
    def index(request):
        """Muestra la página de documentación del sistema"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user

        return DocumentationView.index(user, request.path)

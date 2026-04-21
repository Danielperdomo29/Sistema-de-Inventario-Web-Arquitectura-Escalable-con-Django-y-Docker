from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite acceso de escritura solo a administradores.
    Los colaboradores y clientes solo pueden leer (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        # Lectura permitida para cualquier usuario autenticado
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escritura solo para superusuarios o rol Administrador
        return request.user.is_superuser or (
            hasattr(request.user, 'role')
            and request.user.role
            and request.user.role.name == 'Administrador'
        )

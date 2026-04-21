from app.models.role import Role
from app.models.user_account import UserAccount


class AuthService:
    """
    Servicio para manejar la lógica de autorización y gestión de roles.
    Cumple con el principio de responsabilidad única (SOLID).
    """

    @staticmethod
    def get_user_role(user):
        """Obtiene el objeto Rol asociado al usuario."""
        if not user.is_authenticated:
            return None
        try:
            return Role.objects.get(id=user.rol_id)
        except Role.DoesNotExist:
            return None

    @staticmethod
    def has_permission(user, action, resource):
        """
        Verifica si un usuario tiene permiso para una acción específica.
        Lógica:
        - Admin: Todo.
        - Colaborador: Crear productos, Ver todo. (No editar/eliminar).
        - Cliente: Ver propio.
        """
        role = AuthService.get_user_role(user)
        if not role:
            return False

        if role.is_admin:
            return True

        if role.is_collaborator:
            # Colaborador puede ver todo y agregar productos
            if action == "view":
                return True
            if action == "add" and resource == "product":
                return True
            return False

        if role.is_client:
            # Cliente solo puede ver (lógica adicional por recurso sería necesaria aquí)
            return action == "view"

        return False

    @staticmethod
    def is_admin(user):
        role = AuthService.get_user_role(user)
        return role.is_admin if role else False

    @staticmethod
    def is_collaborator(user):
        role = AuthService.get_user_role(user)
        return role.is_collaborator if role else False

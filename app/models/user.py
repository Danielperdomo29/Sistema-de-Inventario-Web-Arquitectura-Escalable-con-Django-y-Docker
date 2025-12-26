from django.contrib.auth.hashers import make_password
from django.db.models import Q

from .user_account import UserAccount


class User:
    """
    Adapter/Facade para compatibilidad con el sistema antiguo.
    Utiliza UserAccount bajo el capó.
    """

    @staticmethod
    def authenticate(username, password):
        """Autentica un usuario por username o email"""
        try:
            user = UserAccount.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                # Para compatibilidad, retornamos el objeto usuario.
                # Si el código antiguo espera un dict, esto podría fallar,
                # pero Django permite acceso atributos.
                # Simulamos propiedad 'rol' para compatibilidad si es necesaria
                if not hasattr(user, "rol"):
                    user.rol = "Admin" if user.rol_id == 1 else "Usuario"
                return user
        except UserAccount.DoesNotExist:
            return None
        return None

    @staticmethod
    def create(username, email, password, nombre_completo):
        """Crea un nuevo usuario"""
        # nombre_completo se divide en first/last name simple
        parts = nombre_completo.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        user = UserAccount.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            rol_id=2,  # Por defecto
        )
        return user.id

    @staticmethod
    def exists(username=None, email=None):
        """Verifica si un usuario o email ya existe"""
        query = Q()
        if username:
            query |= Q(username=username)
        if email:
            query |= Q(email=email)

        if not query:
            return False

        return UserAccount.objects.filter(query).exists()

    @staticmethod
    def get_by_id(user_id):
        """Obtiene un usuario por ID"""
        try:
            return UserAccount.objects.get(pk=user_id)
        except UserAccount.DoesNotExist:
            return None

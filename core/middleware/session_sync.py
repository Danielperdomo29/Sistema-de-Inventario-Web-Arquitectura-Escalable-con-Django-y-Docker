from django.utils.deprecation import MiddlewareMixin


class SessionSyncMiddleware(MiddlewareMixin):
    """
    Middleware para sincronizar el estado de autenticación de Django
    con las expectativas de los controladores legacy que buscan 'user_id' en la sesión.
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            if "user_id" not in request.session or request.session["user_id"] != request.user.id:
                request.session["user_id"] = request.user.id
            if "username" not in request.session or request.session["username"] != request.user.username:
                request.session["username"] = request.user.username
        return None

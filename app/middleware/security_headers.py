class SecurityHeadersMiddleware:
    """
    Middleware para añadir cabeceras anti-tampering y proteger contra
    ataques de Burp Suite, MiTM, y retención en caché de credenciales.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Cabeceras adicionales para seguridad estricta
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Evitar pre-cacheo de respuestas de sistema para que proxies locales no guarden el state
        response["Cache-Control"] = "no-store, max-age=0"

        # Limpieza de datos en logout (Opcional, manejado mejor en sesión, pero robusto)
        if request.path == "/accounts/logout/":
            response["Clear-Site-Data"] = '"cache","cookies","storage"'

        return response

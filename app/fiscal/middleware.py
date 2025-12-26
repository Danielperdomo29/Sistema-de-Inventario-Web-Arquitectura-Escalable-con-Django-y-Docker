"""
Middleware para auditoría fiscal.

Captura el request actual y lo hace disponible para los signals.
"""
from app.fiscal.signals import set_current_request


class FiscalAuditMiddleware:
    """
    Middleware que captura el request para auditoría.
    
    Debe estar después de AuthenticationMiddleware en MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Guardar request en thread-local
        set_current_request(request)
        
        response = self.get_response(request)
        
        # Limpiar request después de la respuesta
        set_current_request(None)
        
        return response

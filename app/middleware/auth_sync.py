"""
Middleware para sincronizar estado de autenticación entre allauth y sistema existente.
"""
from django.utils.deprecation import MiddlewareMixin


class AuthSyncMiddleware(MiddlewareMixin):
    """
    Middleware para sincronizar estado de autenticación
    """
    
    def process_request(self, request):
        """
        Verifica y sincroniza el usuario autenticado
        """
        if request.user.is_authenticated:
            try:
                # CRÍTICO: Sincronizar session['user_id'] para sistema antiguo
                if 'user_id' not in request.session or request.session.get('user_id') != request.user.id:
                    request.session['user_id'] = request.user.id
                    request.session['username'] = request.user.username
                    request.session.modified = True
                
                # Asegurar que el usuario tiene rol_id
                if not hasattr(request.user, 'rol_id') or request.user.rol_id is None:
                    request.user.rol_id = 2  # Usuario por defecto
                    request.user.save(update_fields=['rol_id'])
                
                # Si viene de allauth y no tiene use_allauth marcado
                if hasattr(request.user, 'use_allauth') and not request.user.use_allauth:
                    # Verificar si tiene EmailAddress de allauth
                    try:
                        from allauth.account.models import EmailAddress
                        if EmailAddress.objects.filter(user=request.user).exists():
                            request.user.use_allauth = True
                            request.user.save(update_fields=['use_allauth'])
                    except Exception:
                        # Si allauth no está disponible, ignorar
                        pass
            except Exception as e:
                # Si hay algún error, no bloquear el request
                # Solo registrar en desarrollo
                if hasattr(request, 'META') and request.META.get('SERVER_NAME') == 'localhost':
                    print(f"AuthSyncMiddleware warning: {str(e)}")
        
        return None

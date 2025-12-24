"""
Decoradores de seguridad para control de acceso y protección.
"""
from functools import wraps
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def require_verified_email(view_func):
    """
    Requiere que el usuario tenga email verificado.
    Uso: @require_verified_email
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Verificar si el usuario tiene email verificado
        if hasattr(request.user, 'email_verified') and not request.user.email_verified:
            return HttpResponseForbidden(
                "Debes verificar tu email antes de acceder a esta página. "
                "Revisa tu bandeja de entrada."
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(allowed_roles):
    """
    Requiere que el usuario tenga un rol específico.
    
    Uso:
        @require_role([1])  # Solo admin
        @require_role([1, 2])  # Admin o usuario
    
    Args:
        allowed_roles: Lista de IDs de roles permitidos
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar rol del usuario
            if hasattr(request.user, 'rol_id'):
                if request.user.rol_id not in allowed_roles:
                    return HttpResponseForbidden(
                        "No tienes permisos para acceder a esta página."
                    )
            else:
                # Si no tiene rol_id, denegar acceso
                return HttpResponseForbidden(
                    "Tu cuenta no tiene un rol asignado. Contacta al administrador."
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(view_func):
    """
    Requiere que el usuario sea administrador (rol_id=1).
    Uso: @require_admin
    """
    return require_role([1])(view_func)


def sanitize_input(allowed_chars=None):
    """
    Sanitiza inputs para prevenir inyecciones.
    
    Uso:
        @sanitize_input(allowed_chars='alphanumeric')
        def my_view(request):
            # request.POST y request.GET están sanitizados
            pass
    
    Args:
        allowed_chars: 'alphanumeric', 'alpha', 'numeric', o None (default)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            import re
            
            def sanitize_value(value):
                if allowed_chars == 'alphanumeric':
                    return re.sub(r'[^a-zA-Z0-9\s]', '', str(value))
                elif allowed_chars == 'alpha':
                    return re.sub(r'[^a-zA-Z\s]', '', str(value))
                elif allowed_chars == 'numeric':
                    return re.sub(r'[^0-9]', '', str(value))
                return value
            
            # Sanitizar POST data
            if request.method == 'POST':
                sanitized_post = request.POST.copy()
                for key in sanitized_post.keys():
                    sanitized_post[key] = sanitize_value(sanitized_post[key])
                request.POST = sanitized_post
            
            # Sanitizar GET data
            sanitized_get = request.GET.copy()
            for key in sanitized_get.keys():
                sanitized_get[key] = sanitize_value(sanitized_get[key])
            request.GET = sanitized_get
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests=10, window_seconds=60):
    """
    Rate limiting simple basado en IP.
    
    Uso:
        @rate_limit(max_requests=5, window_seconds=60)
        def my_view(request):
            pass
    
    Args:
        max_requests: Número máximo de requests
        window_seconds: Ventana de tiempo en segundos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            import time
            
            # Obtener IP del cliente
            ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                 request.META.get('REMOTE_ADDR', ''))
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            
            # Clave de cache
            cache_key = f'rate_limit_{view_func.__name__}_{ip}'
            
            # Obtener requests actuales
            requests = cache.get(cache_key, [])
            now = time.time()
            
            # Filtrar requests dentro de la ventana
            requests = [req_time for req_time in requests 
                       if now - req_time < window_seconds]
            
            # Verificar límite
            if len(requests) >= max_requests:
                return HttpResponse(
                    f"Demasiadas solicitudes. Intenta de nuevo en {window_seconds} segundos.",
                    status=429
                )
            
            # Agregar request actual
            requests.append(now)
            cache.set(cache_key, requests, window_seconds)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

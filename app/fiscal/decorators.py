"""
Decoradores de seguridad para el módulo fiscal.

Proporcionan control de acceso a nivel de función/vista.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from app.fiscal.models.audit_log import FiscalAuditLog


def require_fiscal_permission(permission):
    """
    Decorador que requiere un permiso fiscal específico.
    
    Args:
        permission: Nombre del permiso (sin prefijo 'fiscal.')
    
    Examples:
        @require_fiscal_permission('change_fiscal_data')
        def update_perfil(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar permiso
            full_permission = f'fiscal.{permission}'
            
            if not request.user.has_perm(full_permission):
                raise PermissionDenied(
                    f"Requiere permiso: {full_permission}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def audit_fiscal_action(action, model_name):
    """
    Decorador que audita automáticamente una acción fiscal.
    
    Args:
        action: Tipo de acción (VIEW, CREATE, UPDATE, DELETE, EXPORT)
        model_name: Nombre del modelo
    
    Examples:
        @audit_fiscal_action('VIEW', 'PerfilFiscal')
        def view_perfil(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Ejecutar vista
            response = view_func(request, *args, **kwargs)
            
            # Auditar acción
            try:
                object_id = kwargs.get('pk', kwargs.get('id', 'N/A'))
                
                FiscalAuditLog.log_action(
                    action=action,
                    model_name=model_name,
                    object_id=object_id,
                    user=request.user,
                    request=request,
                    success=True
                )
            except Exception as e:
                # No fallar la vista si falla la auditoría
                import logging
                logger = logging.getLogger('fiscal_audit')
                logger.error(f"Failed to audit action: {e}")
            
            return response
        
        return wrapper
    return decorator


def require_staff_or_owner(get_object_func):
    """
    Decorador que requiere ser staff o dueño del objeto.
    
    Args:
        get_object_func: Función que obtiene el objeto desde request/args/kwargs
    
    Examples:
        def get_perfil(request, pk):
            return PerfilFiscal.objects.get(pk=pk)
        
        @require_staff_or_owner(get_perfil)
        def update_perfil(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Obtener objeto
            obj = get_object_func(request, *args, **kwargs)
            
            # Verificar permisos
            is_staff = request.user.is_staff or request.user.is_superuser
            is_owner = (
                hasattr(obj, 'created_by') and
                obj.created_by == request.user
            )
            
            if not (is_staff or is_owner):
                raise PermissionDenied(
                    "Solo el creador o staff puede acceder a este recurso"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_fiscal(max_requests=100, window_seconds=60):
    """
    Decorador de rate limiting para endpoints fiscales.
    
    Args:
        max_requests: Máximo de requests permitidos
        window_seconds: Ventana de tiempo en segundos
    
    Examples:
        @rate_limit_fiscal(max_requests=50, window_seconds=60)
        def export_data(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            
            # Generar cache key por usuario
            cache_key = f'fiscal_rate_limit_{request.user.id}'
            
            # Obtener contador actual
            current_count = cache.get(cache_key, 0)
            
            # Verificar límite
            if current_count >= max_requests:
                raise PermissionDenied(
                    f"Rate limit excedido. Máximo {max_requests} "
                    f"requests por {window_seconds} segundos."
                )
            
            # Incrementar contador
            cache.set(cache_key, current_count + 1, window_seconds)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

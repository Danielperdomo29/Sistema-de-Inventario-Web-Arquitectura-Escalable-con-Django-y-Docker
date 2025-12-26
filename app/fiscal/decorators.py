"""
Decoradores de seguridad para vistas fiscales.

Proporcionan control de acceso a nivel de función/método.
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
        >>> @require_fiscal_permission('change_fiscal')
        >>> def update_perfil_fiscal(request, pk):
        ...     # Solo usuarios con fiscal.change_fiscal pueden acceder
        ...     pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar permiso
            full_permission = f'fiscal.{permission}'
            
            if not request.user.has_perm(full_permission):
                # Auditar intento de acceso no autorizado
                FiscalAuditLog.log_action(
                    action='VIEW',
                    model_name='Permission',
                    object_id=permission,
                    user=request.user,
                    request=request,
                    success=False,
                    error_message=f'Permission denied: {full_permission}'
                )
                
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
        action: Tipo de acción (CREATE, UPDATE, DELETE, VIEW, EXPORT)
        model_name: Nombre del modelo
    
    Examples:
        >>> @audit_fiscal_action('EXPORT', 'PerfilFiscal')
        >>> def export_perfiles(request):
        ...     # La exportación se auditará automáticamente
        ...     pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Ejecutar la vista
            try:
                result = view_func(request, *args, **kwargs)
                success = True
                error_message = ''
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # Auditar la acción
                object_id = kwargs.get('pk', kwargs.get('id', 'N/A'))
                
                if request.user.is_authenticated:
                    FiscalAuditLog.log_action(
                        action=action,
                        model_name=model_name,
                        object_id=object_id,
                        user=request.user,
                        request=request,
                        success=success,
                        error_message=error_message
                    )
            
            return result
        
        return wrapper
    return decorator


def require_staff_or_owner(get_object_func):
    """
    Decorador que requiere que el usuario sea staff o dueño del objeto.
    
    Args:
        get_object_func: Función que retorna el objeto a verificar
    
    Examples:
        >>> def get_perfil(request, pk):
        ...     return PerfilFiscal.objects.get(pk=pk)
        >>> 
        >>> @require_staff_or_owner(get_perfil)
        >>> def update_perfil(request, pk):
        ...     # Solo staff o creador pueden modificar
        ...     pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Obtener el objeto
            obj = get_object_func(request, *args, **kwargs)
            
            # Verificar si es staff o dueño
            is_owner = (
                hasattr(obj, 'created_by') and
                obj.created_by == request.user
            )
            
            if not (request.user.is_staff or is_owner):
                raise PermissionDenied(
                    "Solo el creador o staff pueden modificar este objeto"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class fiscal_permission_required:
    """
    Decorador de clase para requerir múltiples permisos fiscales.
    
    Examples:
        >>> @fiscal_permission_required(['view_fiscal', 'export_fiscal'])
        >>> def export_all_data(request):
        ...     # Requiere ambos permisos
        ...     pass
    """
    
    def __init__(self, permissions):
        """
        Args:
            permissions: Lista de permisos requeridos (sin prefijo 'fiscal.')
        """
        if isinstance(permissions, str):
            permissions = [permissions]
        
        self.permissions = [f'fiscal.{p}' for p in permissions]
    
    def __call__(self, view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar todos los permisos
            missing_perms = [
                perm for perm in self.permissions
                if not request.user.has_perm(perm)
            ]
            
            if missing_perms:
                raise PermissionDenied(
                    f"Faltan permisos: {', '.join(missing_perms)}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper

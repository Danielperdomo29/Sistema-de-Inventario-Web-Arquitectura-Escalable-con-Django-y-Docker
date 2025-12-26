"""
Permisos personalizados para el módulo fiscal.

Define permisos granulares para operaciones sobre datos fiscales.
"""
from rest_framework import permissions


class FiscalDataPermission(permissions.BasePermission):
    """
    Permisos granulares para datos fiscales.
    
    Niveles de permisos:
    - fiscal.view_fiscal: Ver datos fiscales
    - fiscal.add_fiscal: Crear datos fiscales
    - fiscal.change_fiscal: Modificar datos fiscales
    - fiscal.delete_fiscal: Eliminar datos fiscales
    - fiscal.audit_fiscal: Ver logs de auditoría
    - fiscal.export_fiscal: Exportar datos fiscales
    
    Examples:
        >>> # En una vista DRF
        >>> class PerfilFiscalViewSet(viewsets.ModelViewSet):
        ...     permission_classes = [FiscalDataPermission]
    """
    
    def has_permission(self, request, view):
        """
        Verifica si el usuario tiene permiso para la acción.
        
        Args:
            request: Request de Django
            view: Vista actual
        
        Returns:
            bool: True si tiene permiso
        """
        # Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios tienen todos los permisos
        if request.user.is_superuser:
            return True
        
        # Mapear métodos HTTP a permisos
        if request.method in permissions.SAFE_METHODS:
            # GET, HEAD, OPTIONS
            return request.user.has_perm('fiscal.view_fiscal')
        
        if request.method == 'POST':
            return request.user.has_perm('fiscal.add_fiscal')
        
        if request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('fiscal.change_fiscal')
        
        if request.method == 'DELETE':
            return request.user.has_perm('fiscal.delete_fiscal')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permisos a nivel de objeto.
        
        Args:
            request: Request de Django
            view: Vista actual
            obj: Objeto específico
        
        Returns:
            bool: True si tiene permiso sobre el objeto
        """
        # Superusuarios tienen acceso total
        if request.user.is_superuser:
            return True
        
        # Lectura: cualquiera con permiso view_fiscal
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm('fiscal.view_fiscal')
        
        # Modificación/eliminación: solo staff o creador
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Verificar si el objeto tiene campo created_by
            if hasattr(obj, 'created_by'):
                return (
                    request.user.is_staff or
                    obj.created_by == request.user
                )
            
            # Si no tiene created_by, solo staff puede modificar
            return request.user.is_staff
        
        return False


class AuditLogPermission(permissions.BasePermission):
    """
    Permisos específicos para logs de auditoría.
    
    Solo usuarios con permiso audit_fiscal pueden ver logs.
    """
    
    def has_permission(self, request, view):
        """Verifica permiso para ver audit logs"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.has_perm('fiscal.audit_fiscal')


class ExportDataPermission(permissions.BasePermission):
    """
    Permisos para exportar datos fiscales.
    
    Requiere permiso especial export_fiscal.
    """
    
    def has_permission(self, request, view):
        """Verifica permiso para exportar datos"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.has_perm('fiscal.export_fiscal')

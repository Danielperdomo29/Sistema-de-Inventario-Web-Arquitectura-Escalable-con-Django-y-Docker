"""
Permisos personalizados para el módulo fiscal.

Define permisos granulares para operaciones sobre datos fiscales.
"""
from rest_framework import permissions


class FiscalDataPermission(permissions.BasePermission):
    """
    Permisos granulares para datos fiscales.
    
    Niveles de permiso:
    - fiscal.view_fiscal_data: Ver datos fiscales
    - fiscal.add_fiscal_data: Crear datos fiscales
    - fiscal.change_fiscal_data: Modificar datos fiscales
    - fiscal.delete_fiscal_data: Eliminar datos fiscales
    - fiscal.audit_fiscal_data: Ver logs de auditoría
    - fiscal.export_fiscal_data: Exportar datos fiscales
    """
    
    def has_permission(self, request, view):
        """
        Verifica permisos a nivel de vista.
        
        Args:
            request: Request de Django
            view: Vista siendo accedida
        
        Returns:
            bool: True si tiene permiso
        """
        # Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios tienen acceso total
        if request.user.is_superuser:
            return True
        
        # Verificar permisos según método HTTP
        if request.method in permissions.SAFE_METHODS:
            # GET, HEAD, OPTIONS
            return request.user.has_perm('fiscal.view_fiscal_data')
        
        elif request.method == 'POST':
            return request.user.has_perm('fiscal.add_fiscal_data')
        
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('fiscal.change_fiscal_data')
        
        elif request.method == 'DELETE':
            return request.user.has_perm('fiscal.delete_fiscal_data')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permisos a nivel de objeto.
        
        Args:
            request: Request de Django
            view: Vista siendo accedida
            obj: Objeto siendo accedido
        
        Returns:
            bool: True si tiene permiso
        """
        # Superusuarios tienen acceso total
        if request.user.is_superuser:
            return True
        
        # Lectura: cualquiera con permiso view
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm('fiscal.view_fiscal_data')
        
        # Modificación/Eliminación: verificar ownership o staff
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Staff puede modificar todo
            if request.user.is_staff:
                return request.user.has_perm('fiscal.change_fiscal_data')
            
            # Usuarios normales solo sus propios datos
            # (si el modelo tiene created_by)
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
        
        return False


class AuditLogPermission(permissions.BasePermission):
    """
    Permisos para acceder a logs de auditoría.
    
    Solo usuarios con permiso especial pueden ver auditoría.
    """
    
    def has_permission(self, request, view):
        """Verifica permiso para ver auditoría"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Solo lectura permitida en auditoría
        if request.method not in permissions.SAFE_METHODS:
            return False
        
        # Requiere permiso especial
        return (
            request.user.is_superuser or
            request.user.has_perm('fiscal.audit_fiscal_data')
        )


class ExportPermission(permissions.BasePermission):
    """
    Permisos para exportar datos fiscales.
    
    Exportación requiere permiso especial por sensibilidad de datos.
    """
    
    def has_permission(self, request, view):
        """Verifica permiso para exportar"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_superuser or
            request.user.has_perm('fiscal.export_fiscal_data')
        )

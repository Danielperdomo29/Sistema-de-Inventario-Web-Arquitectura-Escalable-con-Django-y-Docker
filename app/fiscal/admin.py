"""
Configuración del Django Admin para el módulo fiscal.

Registra todos los modelos fiscales con interfaces personalizadas.
"""
from django.contrib import admin
from app.fiscal.models import (
    CuentaContable,
    Impuesto,
    PerfilFiscal,
    FiscalAuditLog,
)


@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    """Admin para Plan Único de Cuentas (PUC)."""
    
    list_display = ('codigo', 'nombre', 'nivel', 'naturaleza', 'tipo', 'acepta_movimiento', 'activa')
    list_filter = ('nivel', 'naturaleza', 'tipo', 'acepta_movimiento', 'activa')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion')
        }),
        ('Clasificación', {
            'fields': ('nivel', 'naturaleza', 'tipo', 'padre')
        }),
        ('Estado', {
            'fields': ('acepta_movimiento', 'activa')
        }),
    )
    
    readonly_fields = ('nivel',)
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('padre')


@admin.register(Impuesto)
class ImpuestoAdmin(admin.ModelAdmin):
    """Admin para configuración de impuestos."""
    
    list_display = ('codigo', 'nombre', 'tipo', 'porcentaje', 'aplica_ventas', 'aplica_compras', 'activo')
    list_filter = ('tipo', 'aplica_ventas', 'aplica_compras', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'tipo')
        }),
        ('Configuración', {
            'fields': ('porcentaje', 'base_minima', 'cuenta_por_pagar')
        }),
        ('Aplicabilidad', {
            'fields': ('aplica_ventas', 'aplica_compras', 'activo')
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('cuenta_por_pagar')


@admin.register(PerfilFiscal)
class PerfilFiscalAdmin(admin.ModelAdmin):
    """Admin para perfiles fiscales de clientes/proveedores."""
    
    list_display = ('get_nombre', 'tipo_documento', 'numero_documento', 'dv', 'regimen', 'tipo_persona')
    list_filter = ('tipo_documento', 'tipo_persona', 'regimen')
    search_fields = ('numero_documento', 'nombre_comercial', 'razon_social')
    ordering = ('numero_documento',)
    
    fieldsets = (
        ('Entidad Relacionada', {
            'fields': ('cliente', 'proveedor')
        }),
        ('Identificación Fiscal', {
            'fields': ('tipo_documento', 'numero_documento', 'dv', 'tipo_persona')
        }),
        ('Información Comercial', {
            'fields': ('nombre_comercial', 'regimen', 'responsabilidades')
        }),
        ('Ubicación', {
            'fields': ('departamento_codigo', 'municipio_codigo', 'direccion')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email_facturacion')
        }),
    )
    
    readonly_fields = ('dv',)
    
    def get_nombre(self, obj):
        """Mostrar nombre completo en listado."""
        return obj.get_nombre_completo()
    get_nombre.short_description = 'Nombre'
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('cliente', 'proveedor')


@admin.register(FiscalAuditLog)
class FiscalAuditLogAdmin(admin.ModelAdmin):
    """Admin para logs de auditoría fiscal."""
    
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'user_ip')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'object_id', 'user_ip', 'changes')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información de Auditoría', {
            'fields': ('timestamp', 'user', 'action', 'model_name', 'object_id')
        }),
        ('Detalles', {
            'fields': ('changes', 'user_ip', 'user_agent')
        }),
    )
    
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'changes', 'user_ip', 'user_agent')
    
    def has_add_permission(self, request):
        """No permitir crear logs manualmente."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar logs (retención 7 años DIAN)."""
        return False
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


# Personalizar el sitio de admin
admin.site.site_header = "Sistema de Inventario - Administración"
admin.site.site_title = "Admin Inventario"
admin.site.index_title = "Panel de Administración"

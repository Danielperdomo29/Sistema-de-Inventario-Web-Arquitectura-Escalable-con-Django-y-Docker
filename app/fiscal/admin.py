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
    RangoNumeracion,
    FiscalConfig,
    FacturaElectronica,
    EventoDian,
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


@admin.register(RangoNumeracion)
class RangoNumeracionAdmin(admin.ModelAdmin):
    """Admin para rangos de numeración DIAN."""
    
    list_display = ('prefijo', 'numero_resolucion', 'consecutivo_actual', 'estado', 'numeros_disponibles', 'porcentaje_uso_display', 'is_default')
    list_filter = ('estado', 'is_default', 'fiscal_config')
    search_fields = ('prefijo', 'numero_resolucion')
    ordering = ('-is_default', '-fecha_inicio_vigencia')
    date_hierarchy = 'fecha_inicio_vigencia'
    
    fieldsets = (
        ('Configuración Fiscal', {
            'fields': ('fiscal_config', 'is_default')
        }),
        ('Resolución DIAN', {
            'fields': ('numero_resolucion', 'fecha_resolucion', 'fecha_inicio_vigencia', 'fecha_fin_vigencia')
        }),
        ('Rango de Numeración', {
            'fields': ('prefijo', 'rango_desde', 'rango_hasta', 'consecutivo_actual')
        }),
        ('Seguridad', {
            'fields': ('clave_tecnica',)
        }),
        ('Estado y Alertas', {
            'fields': ('estado', 'porcentaje_alerta', 'alerta_enviada')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('estado',)
    
    def numeros_disponibles(self, obj):
        """Muestra números disponibles."""
        disponibles = obj.numeros_disponibles
        if disponibles < 100:
            return f"⚠️ {disponibles}"
        return disponibles
    numeros_disponibles.short_description = 'Disponibles'
    
    def porcentaje_uso_display(self, obj):
        """Muestra porcentaje de uso con indicador."""
        porcentaje = obj.porcentaje_uso
        if porcentaje >= 90:
            return f"🔴 {porcentaje:.1f}%"
        elif porcentaje >= 70:
            return f"🟡 {porcentaje:.1f}%"
        else:
            return f"🟢 {porcentaje:.1f}%"
    porcentaje_uso_display.short_description = 'Uso'


@admin.register(FiscalConfig)
class FiscalConfigAdmin(admin.ModelAdmin):
    """Admin para configuración fiscal DIAN."""
    
    list_display = ('nit_emisor', 'razon_social', 'get_ambiente_display', 'is_active', 'updated_at')
    list_filter = ('ambiente', 'is_active')
    search_fields = ('nit_emisor', 'razon_social', 'software_id')
    
    fieldsets = (
        ('Emisor', {
            'fields': ('nit_emisor', 'dv_emisor', 'razon_social')
        }),
        ('Proveedor Tecnológico', {
            'fields': ('software_id', 'pin_software')
        }),
        ('Ambiente', {
            'fields': ('ambiente', 'test_set_id')
        }),
        ('Resolución de Facturación', {
            'fields': ('numero_resolucion', 'fecha_resolucion', 'prefijo', 'rango_desde', 'rango_hasta', 'clave_tecnica')
        }),
        ('Certificado Digital', {
            'fields': ('certificado_archivo', '_certificado_password')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevenir eliminación accidental de configuración activa."""
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(FacturaElectronica)
class FacturaElectronicaAdmin(admin.ModelAdmin):
    """Admin para facturas electrónicas."""
    
    list_display = ('numero_factura', 'venta', 'cufe_display', 'estado', 'ambiente', 'fecha_creacion')
    list_filter = ('estado', 'ambiente', 'fecha_creacion')
    search_fields = ('numero_factura', 'cufe', 'venta__id')
    ordering = ('-fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Venta', {
            'fields': ('venta',)
        }),
        ('Factura', {
            'fields': ('numero_factura', 'prefijo', 'cufe')
        }),
        ('Archivos', {
            'fields': ('archivo_xml', 'archivo_pdf')
        }),
        ('Estado', {
            'fields': ('estado', 'ambiente')
        }),
    )
    
    readonly_fields = ('numero_factura', 'cufe', 'fecha_creacion')
    
    def cufe_display(self, obj):
        """Muestra CUFE abreviado."""
        if obj.cufe:
            return f"{obj.cufe[:16]}..."
        return "-"
    cufe_display.short_description = 'CUFE'
    
    def has_add_permission(self, request):
        """No permitir crear facturas manualmente."""
        return False


@admin.register(EventoDian)
class EventoDianAdmin(admin.ModelAdmin):
    """Admin para eventos DIAN."""
    
    list_display = ('factura', 'codigo_evento', 'es_error', 'fecha_evento')
    list_filter = ('es_error', 'codigo_evento', 'fecha_evento')
    search_fields = ('factura__numero_factura', 'codigo_evento', 'descripcion')
    ordering = ('-fecha_evento',)
    
    readonly_fields = ('fecha_evento',)
    
    fieldsets = (
        ('Factura', {
            'fields': ('factura',)
        }),
        ('Evento', {
            'fields': ('codigo_evento', 'descripcion', 'es_error')
        }),
        ('Datos', {
            'fields': ('xml_evento', 'detalles')
        }),
        ('Fecha', {
            'fields': ('fecha_evento',)
        }),
    )


# Personalizar el sitio de admin
admin.site.site_header = "Sistema de Inventario - Administración"
admin.site.site_title = "Admin Inventario"
admin.site.index_title = "Panel de Administración"

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from app.controllers.auth_controller import AuthController
from app.controllers.category_controller import CategoryController
from app.controllers.chatbot_controller import ChatbotController
from app.controllers.client_controller import ClientController
from app.controllers.config_controller import ConfigController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.documentation_controller import DocumentationController
from app.controllers.fiscal_controller import FiscalController
from app.controllers.inventory_movement_controller import InventoryMovementController
from app.controllers.product_controller import ProductController
from app.controllers.purchase_controller import PurchaseController
from app.controllers.purchase_detail_controller import PurchaseDetailController
from app.controllers.report_controller import ReportController
from app.controllers.role_controller import RoleController
from app.controllers.sale_controller import SaleController
from app.controllers.sale_detail_controller import SaleDetailController
from app.controllers.supplier_controller import SupplierController
from app.controllers.dian_invoice_controller import DianInvoiceController
from app.controllers.warehouse_controller import WarehouseController

# URLs del sistema de inventario (existentes - sin cambios)
urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Dashboard y autenticación
    path("", DashboardController.index, name="dashboard"),
    path("login/", AuthController.login, name="login"),
    path("register/", AuthController.register, name="register"),
    path("logout/", AuthController.logout, name="logout"),
    path("productos/", ProductController.index, name="products"),
    path("productos/crear/", ProductController.create, name="products_create"),
    path("productos/<int:product_id>/editar/", ProductController.edit, name="products_edit"),
    path("productos/<int:product_id>/eliminar/", ProductController.delete, name="products_delete"),
    path("categorias/", CategoryController.index, name="categories"),
    path("categorias/crear/", CategoryController.create, name="categories_create"),
    path("categorias/<int:category_id>/editar/", CategoryController.edit, name="categories_edit"),
    path(
        "categorias/<int:category_id>/eliminar/",
        CategoryController.delete,
        name="categories_delete",
    ),
    path("clientes/", ClientController.index, name="clients"),
    path("clientes/crear/", ClientController.create, name="clients_create"),
    path("clientes/<int:client_id>/editar/", ClientController.edit, name="clients_edit"),
    path("clientes/<int:client_id>/eliminar/", ClientController.delete, name="clients_delete"),
    path("proveedores/", SupplierController.index, name="suppliers"),
    path("proveedores/crear/", SupplierController.create, name="suppliers_create"),
    path("proveedores/<int:supplier_id>/editar/", SupplierController.edit, name="suppliers_edit"),
    path(
        "proveedores/<int:supplier_id>/eliminar/",
        SupplierController.delete,
        name="suppliers_delete",
    ),
    path("roles/", RoleController.index, name="roles"),
    path("roles/crear/", RoleController.create, name="roles_create"),
    path("roles/<int:role_id>/editar/", RoleController.edit, name="roles_edit"),
    path("roles/<int:role_id>/eliminar/", RoleController.delete, name="roles_delete"),
    path("almacenes/", WarehouseController.index, name="warehouses"),
    path("almacenes/crear/", WarehouseController.create, name="warehouses_create"),
    path("almacenes/<int:warehouse_id>/editar/", WarehouseController.edit, name="warehouses_edit"),
    path(
        "almacenes/<int:warehouse_id>/eliminar/",
        WarehouseController.delete,
        name="warehouses_delete",
    ),
    # Ventas
    path("ventas/", SaleController.index, name="sales"),
    path("ventas/crear/", SaleController.create, name="sales_create"),
    path("ventas/<int:sale_id>/editar/", SaleController.edit, name="sales_edit"),
    path("ventas/<int:sale_id>/eliminar/", SaleController.delete, name="sales_delete"),
    path("ventas/<int:sale_id>/ver/", SaleController.view, name="sales_detail"),  # NEW: Added for /ventas/{id}/ver/
    # Solicitud del usuario: URL de detalle de ventas (alias)
    path("detalle-ventas/<int:sale_id>/ver/", SaleController.view, name="sales_view"),
    
    # DIAN - Facturación Electrónica
    path("dian/generar/<int:sale_id>/", DianInvoiceController.generate_invoice, name="dian_generate_invoice"),
    path("dian/pdf/<int:sale_id>/", DianInvoiceController.download_pdf, name="dian_download_pdf"),
    path("dian/xml/<int:sale_id>/", DianInvoiceController.download_xml, name="dian_download_xml"),

    # Detalle de Ventas (Items individuales)
    path("items-venta/", SaleDetailController.index, name="sale_details"),
    path("items-venta/crear/", SaleDetailController.create, name="sale_details_create"),
    path(
        "items-venta/<int:detail_id>/editar/",
        SaleDetailController.edit,
        name="sale_details_edit",
    ),
    path(
        "items-venta/<int:detail_id>/eliminar/",
        SaleDetailController.delete,
        name="sale_details_delete",
    ),
    path(
        "items-venta/<int:detail_id>/ver/", SaleDetailController.view, name="sale_details_view"
    ),
    path("compras/", PurchaseController.index, name="purchases"),
    path("compras/crear/", PurchaseController.create, name="purchases_create"),
    path("compras/<int:purchase_id>/editar/", PurchaseController.edit, name="purchases_edit"),
    path("compras/<int:purchase_id>/eliminar/", PurchaseController.delete, name="purchases_delete"),
    path("compras/<int:purchase_id>/ver/", PurchaseController.view, name="purchases_view"),
    path("detalle-compras/", PurchaseDetailController.index, name="purchase_details"),
    path("detalle-compras/crear/", PurchaseDetailController.create, name="purchase_details_create"),
    path(
        "detalle-compras/<int:detail_id>/editar/",
        PurchaseDetailController.edit,
        name="purchase_details_edit",
    ),
    path(
        "detalle-compras/<int:detail_id>/eliminar/",
        PurchaseDetailController.delete,
        name="purchase_details_delete",
    ),
    path(
        "detalle-compras/<int:detail_id>/ver/",
        PurchaseDetailController.view,
        name="purchase_details_view",
    ),
    path("movimientos-inventario/", InventoryMovementController.index, name="inventory_movements"),
    path(
        "movimientos-inventario/crear/",
        InventoryMovementController.create,
        name="inventory_movements_create",
    ),
    path(
        "movimientos-inventario/<int:movement_id>/editar/",
        InventoryMovementController.edit,
        name="inventory_movements_edit",
    ),
    path(
        "movimientos-inventario/<int:movement_id>/eliminar/",
        InventoryMovementController.delete,
        name="inventory_movements_delete",
    ),
    path(
        "movimientos-inventario/<int:movement_id>/ver/",
        InventoryMovementController.view,
        name="inventory_movements_view",
    ),
    path("reportes/", ReportController.index, name="reports"),
    path("documentacion/", DocumentationController.index, name="documentation"),
    path("configuracion/", ConfigController.index, name="config"),
    path("configuracion/perfil/editar/", ConfigController.edit_profile, name="config_edit_profile"),
    path(
        "configuracion/perfil/cambiar-password/",
        ConfigController.change_password,
        name="config_change_password",
    ),
    path("configuracion/usuarios/crear/", ConfigController.create_user, name="config_create_user"),
    path(
        "configuracion/usuarios/<int:user_edit_id>/editar/",
        ConfigController.edit_user,
        name="config_edit_user",
    ),
    path(
        "configuracion/usuarios/<int:user_delete_id>/eliminar/",
        ConfigController.delete_user,
        name="config_delete_user",
    ),
    # Chatbot con IA
    path("chatbot/", ChatbotController.index, name="chatbot"),
    path("chatbot/send/", ChatbotController.send_message, name="chatbot_send"),
    path("chatbot/clear-history/", ChatbotController.clear_history, name="chatbot_clear_history"),
    path("chatbot/history/", ChatbotController.get_history, name="chatbot_history"),
    # Analytics con IA (DeepSeek)
    path("analytics/", include("app.views.analytics_urls")),
    # Módulo Fiscal - Fase A
    path("fiscal/", FiscalController.index, name="fiscal"),
    path("fiscal/perfiles/", FiscalController.perfiles_fiscales, name="fiscal_perfiles"),
    path("fiscal/perfiles/crear/", FiscalController.perfil_fiscal_crear, name="fiscal_perfil_crear"),
    path("fiscal/perfiles/<int:perfil_id>/editar/", FiscalController.perfil_fiscal_editar, name="fiscal_perfil_editar"),
    path("fiscal/cuentas-puc/", FiscalController.cuentas_puc, name="fiscal_cuentas_puc"),
    path("fiscal/impuestos/", FiscalController.impuestos, name="fiscal_impuestos"),
    # DIAN
    path("dian/", include("facturacion.urls")),
    # API Fiscal & Reportes
    path("fiscal/", include("app.fiscal.urls")),
]

# Django-Allauth & 2FA URLs
urlpatterns += [
    path("accounts/", include("allauth_2fa.urls")), # Include 2FA urls before allauth urls
    path("accounts/", include("allauth.urls")),
]

# Debug Toolbar (DEBE IR PRIMERO en desarrollo)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

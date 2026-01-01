from django.urls import path
from . import views
from . import views_config

urlpatterns = [
    # === INTEGRACION & PRUEBAS ===
    path('test-integracion/', views.test_integracion, name='test_integracion'),
    
    # === REPORTES FISCALES ===
    path('reportes/libro-diario/', views.libro_diario, name='libro_diario'),
    path('reportes/balance-prueba/', views.balance_prueba, name='balance_prueba'),
    path('reportes/estado-resultados/', views.estado_resultados, name='estado_resultados'),
    path('reportes/libro-mayor/', views.libro_mayor, name='libro_mayor'),
    
    # === CIERRE CONTABLE ===
    path('cierre/ejecutar/', views.ejecutar_cierre, name='ejecutar_cierre'),
    path('cierre/verificar/', views.verificar_cierre, name='verificar_cierre'),
    
    # === DATA & RESUMEN ===
    path('dashboard/resumen/', views.dashboard_resumen, name='dashboard_resumen'),

    # === FACTURACIÓN ELECTRÓNICA ===
    path('api/validar-xml/', views.validar_xml, name='validar_xml'),

    # === DECLARACIÓN DE IVA (FORMULARIO 300) ===
    path('reportes/declaracion-iva/', views.declaracion_iva, name='declaracion_iva'),
    path('reportes/declaracion-iva/detalle/', views.declaracion_iva_detalle, name='declaracion_iva_detalle'),
    path('reportes/declaracion-iva/export/', views.declaracion_iva_export, name='declaracion_iva_export'),

    # === RETENCIÓN EN LA FUENTE (FORMULARIO 350) ===
    path('reportes/declaracion-retefuente/', views.declaracion_retefuente, name='declaracion_retefuente'),
    path('reportes/declaracion-retefuente/detalle/', views.declaracion_retefuente_detalle, name='declaracion_retefuente_detalle'),
    path('reportes/declaracion-retefuente/export/', views.declaracion_retefuente_export, name='declaracion_retefuente_export'),
    path('reportes/declaracion-retefuente/resumen-anual/', views.declaracion_retefuente_resumen_anual, name='declaracion_retefuente_resumen_anual'),
    
    # === CONFIGURACIÓN ===
    path('configuracion/', views_config.configuracion_fiscal, name='configuracion_fiscal'),
]

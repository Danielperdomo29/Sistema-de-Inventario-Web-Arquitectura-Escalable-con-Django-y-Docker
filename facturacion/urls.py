from django.urls import path
from . import views

urlpatterns = [
    path('generar/<int:sale_id>/', views.generar_factura_dian, name='generar_factura_dian'),
]

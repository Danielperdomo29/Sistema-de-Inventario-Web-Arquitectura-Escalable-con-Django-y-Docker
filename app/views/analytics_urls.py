"""
URLs para el módulo de Analytics con IA.
"""

from django.urls import path

from app.views.analytics_view import (
    analytics_dashboard,
    generate_summary,
    ask_question,
    get_sales_data,
    get_inventory_data,
)

urlpatterns = [
    path("", analytics_dashboard, name="analytics"),
    path("generate-summary/", generate_summary, name="analytics_generate_summary"),
    path("ask/", ask_question, name="analytics_ask"),
    path("sales-data/", get_sales_data, name="analytics_sales_data"),
    path("inventory-data/", get_inventory_data, name="analytics_inventory_data"),
]

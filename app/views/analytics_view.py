"""
Vista de Analytics con IA.
Dashboard de análisis inteligente usando DeepSeek.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from app.services.analytics_service import get_analytics_service


@login_required
def analytics_dashboard(request):
    """
    Vista principal del dashboard de analytics.
    Muestra estadísticas y permite consultas con IA.
    """
    try:
        analytics = get_analytics_service()
        quick_stats = analytics.get_quick_stats()
    except Exception as e:
        quick_stats = {
            "error": str(e),
            "ventas_hoy_total": 0,
            "ventas_hoy_cantidad": 0,
            "productos_stock_bajo": 0,
        }

    context = {
        "title": "Analytics IA",
        "quick_stats": quick_stats,
    }
    return render(request, "analytics.html", context)


@login_required
@require_http_methods(["POST"])
def generate_summary(request):
    """
    API endpoint para generar resumen ejecutivo con IA.
    """
    try:
        analytics = get_analytics_service()
        summary = analytics.generate_daily_summary()
        return JsonResponse({
            "success": True,
            "summary": summary,
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ask_question(request):
    """
    API endpoint para consultas en lenguaje natural.
    """
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        
        if not question:
            return JsonResponse({
                "success": False,
                "error": "Por favor, ingresa una pregunta.",
            }, status=400)

        analytics = get_analytics_service()
        answer = analytics.answer_question(question)
        
        return JsonResponse({
            "success": True,
            "question": question,
            "answer": answer,
        })
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Formato de solicitud inválido.",
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
        }, status=500)


@login_required
def get_sales_data(request):
    """
    API endpoint para obtener datos de ventas (sin IA).
    """
    try:
        analytics = get_analytics_service()
        data = analytics.get_sales_data()
        return JsonResponse({
            "success": True,
            "data": data,
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
        }, status=500)


@login_required
def get_inventory_data(request):
    """
    API endpoint para obtener datos de inventario (sin IA).
    """
    try:
        analytics = get_analytics_service()
        data = analytics.get_inventory_summary()
        return JsonResponse({
            "success": True,
            "data": data,
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
        }, status=500)

"""
Celery tasks para generación de reportes
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Count, F
import time


@shared_task(name='generate_monthly_report')
def generate_monthly_report(year, month):
    """
    Genera reporte mensual de ventas (tarea pesada)
    
    Usage:
        # Async
        task = generate_monthly_report.delay(2024, 1)
        
        # Sync (para testing)
        result = generate_monthly_report(2024, 1)
    
    Args:
        year: Año del reporte
        month: Mes del reporte (1-12)
    
    Returns:
        dict: Resumen del reporte con totales
    """
    from app.models.sale import Sale
    
    # Simular procesamiento pesado
    time.sleep(2)
    
    # Calcular ventas del mes
    sales = Sale.objects.filter(
        fecha__year=year,
        fecha__month=month
    ).select_related('cliente', 'usuario')
    
    # Aggregates
    stats = sales.aggregate(
        total_sales=Sum('total'),
        count=Count('id'),
        avg_sale=Sum('total') / Count('id') if sales.count() > 0 else 0
    )
    
    # Top productos (si hay detalles)
    try:
        from app.models.sale_detail import SaleDetail
        top_products = SaleDetail.objects.filter(
            venta__fecha__year=year,
            venta__fecha__month=month
        ).values('producto__nombre').annotate(
            total_qty=Sum('cantidad'),
            total_revenue=Sum(F('precio_unitario') * F('cantidad'))
        ).order_by('-total_revenue')[:5]
        
        top_products_list = list(top_products)
    except:
        top_products_list = []
    
    return {
        'year': year,
        'month': month,
        'total_sales': float(stats['total_sales'] or 0),
        'count': stats['count'],
        'avg_sale': float(stats['avg_sale'] or 0),
        'top_products': top_products_list,
        'generated_at': str(timezone.now())
    }


@shared_task(name='check_low_stock')
def check_low_stock():
    """
    Verifica productos con stock bajo
    Ejecutar diariamente con Celery Beat
    
    Usage:
        # Ejecutar manualmente
        task = check_low_stock.delay()
        
        # Con Celery Beat (en settings.py):
        CELERY_BEAT_SCHEDULE = {
            'check-low-stock-daily': {
                'task': 'check_low_stock',
                'schedule': crontab(hour=8, minute=0),  # 8am diario
            },
        }
    
    Returns:
        dict: Productos con stock bajo
    """
    from app.models.product import Product
    
    low_stock = Product.objects.filter(
        stock_actual__lte=F('stock_minimo'),
        activo=True
    ).select_related('categoria')
    
    products_data = []
    for product in low_stock:
        products_data.append({
            'id': product.id,
            'codigo': product.codigo,
            'nombre': product.nombre,
            'categoria': product.categoria.nombre if product.categoria else None,
            'stock_actual': product.stock_actual,
            'stock_minimo': product.stock_minimo,
            'deficit': product.stock_minimo - product.stock_actual
        })
    
    return {
        'products_count': len(products_data),
        'products': products_data,
        'checked_at': str(timezone.now())
    }


@shared_task(name='generate_daily_summary')
def generate_daily_summary(date_str=None):
    """
    Genera resumen diario de ventas
    
    Args:
        date_str: Fecha en formato 'YYYY-MM-DD' (default: hoy)
    
    Returns:
        dict: Resumen del día
    """
    from app.models.sale import Sale
    from datetime import datetime
    
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = timezone.now().date()
    
    sales = Sale.objects.filter(
        fecha__date=target_date
    )
    
    stats = sales.aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    
    return {
        'date': str(target_date),
        'total_sales': float(stats['total'] or 0),
        'sales_count': stats['count'],
        'avg_sale': float((stats['total'] or 0) / stats['count']) if stats['count'] > 0 else 0,
        'generated_at': str(timezone.now())
    }

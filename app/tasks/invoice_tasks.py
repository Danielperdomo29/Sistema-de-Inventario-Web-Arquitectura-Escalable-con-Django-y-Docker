"""
Celery tasks para facturación y procesos batch
"""
from celery import shared_task
from django.utils import timezone


@shared_task(name='batch_generate_invoices')
def batch_generate_invoices(sale_ids):
    """
    Genera facturas en batch (no bloquea UI)
    
    Usage:
        # Generar facturas para múltiples ventas
        task = batch_generate_invoices.delay([1, 2, 3, 4, 5])
        
        # Verificar resultado
        from celery.result import AsyncResult
        task_result = AsyncResult(task.id)
        if task_result.ready():
            results = task_result.result
    
    Args:
        sale_ids: Lista de IDs de ventas para procesar
    
    Returns:
        list: Resultados de cada factura generada
    """
    from app.models.sale import Sale
    
    results = []
    
    for sale_id in sale_ids:
        try:
            sale = Sale.objects.get(id=sale_id)
            
            # Aquí iría la lógica real de generación de factura
            # Por ahora solo simulamos
            results.append({
                'sale_id': sale_id,
                'numero_factura': sale.numero_factura,
                'status': 'success',
                'message': 'Invoice generated successfully'
            })
        except Sale.DoesNotExist:
            results.append({
                'sale_id': sale_id,
                'status': 'error',
                'message': 'Sale not found'
            })
        except Exception as e:
            results.append({
                'sale_id': sale_id,
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'total': len(sale_ids),
        'success': len([r for r in results if r['status'] == 'success']),
        'errors': len([r for r in results if r['status'] == 'error']),
        'results': results,
        'generated_at': str(timezone.now())
    }


@shared_task(name='process_end_of_day')
def process_end_of_day(date_str=None):
    """
    Procesa cierre del día (tarea nocturna)
    
    Usage con Celery Beat:
        CELERY_BEAT_SCHEDULE = {
            'end-of-day-process': {
                'task': 'process_end_of_day',
                'schedule': crontab(hour=23, minute=0),  # 11pm diario
            },
        }
    
    Args:
        date_str: Fecha en formato 'YYYY-MM-DD' (default: hoy)
    
    Returns:
        dict: Resumen del cierre
    """
    from app.models.sale import Sale
    from datetime import datetime
    
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%M-%d').date()
    else:
        target_date = timezone.now().date()
    
    # Obtener todas las ventas del día
    daily_sales = Sale.objects.filter(fecha__date=target_date)
    
    # Calcular totales
    total_count = daily_sales.count()
    total_amount = sum(sale.total for sale in daily_sales)
    
    # Aquí podrían ir más procesos:
    # - Backup de ventas
    # - Notificaciones
    # - Generación de reportes
    # - Actualización de estadísticas
    
    return {
        'date': str(target_date),
        'sales_count': total_count,
        'total_amount': float(total_amount),
        'status': 'completed',
        'processed_at': str(timezone.now())
    }


@shared_task(name='send_bulk_emails')
def send_bulk_emails(recipient_ids, subject, message):
    """
    Envío de emails en batch
    
    Usage:
        task = send_bulk_emails.delay([1, 2, 3], 'Promoción', 'Mensaje...')
    
    Args:
        recipient_ids: Lista de IDs de clientes
        subject: Asunto del email
        message: Cuerpo del mensaje
    
    Returns:
        dict: Resultado del envío
    """
    from app.models.client import Client
    
    results = []
    
    for client_id in recipient_ids:
        try:
            client = Client.objects.get(id=client_id)
            
            if client.email:
                # Aquí iría la lógica real de envío de email
                # Por ahora solo simulamos
                results.append({
                    'client_id': client_id,
                    'email': client.email,
                    'status': 'sent'
                })
            else:
                results.append({
                    'client_id': client_id,
                    'status': 'skipped',
                    'reason': 'No email address'
                })
        except Client.DoesNotExist:
            results.append({
                'client_id': client_id,
                'status': 'error',
                'reason': 'Client not found'
            })
    
    return {
        'total': len(recipient_ids),
        'sent': len([r for r in results if r['status'] == 'sent']),
        'skipped': len([r for r in results if r['status'] == 'skipped']),
        'errors': len([r for r in results if r['status'] == 'error']),
        'results': results,
        'sent_at': str(timezone.now())
    }

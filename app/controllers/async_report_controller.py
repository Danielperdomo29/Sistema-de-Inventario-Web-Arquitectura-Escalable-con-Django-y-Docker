"""
Controller para gestión de reportes asíncronos
"""
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie
from celery.result import AsyncResult

from app.models.user import User
from app.tasks.report_tasks import generate_monthly_report, check_low_stock, generate_daily_summary
from app.tasks.invoice_tasks import batch_generate_invoices


class AsyncReportController:
    """Controlador para tareas asíncronas de reportes"""
    
    @staticmethod
    @ensure_csrf_cookie
    def generate_monthly_report_async(request):
        """
        Genera reporte mensual en background
        
        POST /tasks/report/monthly/
        Body: {year: 2024, month: 1}
        """
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        year = int(request.POST.get('year', 2024))
        month = int(request.POST.get('month', 1))
        
        # Disparar tarea en background
        task = generate_monthly_report.delay(year, month)
        
        # Guardar task_id en sesión para tracking
        recent_tasks = request.session.get('recent_tasks', [])
        recent_tasks.append(task.id)
        request.session['recent_tasks'] = recent_tasks[-20:]  # Mantener últimas 20
        
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing',
            'check_url': f'/tasks/status/{task.id}/',
            'message': f'Generando reporte para {month}/{year}...'
        })
    
    @staticmethod
    def check_task_status(request, task_id):
        """
        Verifica el status de cualquier tarea asíncrona
        
        GET /tasks/status/<task_id>/
        """
        task = AsyncResult(task_id)
        
        response = {
            'task_id': task_id,
            'status': task.state,  # PENDING, STARTED, SUCCESS, FAILURE
            'ready': task.ready()
        }
        
        if task.ready():
            if task.successful():
                response['result'] = task.result
                response['message'] = 'Tarea completada exitosamente'
            else:
                response['error'] = str(task.info)
                response['message'] = 'Tarea fallida'
        else:
            response['message'] = 'Tarea en proceso...'
        
        return JsonResponse(response)
    
    @staticmethod
    @ensure_csrf_cookie
    def check_low_stock_async(request):
        """
        Verifica stock bajo de forma asíncrona
        
        POST /tasks/stock/check/
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        task = check_low_stock.delay()
        
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing',
            'check_url': f'/tasks/status/{task.id}/',
            'message': 'Verificando productos con stock bajo...'
        })
    
    @staticmethod
    @ensure_csrf_cookie
    def generate_daily_summary_async(request):
        """
        Genera resumen diario
        
        POST /tasks/report/daily/
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        date_str = request.POST.get('date', None)  # Format: YYYY-MM-DD
        
        task = generate_daily_summary.delay(date_str)
        
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing',
            'check_url': f'/tasks/status/{task.id}/',
            'message': 'Generando resumen diario...'
        })
    
    @staticmethod
    @ensure_csrf_cookie
    def batch_invoices_async(request):
        """
        Genera facturas en batch
        
        POST /tasks/invoices/batch/
        Body: {sale_ids: [1,2,3,4,5]}
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        sale_ids_str = request.POST.get('sale_ids', '')
        sale_ids = [int(x.strip()) for x in sale_ids_str.split(',') if x.strip()]
        
        if not sale_ids:
            return JsonResponse({'error': 'No sale IDs provided'}, status=400)
        
        task = batch_generate_invoices.delay(sale_ids)
        
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing',
            'check_url': f'/tasks/status/{task.id}/',
            'message': f'Generando {len(sale_ids)} facturas en batch...'
        })

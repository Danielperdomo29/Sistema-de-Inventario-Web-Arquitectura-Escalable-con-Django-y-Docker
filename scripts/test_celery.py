"""
Script de testing comprehensivo para Celery
Ejecuta tareas pesadas y valida rendimiento
"""
import os
import sys
import time
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.tasks.report_tasks import generate_monthly_report, check_low_stock, generate_daily_summary
from app.tasks.invoice_tasks import batch_generate_invoices, process_end_of_day
from celery.result import AsyncResult


def test_celery_tasks():
    """Ejecuta todas las tareas de Celery y valida resultados"""
    print("=" * 70)
    print("CELERY HEAVY TESTING - FASE 3")
    print("=" * 70)
    print("\nNOTA: Asegurate de tener un worker corriendo:")
    print("  python -m celery -A config worker -l INFO\n")
    
    results = {}
    
    # Test 1: Reporte Mensual (tarea pesada - 2s delay)
    print("\n" + "-" * 70)
    print("[Test 1] Generando reporte mensual (async, ~2s)...")
    start = time.time()
    task1 = generate_monthly_report.delay(2024, 1)
    print(f"  Task ID: {task1.id}")
    print(f"  Status inicial: {task1.state}")
    
    # Esperar resultado
    try:
        result1 = task1.get(timeout=10)
        elapsed = time.time() - start
        print(f"  OK - Completado en {elapsed:.2f}s")
        print(f"  Resultado: {result1['count']} ventas, Total: ${result1['total_sales']:.2f}")
        results['monthly_report'] = {'status': 'success', 'time': elapsed}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['monthly_report'] = {'status': 'error', 'error': str(e)}
    
    # Test 2: Check Low Stock
    print("\n" + "-" * 70)
    print("[Test 2] Verificando stock bajo...")
    start = time.time()
    task2 = check_low_stock.delay()
    print(f"  Task ID: {task2.id}")
    
    try:
        result2 = task2.get(timeout=10)
        elapsed = time.time() - start
        print(f"  OK - Completado en {elapsed:.2f}s")
        print(f"  Productos con stock bajo: {result2['products_count']}")
        if result2['products_count'] > 0:
            print(f"  Primeros 3: {result2['products'][:3]}")
        results['low_stock'] = {'status': 'success', 'time': elapsed}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['low_stock'] = {'status': 'error', 'error': str(e)}
    
    # Test 3: Daily Summary
    print("\n" + "-" * 70)
    print("[Test 3] Resumen diario...")
    start = time.time()
    task3 = generate_daily_summary.delay()
    print(f"  Task ID: {task3.id}")
    
    try:
        result3 = task3.get(timeout=10)
        elapsed = time.time() - start
        print(f"  OK - Completado en {elapsed:.2f}s")
        print(f"  Ventas del dia: {result3['sales_count']}, Total: ${result3['total_sales']:.2f}")
        results['daily_summary'] = {'status': 'success', 'time': elapsed}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['daily_summary'] = {'status': 'error', 'error': str(e)}
    
    # Test 4: Batch Invoices (tarea heavy)
    print("\n" + "-" * 70)
    print("[Test 4] Generacion batch de facturas (10 facturas)...")
    start = time.time()
    sale_ids = list(range(1, 11))  # IDs 1-10
    task4 = batch_generate_invoices.delay(sale_ids)
    print(f"  Task ID: {task4.id}")
    
    try:
        result4 = task4.get(timeout=15)
        elapsed = time.time() - start
        print(f"  OK - Completado en {elapsed:.2f}s")
        print(f"  Total: {result4['total']}, Exitosos: {result4['success']}, Errores: {result4['errors']}")
        results['batch_invoices'] = {'status': 'success', 'time': elapsed}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['batch_invoices'] = {'status': 'error', 'error': str(e)}
    
    # Test 5: End of Day
    print("\n" + "-" * 70)
    print("[Test 5] Proceso de cierre del dia...")
    start = time.time()
    task5 = process_end_of_day.delay()
    print(f"  Task ID: {task5.id}")
    
    try:
        result5 = task5.get(timeout=10)
        elapsed = time.time() - start
        print(f"  OK - Completado en {elapsed:.2f}s")
        print(f"  Ventas procesadas: {result5['sales_count']}, Monto: ${result5['total_amount']:.2f}")
        results['end_of_day'] = {'status': 'success', 'time': elapsed}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['end_of_day'] = {'status': 'error', 'error': str(e)}
    
    # Test 6: Multiples tareas simultaneas (stress test)
    print("\n" + "-" * 70)
    print("[Test 6] STRESS TEST - 5 tareas simultaneas...")
    start = time.time()
    
    tasks = []
    tasks.append(('Report 2024-01', generate_monthly_report.delay(2024, 1)))
    tasks.append(('Report 2024-02', generate_monthly_report.delay(2024, 2)))
    tasks.append(('Report 2024-03', generate_monthly_report.delay(2024, 3)))
    tasks.append(('Stock Check', check_low_stock.delay()))
    tasks.append(('Daily Summary', generate_daily_summary.delay()))
    
    print(f"  Lanzadas {len(tasks)} tareas...")
    
    completed = 0
    failed = 0
    
    for name, task in tasks:
        try:
            task.get(timeout=15)
            completed += 1
            print(f"    OK - {name}")
        except Exception as e:
            failed += 1
            print(f"    ERROR - {name}: {e}")
    
    elapsed = time.time() - start
    print(f"\n  Resultado: {completed}/{len(tasks)} exitosas en {elapsed:.2f}s")
    results['stress_test'] = {
        'status': 'success' if failed == 0 else 'partial',
        'time': elapsed,
        'completed': completed,
        'failed': failed
    }
    
    # Resumen Final
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    
    success_count = len([r for r in results.values() if r['status'] == 'success'])
    total_count = len(results)
    
    for test_name, result in results.items():
        status_emoji = "OK" if result['status'] == 'success' else "ERROR"
        time_str = f"{result.get('time', 0):.2f}s" if 'time' in result else "N/A"
        print(f"{status_emoji} - {test_name}: {time_str}")
    
    print(f"\nTotal: {success_count}/{total_count} tests exitosos")
    
    if success_count == total_count:
        print("\n" + "=" * 70)
        print("CELERY FUNCIONANDO PERFECTAMENTE")
        print("=" * 70)
        return True
    else:
        print("\nALGUNOS TESTS FALLARON - Verificar worker de Celery")
        return False


if __name__ == "__main__":
    print("\nVerificando que Redis este activo...")
    try:
        from django.core.cache import cache
        cache.set('celery_test', 'ok', 10)
        if cache.get('celery_test') == 'ok':
            print("OK - Redis conectado\n")
        else:
            print("ERROR - Redis no responde correctamente\n")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR - No se puede conectar a Redis: {e}\n")
        sys.exit(1)
    
    success = test_celery_tasks()
    sys.exit(0 if success else 1)

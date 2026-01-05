"""
Script de prueba de carga simple para validar performance con Redis
Ejecutar: python scripts/load_test.py
"""
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración
BASE_URL = "http://127.0.0.1:8000"
NUM_REQUESTS = 100
NUM_WORKERS = 10

def login():
    """Obtiene una sesión autenticada"""
    session = requests.Session()
    # Primero obtén el CSRF token
    login_page = session.get(f"{BASE_URL}/login/")
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    # Login
    if csrf_token:
        session.post(f"{BASE_URL}/login/", {
            "username": "admin",
            "password": "1003811758",
            "csrfmiddlewaretoken": csrf_token
        })
    
    return session

def test_endpoint(endpoint_name, url, session):
    """Prueba un endpoint y mide el tiempo de respuesta"""
    start = time.time()
    try:
        response = session.get(url)
        elapsed = (time.time() - start) * 1000  # en ms
        
        return {
            'endpoint': endpoint_name,
            'status': response.status_code,
            'time_ms': elapsed,
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'endpoint': endpoint_name,
            'status': 0,
            'time_ms': 0,
            'success': False,
            'error': str(e)
        }

def run_load_test():
    """Ejecuta pruebas de carga en múltiples endpoints"""
    print("=" * 70)
    print("PRUEBA DE CARGA - FASE 2 REDIS")
    print("=" * 70)
    print(f"\nConfiguracion:")
    print(f"  - Requests totales: {NUM_REQUESTS}")
    print(f"  - Workers concurrentes: {NUM_WORKERS}")
    print(f"  - Base URL: {BASE_URL}")
    
    # Endpoints a probar
    endpoints = [
        ("Productos (cached)", "/productos/"),
        ("Ventas", "/ventas/"),
        ("Dashboard", "/"),
    ]
    
    results = {}
    
    for endpoint_name, endpoint_url in endpoints:
        print(f"\n{'-' * 70}")
        print(f"Probando: {endpoint_name}")
        print(f"URL: {endpoint_url}")
        
        times = []
        errors = 0
        
        # Crear múltiples sesiones (simular usuarios)
        sessions = [login() for _ in range(NUM_WORKERS)]
        
        # Ejecutar requests concurrentes
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = []
            for i in range(NUM_REQUESTS):
                session = sessions[i % NUM_WORKERS]
                future = executor.submit(test_endpoint, endpoint_name, BASE_URL + endpoint_url, session)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    times.append(result['time_ms'])
                else:
                    errors += 1
        
        total_time = time.time() - start_time
        
        # Calcular estadísticas
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)
            p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max_time
            
            success_rate = (len(times) / NUM_REQUESTS) * 100
            rps = NUM_REQUESTS / total_time
            
            print(f"\n  Resultados:")
            print(f"    - Tiempo promedio: {avg_time:.2f}ms")
            print(f"    - Min/Max: {min_time:.2f}ms / {max_time:.2f}ms")
            print(f"    - Mediana: {median_time:.2f}ms")
            print(f"    - P95: {p95_time:.2f}ms")
            print(f"    - Requests exitosos: {len(times)}/{NUM_REQUESTS} ({success_rate:.1f}%)")
            print(f"    - RPS (requests/seg): {rps:.2f}")
            print(f"    - Tiempo total: {total_time:.2f}s")
            
            results[endpoint_name] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'median': median_time,
                'p95': p95_time,
                'success_rate': success_rate,
                'rps': rps,
                'errors': errors
            }
        else:
            print(f"  ERROR - Todas las requests fallaron")
            results[endpoint_name] = {'errors': NUM_REQUESTS}
    
    # Resumen final
    print(f"\n{'=' * 70}")
    print("RESUMEN GENERAL")
    print("=" * 70)
    
    for endpoint, stats in results.items():
        if 'avg' in stats:
            print(f"\n{endpoint}:")
            print(f"  Promedio: {stats['avg']:.2f}ms")
            print(f"  P95: {stats['p95']:.2f}ms")
            print(f"  RPS: {stats['rps']:.2f}")
            print(f"  Success: {stats['success_rate']:.1f}%")
    
    # Validación de objetivos
    print(f"\n{'=' * 70}")
    print("VALIDACION DE OBJETIVOS")
    print("=" * 70)
    
    productos_stats = results.get("Productos (cached)", {})
    if 'avg' in productos_stats:
        if productos_stats['avg'] < 100:
            print("OK - Productos: Tiempo promedio < 100ms (con cache)")
        else:
            print(f"WARN - Productos: {productos_stats['avg']:.2f}ms (esperado <100ms)")
        
        if productos_stats['p95'] < 200:
            print("OK - Productos: P95 < 200ms")
        else:
            print(f"WARN - Productos: P95 {productos_stats['p95']:.2f}ms")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    run_load_test()

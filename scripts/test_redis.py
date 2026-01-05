"""
Script para validar conexión y rendimiento de Redis
Ejecutar: python scripts/test_redis.py
"""
import os
import time
import sys
from dotenv import load_dotenv

load_dotenv()

def test_redis_connection():
    """Prueba conexión básica a Redis"""
    try:
        import redis
    except ImportError:
        print("❌ Error: Instala redis con: pip install redis")
        return False
    
    redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
    print("=" * 70)
    print("VALIDACIÓN DE REDIS - FASE 2")
    print("=" * 70)
    print(f"\n📡 Conectando a: {redis_url}")
    
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test 1: Ping
        print("\n🔍 Test 1: Ping")
        result = r.ping()
        print(f"   ✅ Respuesta: {result}")
        
        # Test 2: Set/Get básico
        print("\n🔍 Test 2: Set/Get Performance")
        start = time.time()
        r.set('test_key', 'test_value', ex=60)
        value = r.get('test_key')
        elapsed = (time.time() - start) * 1000
        
        if value == 'test_value':
            print(f"   ✅ Set/Get exitoso: {elapsed:.2f}ms")
        else:
            print(f"   ❌ Valor incorrecto: {value}")
            return False
        
        # Test 3: Info de memoria
        print("\n🔍 Test 3: Información del Servidor")
        info = r.info('memory')
        print(f"   ✅ Memoria usada: {info['used_memory_human']}")
        print(f"   ✅ Keys totales: {r.dbsize()}")
        
        # Test 4: Performance de múltiples operaciones
        print("\n🔍 Test 4: Performance Batch (100 ops)")
        start = time.time()
        for i in range(100):
            r.set(f'bench_key_{i}', f'value_{i}', ex=60)
        elapsed = (time.time() - start) * 1000
        avg = elapsed / 100
        print(f"   ✅ Total: {elapsed:.2f}ms")
        print(f"   ✅ Promedio por operación: {avg:.2f}ms")
        
        # Cleanup
        for i in range(100):
            r.delete(f'bench_key_{i}')
        r.delete('test_key')
        
        print("\n" + "=" * 70)
        print("✅ REDIS FUNCIONANDO CORRECTAMENTE")
        print("=" * 70)
        print()
        
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ Error de conexión: {e}")
        print()
        print("Soluciones:")
        print("  1. Verifica que Redis esté corriendo:")
        print("     - Docker: docker ps | grep redis")
        print("     - Local: redis-cli ping")
        print("  2. Verifica REDIS_URL en .env")
        print("  3. Verifica firewall/puerto 6379")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)

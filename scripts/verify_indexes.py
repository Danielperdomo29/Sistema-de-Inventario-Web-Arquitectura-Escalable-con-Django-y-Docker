"""
Script para validar que los índices de base de datos se crearon correctamente.
Ejecutar: python scripts/verify_indexes.py
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'pablogarciajcbd'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def check_indexes():
    """Verifica que los índices se crearon correctamente"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("=" * 80)
        print("VERIFICACIÓN DE ÍNDICES - FASE 1 OPTIMIZACIÓN")
        print("=" * 80)
        print()
        
        # Tablas a verificar
        tables = ['productos', 'ventas', 'clientes']
        
        for table in tables:
            print(f"\n📊 Tabla: {table}")
            print("-" * 80)
            
            # Mostrar índices
            cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = cursor.fetchall()
            
            if not indexes:
                print(f"  ⚠️  No se encontraron índices en la tabla {table}")
                continue
            
            # Agrupar índices por nombre
            index_dict = {}
            for idx in indexes:
                key_name = idx[2]  # Key_name está en la posición 2
                column_name = idx[4]  # Column_name está en la posición 4
                
                if key_name not in index_dict:
                    index_dict[key_name] = []
                index_dict[key_name].append(column_name)
            
            # Mostrar índices agrupados
            for idx_name, columns in index_dict.items():
                if idx_name == 'PRIMARY':
                    continue  # Skip primary key
                
                columns_str = ', '.join(columns)
                print(f"  ✅ {idx_name}: ({columns_str})")
        
        print("\n" + "=" * 80)
        print("VERIFICACIÓN DEL USO DE ÍNDICES")
        print("=" * 80)
        print()
        
        # Queries de ejemplo con EXPLAIN
        test_queries = [
            ("Productos activos", "SELECT * FROM productos WHERE activo = 1 LIMIT 10"),
            ("Ventas por fecha", "SELECT * FROM ventas WHERE fecha > '2024-01-01' LIMIT 10"),
            ("Clientes por documento", "SELECT * FROM clientes WHERE documento LIKE 'CC%' LIMIT 10"),
        ]
        
        for desc, query in test_queries:
            print(f"\n🔍 {desc}:")
            print(f"   Query: {query}")
            
            cursor.execute(f"EXPLAIN {query}")
            explain_result = cursor.fetchone()
            
            if explain_result:
                possible_keys = explain_result[5]  # possible_keys
                key_used = explain_result[6]  # key
                rows = explain_result[8]  # rows
                
                if key_used:
                    print(f"   ✅ Índice usado: {key_used}")
                    print(f"   📊 Filas examinadas: {rows}")
                else:
                    print(f"   ⚠️  NO usa índice (posibles: {possible_keys})")
                    print(f"   📊 Filas examinadas: {rows}")
            else:
                print(f"   ❌ No se pudo obtener el plan de ejecución")
        
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print()
        print("✅ Si ves índices como 'idx_prod_activo', 'idx_sale_fecha', etc., están creados.")
        print("✅ Si en EXPLAIN aparece 'key: idx_xxx', MySQL los está usando.")
        print("⚠️  Si 'key: NULL', la query no usa índices y es candidata a optimización.")
        print()
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        print()
        print("Asegúrate de que:")
        print("  1. MySQL está corriendo")
        print("  2. Las credenciales en .env son correctas")
        print("  3. La base de datos existe")
        sys.exit(1)

if __name__ == "__main__":
    check_indexes()

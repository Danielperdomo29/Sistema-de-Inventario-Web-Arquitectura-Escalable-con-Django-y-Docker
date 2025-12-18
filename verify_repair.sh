#!/bin/bash
# Script de verificación y restauración (Compatible con WSL/Linux Local)

echo "============================================"
echo "   REPARACIÓN SISTEMA INVENTARIO DJANGO"
echo "   (Modo Local / WSL)"
echo "============================================"

# 1. Detectar Python
echo "[1/6] Detectando entorno Python..."
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "ERROR: No se encontró 'python3' ni 'python'. Instálalo primero."
        exit 1
    fi
fi
echo "      Usando comando: $PYTHON_CMD"

# 2. Verificar Dependencias
echo "[2/6] Verificando dependencias..."
$PYTHON_CMD -c "import django; import pymysql" 2>/dev/null
if [ $? -ne 0 ]; then
    # Fallback check for original MySQLdb
    $PYTHON_CMD -c "import django; import MySQLdb" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: Faltan dependencias (Django o driver MySQL)."
        echo "      Intenta instalar: pip install django pymysql cryptography"
        echo "      O si tienes un entorno virtual, actívalo con: source venv/bin/activate"
        exit 1
    fi
fi

# 3. Limpiar migraciones antiguas (Opcional, comentado por seguridad)
# echo "Limpiando migraciones antiguas..."
# rm app/migrations/00*.py 2>/dev/null

# 4. Verificar Sistema Django
echo "[3/6] Verificando consistencia de Django..."
$PYTHON_CMD manage.py check
if [ $? -ne 0 ]; then
    echo "ERROR: Falló el chequeo de Django."
    exit 1
fi

# 5. Crear Migraciones
echo "[4/6] Creando migraciones..."
$PYTHON_CMD manage.py makemigrations app

# 6. Aplicar Migraciones
echo "[5/6] Aplicando migraciones (fake-initial)..."
$PYTHON_CMD manage.py migrate --fake-initial

# 7. Verificación Final (Tablas y Login)
echo "[6/6] Verificando base de datos y login..."
$PYTHON_CMD -c "
import os
import django
from django.db import connection
from django.test import Client
from django.contrib.auth import get_user_model

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    # Verificar Tablas
    print('   > Verificando tablas críticas...')
    tables = ['auth_user', 'django_session', 'ventas', 'productos']
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f'SHOW TABLES LIKE \"{table}\"')
            exists = cursor.fetchone()
            status = 'OK' if exists else 'MISSING'
            print(f'     - Tabla {table}: {status}')

    # Test Login
    print('   > Probando Login simulado...')
    User = get_user_model()
    username = 'admin_test'
    password = 'password123'

    if not User.objects.filter(username=username).exists():
        print(f'     - Creando usuario test: {username}')
        User.objects.create_user(username=username, password=password)

    c = Client()
    response = c.post('/login/', {'username': username, 'password': password})

    if response.status_code in [302, 200] and (response.url == '/' if hasattr(response, 'url') else True):
         print('     - LOGIN EXITOSO: Redirección detectada.')
    else:
         print(f'     - LOGIN FALLIDO: Status {response.status_code}')

except Exception as e:
    print(f'   ERROR CRÍTICO: {e}')
"

echo "============================================"
echo "   PROCESO COMPLETADO"
echo "============================================"

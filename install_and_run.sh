#!/bin/bash

# ==========================================
#   SISTEMA DE INVENTARIO - INSTALACIÓN TOTAL
#   (Modo "Principiante" / Fresh Start)
# ==========================================

echo "🚀 INICIANDO INSTALACIÓN DESDE CERO..."
echo "----------------------------------------"

# 1. LIMPIEZA
echo "🧹 [1/5] Limpiando instalación anterior..."
rm -rf venv
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 2. ENTORNO VIRTUAL
echo "📦 [2/5] Creando entorno Python aislado..."
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi
$PYTHON_CMD -m venv venv

# Activación automática PARA ESTE SCRIPT
source venv/bin/activate

# 3. DEPENDENCIAS
echo "⬇️  [3/5] Instalando librerías (Django, MySQL, etc)..."
pip install --upgrade pip > /dev/null
pip install django pymysql cryptography > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se pudieron instalar las librerías."
    exit 1
fi

# 4. BASE DE DATOS
echo "🗄️  [4/5] Configurando Base de Datos..."
python manage.py makemigrations app > /dev/null
python manage.py migrate --fake-initial > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló la configuración de la base de datos."
    exit 1
fi

# Crear superusuario por defecto si no existe (Seguro para dev)
echo "creating default admin (admin/admin) if not exists..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('✅ Usuario admin creado (User: admin / Pass: admin)')
else:
    print('✅ Usuario admin ya existe')
"

# 5. EJECUCIÓN
echo "----------------------------------------"
echo "✅ INSTALACIÓN COMPLETADA CON ÉXITO"
echo "----------------------------------------"
echo "🚀 INICIANDO SERVIDOR..."
echo "🌐 Abre en tu navegador: http://127.0.0.1:8000"
echo "⚠️  Para detener el servidor presiona CTRL + C"
echo "----------------------------------------"

python manage.py runserver 0.0.0.0:8000

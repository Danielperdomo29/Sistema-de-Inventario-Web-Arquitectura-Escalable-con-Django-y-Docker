#!/bin/bash
# Script de configuración automática del entorno local (Limpieza Forzada)

echo "============================================"
echo "   CONFIGURACIÓN ENTORNO LOCAL (WSL)"
echo "============================================"

# 1. Limpieza de entorno previo corrupto
if [ -d "venv" ]; then
    echo "[0/3] Eliminando entorno virtual previo..."
    rm -rf venv
fi

# 2. Crear entorno virtual
echo "[1/3] Creando entorno virtual (venv)..."
# Intentar python3, luego python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual. Asegúrate de tener 'python3-venv' instalado."
    echo "Prueba: sudo apt install python3-venv"
    exit 1
fi

# 3. Activar y actualizar pip
echo "[2/3] Instalando dependencias..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Soporte fallback para Git Bash on Windows
    source venv/Scripts/activate
else
    echo "ERROR: No se encuentra el script de activación del entorno virtual."
    exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Falló la instalación de dependencias."
    echo "Asegúrate de tener las librerías de desarrollo de MySQL instaladas."
    echo "Prueba: sudo apt install default-libmysqlclient-dev build-essential pkg-config"
    exit 1
fi

# 4. Ejecutar verificación
echo "[3/3] Ejecutando verificación..."
bash verify_repair.sh

echo "============================================"
echo "   LISTO! Para trabajar, usa siempre:"
echo "   source venv/bin/activate"
echo "============================================"

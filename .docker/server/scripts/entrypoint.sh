#!/bin/bash

## ---------------------------------------------------------
## Corregir permisos de todos los archivos root en /var/www/html
## ---------------------------------------------------------

echo "Corrigiendo permisos de archivos root..."
# find /var/www/html -user root -exec sudo chown ${MY_USER}:${MY_GROUP} {} \; 2>/dev/null || true
echo "✓ Permisos corregidos (Skipped for performance)"

## ---------------------------------------------------------
## Ejecutar Migraciones
## ---------------------------------------------------------

echo "Running migrations..."
/usr/local/bin/wait-for-mysql.sh python manage.py makemigrations app
/usr/local/bin/wait-for-mysql.sh python manage.py migrate
echo "✓ Migrations applied"

## ---------------------------------------------------------
## Ejecutar comando principal
## ---------------------------------------------------------

exec "$@"

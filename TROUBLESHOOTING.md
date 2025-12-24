# Guía Rápida de Troubleshooting

## Problema Actual

El servidor está fallando al iniciar con un error de importación de módulo.

## Solución Temporal

### Opción 1: Desactivar Allauth Temporalmente

Edita tu `.env`:

```env
USE_NEW_SETTINGS=False
ENABLE_ALLAUTH=False
```

Luego:

```bash
python manage.py runserver
```

Esto hará que el sistema use la configuración antigua y funcione normalmente.

### Opción 2: Verificar Instalación de Dependencias

```bash
pip list | findstr allauth
pip list | findstr crispy
```

Deberías ver:

- django-allauth
- django-crispy-forms
- crispy-bootstrap5

Si falta alguna:

```bash
pip install django-allauth django-crispy-forms crispy-bootstrap5
```

### Opción 3: Reinstalar Dependencias

```bash
pip uninstall django-allauth django-crispy-forms crispy-bootstrap5 -y
pip install django-allauth==0.63.3 django-crispy-forms==2.3 crispy-bootstrap5==2024.2
```

## Diagnóstico

### Ver Error Completo

```bash
python manage.py runserver 2>&1 | more
```

### Verificar Configuración

```bash
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; import django; django.setup(); from django.conf import settings; print('OK')"
```

### Verificar Imports

```bash
python -c "import allauth; print('allauth OK')"
python -c "import crispy_forms; print('crispy_forms OK')"
python -c "import crispy_bootstrap5; print('crispy_bootstrap5 OK')"
```

## Si Nada Funciona

### Usar Sistema Actual (Sin Allauth)

1. Edita `.env`:

   ```env
   USE_NEW_SETTINGS=False
   ENABLE_ALLAUTH=False
   ```

2. Reinicia servidor:

   ```bash
   python manage.py runserver
   ```

3. Tu sistema funcionará con las rutas actuales:
   - `/login/`
   - `/register/`
   - `/logout/`

## Contacto

Si el problema persiste, comparte el error completo para ayudarte mejor.

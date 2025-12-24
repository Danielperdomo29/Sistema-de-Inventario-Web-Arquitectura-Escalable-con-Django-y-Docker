# Troubleshooting: Login funciona pero no puedo acceder al dashboard

## Problema

Después de hacer login con `http://localhost:8000/login/`, no puedo acceder a productos (`/productos/`) ni otras secciones del dashboard. La página se queda en `http://localhost:8000/`.

## Causas Posibles

### 1. Usuario sin `rol_id`

**Síntoma:** Login exitoso pero error 403 o redirección al login al intentar acceder a productos.

**Diagnóstico:**

```bash
python scripts/fix_user_permissions.py
```

**Solución Manual:**

```python
python manage.py shell

from app.models.user_account import UserAccount
user = UserAccount.objects.get(username='tu_usuario')
print(f"rol_id: {user.rol_id}")  # Debe ser 1 o 2

# Si es None, arreglar:
user.rol_id = 2  # 1=Admin, 2=Usuario
user.save()
```

### 2. Middleware causando errores

**Síntoma:** Errores en consola del servidor al navegar.

**Solución:** El `AuthSyncMiddleware` ya está configurado para manejar errores gracefully. Si persiste, temporalmente desactivar:

```python
# config/settings/base.py
MIDDLEWARE = [
    # ...
    # 'app.middleware.auth_sync.AuthSyncMiddleware',  # Comentar temporalmente
    # ...
]
```

### 3. Sesión no persistente

**Síntoma:** Login exitoso pero al navegar a otra página, vuelve a pedir login.

**Diagnóstico:**

```python
python manage.py shell

from django.contrib.sessions.models import Session
from datetime import datetime
sessions = Session.objects.filter(expire_date__gte=datetime.now())
print(f"Sesiones activas: {sessions.count()}")
```

**Solución:**

```python
# Verificar configuración de sesión
# config/settings/base.py
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

### 4. CSRF Token issues

**Síntoma:** Formularios no funcionan, error 403 Forbidden.

**Solución:** Limpiar cookies del navegador y volver a intentar.

### 5. Conflicto localhost vs 127.0.0.1

**Síntoma:** Login en `localhost:8000` funciona, pero en `127.0.0.1:8000` no (o viceversa).

**Solución:** Usar siempre el mismo dominio. Configurar en `.env`:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## Pasos de Diagnóstico

### Paso 1: Verificar usuario

```bash
python scripts/fix_user_permissions.py
```

### Paso 2: Verificar sesión

```bash
python manage.py shell
```

```python
from django.contrib.sessions.models import Session
from datetime import datetime
print(Session.objects.filter(expire_date__gte=datetime.now()).count())
```

### Paso 3: Verificar logs del servidor

Revisar la consola donde corre `python manage.py runserver` para ver errores.

### Paso 4: Probar en navegador incógnito

Elimina problemas de caché/cookies.

### Paso 5: Verificar autenticación

```bash
python manage.py shell
```

```python
from django.contrib.auth import authenticate
user = authenticate(username='tu_usuario', password='tu_password')
print(f"Autenticado: {user is not None}")
if user:
    print(f"rol_id: {user.rol_id}")
    print(f"is_active: {user.is_active}")
```

## Solución Rápida

```bash
# 1. Reparar permisos de usuarios
python scripts/fix_user_permissions.py

# 2. Reiniciar servidor
# Ctrl+C en la terminal del servidor
python manage.py runserver

# 3. Limpiar caché del navegador
# Ctrl+Shift+Delete → Limpiar cookies y caché

# 4. Intentar login nuevamente
```

## Verificación

Después de aplicar la solución:

1. Login: `http://localhost:8000/login/`
2. Verificar dashboard: `http://localhost:8000/`
3. Acceder a productos: `http://localhost:8000/productos/`
4. Acceder a categorías: `http://localhost:8000/categorias/`

Si todo funciona: ✅ Problema resuelto

## Contacto

Si el problema persiste, proporcionar:

- Logs del servidor (consola donde corre runserver)
- Username del usuario con problema
- Navegador utilizado
- Pasos exactos para reproducir

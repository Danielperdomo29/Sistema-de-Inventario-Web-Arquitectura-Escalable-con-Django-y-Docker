# Pruebas de Humo (Smoke Tests) - Django Allauth

## Objetivo

Verificar que el flujo completo de autenticación funciona correctamente desde el registro hasta el acceso al dashboard.

---

## Pre-requisitos

### 1. Activar Django-Allauth

Editar `.env`:

```env
USE_NEW_SETTINGS=True
ENABLE_ALLAUTH=True
ENABLE_EMAIL_VERIFICATION=mandatory
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 2. Crear Site Object

```bash
python manage.py setup_site --domain=localhost:8000 --name="Sistema de Inventario"
```

### 3. Aplicar Migraciones

```bash
python manage.py migrate
```

### 4. Iniciar Servidor

```bash
python manage.py runserver
```

---

## Flujo de Prueba Completo

### Test 1: Registro de Usuario

#### Paso 1.1: Acceder a Registro

```
URL: http://localhost:8000/accounts/signup/
```

**Verificar**:

- ✅ Página carga correctamente
- ✅ Formulario muestra campos: Email, Password1, Password2
- ✅ Diseño Bootstrap 5 se ve correctamente
- ✅ Mensajes de requisitos de contraseña visibles

#### Paso 1.2: Intentar Registro con Contraseña Débil

**Datos de prueba**:

```
Email: test@ejemplo.com
Password1: 123
Password2: 123
```

**Resultado Esperado**:

- ❌ Formulario NO se envía
- ✅ Mensaje de error visible: "Esta contraseña es demasiado corta. Debe contener al menos 8 caracteres."
- ✅ Error se muestra con clase CSS `.invalid-feedback`
- ✅ Campo tiene clase `.is-invalid`

#### Paso 1.3: Registro Exitoso

**Datos de prueba**:

```
Email: test@ejemplo.com
Password1: TestPassword123!
Password2: TestPassword123!
```

**Resultado Esperado**:

- ✅ Formulario se envía
- ✅ Redirección a `/accounts/verify-email/`
- ✅ Mensaje: "Email enviado a test@ejemplo.com"

---

### Test 2: Verificación de Email

#### Paso 2.1: Revisar Consola

**En la terminal donde corre `runserver`**:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: [Sistema de Inventario] Please Confirm Your E-mail Address
From: Sistema de Inventario <noreply@inventario.com>
To: test@ejemplo.com
Date: ...

Hello from Sistema de Inventario!

You're receiving this e-mail because user test@ejemplo.com has given your e-mail address to register an account.

To confirm this is correct, go to http://localhost:8000/accounts/confirm-email/XXXXX-XXXXX/

Thank you for using Sistema de Inventario!
```

**Verificar**:

- ✅ Email se imprime en consola
- ✅ Contiene enlace de confirmación
- ✅ Enlace tiene formato: `/accounts/confirm-email/{key}/`

#### Paso 2.2: Copiar Enlace de Confirmación

**Copiar el enlace** que aparece en el email (ejemplo):

```
http://localhost:8000/accounts/confirm-email/MQ:1tXXXX:XXXXXXXXXXXXXXXXX/
```

#### Paso 2.3: Acceder al Enlace

**Pegar en navegador**

**Resultado Esperado**:

- ✅ Página de confirmación carga
- ✅ Muestra email a confirmar
- ✅ Botón "Confirmar Email" visible

#### Paso 2.4: Confirmar Email

**Hacer clic en "Confirmar Email"**

**Resultado Esperado**:

- ✅ Redirección a `/accounts/login/`
- ✅ Mensaje de éxito: "Email confirmado exitosamente"

---

### Test 3: Inicio de Sesión

#### Paso 3.1: Intentar Login Sin Verificar (Opcional)

**Si el usuario NO ha verificado su email**:

```
Email: test@ejemplo.com
Password: TestPassword123!
```

**Resultado Esperado**:

- ❌ Login bloqueado
- ✅ Mensaje: "Debes verificar tu email antes de iniciar sesión"

#### Paso 3.2: Login Exitoso

**Después de verificar email**:

```
Email: test@ejemplo.com
Password: TestPassword123!
Remember: ✓ (checked)
```

**Resultado Esperado**:

- ✅ Login exitoso
- ✅ Redirección a `/` (dashboard)
- ✅ Usuario autenticado
- ✅ Sesión recordada (cookie persistente)

---

### Test 4: Acceso al Dashboard

#### Paso 4.1: Verificar Autenticación

**URL**: `http://localhost:8000/`

**Verificar**:

- ✅ Dashboard carga correctamente
- ✅ Usuario aparece como autenticado
- ✅ Nombre/email del usuario visible en navbar

---

### Test 5: Reset de Contraseña

#### Paso 5.1: Logout

**Hacer clic en Logout**

**Resultado Esperado**:

- ✅ Sesión cerrada automáticamente (sin página de confirmación)
- ✅ Redirección a `/accounts/login/`

#### Paso 5.2: Solicitar Reset

**URL**: `http://localhost:8000/accounts/password/reset/`

**Datos**:

```
Email: test@ejemplo.com
```

**Resultado Esperado**:

- ✅ Email de reset enviado
- ✅ Mensaje en consola con enlace de reset

#### Paso 5.3: Revisar Email en Consola

**Buscar en terminal**:

```
Subject: [Sistema de Inventario] Password Reset E-mail
...
http://localhost:8000/accounts/password/reset/key/XXXXX-XXXXX/
```

#### Paso 5.4: Resetear Contraseña

**Acceder al enlace y establecer nueva contraseña**:

```
New Password: NewPassword456!
Confirm: NewPassword456!
```

**Resultado Esperado**:

- ✅ Contraseña cambiada
- ✅ Redirección a login
- ✅ Puede iniciar sesión con nueva contraseña

---

## Checklist de Verificación

### Funcionalidad

- [ ] Registro de usuario funciona
- [ ] Email de confirmación se envía
- [ ] Confirmación de email funciona
- [ ] Login con email funciona
- [ ] Logout automático funciona
- [ ] Reset de contraseña funciona
- [ ] Sesión se recuerda (checkbox)
- [ ] Redirección al dashboard funciona

### Validaciones

- [ ] Contraseña débil rechazada
- [ ] Contraseñas no coinciden rechazadas
- [ ] Email duplicado rechazado
- [ ] Email inválido rechazado
- [ ] Login sin verificar bloqueado

### UI/UX

- [ ] Todos los templates usan Bootstrap 5
- [ ] Errores se muestran con `.invalid-feedback`
- [ ] Campos con error tienen `.is-invalid`
- [ ] Mensajes de éxito visibles
- [ ] Diseño consistente en todas las páginas
- [ ] Responsive en móvil

### Seguridad

- [ ] Rate limiting funciona (5 intentos/5min)
- [ ] Tokens expiran correctamente
- [ ] CSRF protection activo
- [ ] Emails únicos enforced
- [ ] Password validators activos

---

## Comandos Útiles para Testing

### Ver Usuarios Creados

```bash
python manage.py shell
```

```python
from app.models.user_account import UserAccount
users = UserAccount.objects.all()
for u in users:
    print(f"{u.email} - Verified: {u.email_verified}")
```

### Verificar Email Manualmente

```python
from app.models.user_account import UserAccount
user = UserAccount.objects.get(email='test@ejemplo.com')
user.mark_email_verified()
print(f"Email verified: {user.email_verified}")
```

### Ver Site Object

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
print(f"Site: {site.name} - {site.domain}")
```

### Limpiar Datos de Prueba

```bash
python manage.py shell
```

```python
from app.models.user_account import UserAccount
UserAccount.objects.filter(email__contains='test').delete()
```

---

## Troubleshooting

### Problema: Email no se envía

**Solución**:

```python
# Verificar configuración en settings
from django.conf import settings
print(settings.EMAIL_BACKEND)
# Debe ser: django.core.mail.backends.console.EmailBackend
```

### Problema: Site object no existe

**Solución**:

```bash
python manage.py setup_site
```

### Problema: Templates no se encuentran

**Verificar**:

```python
from django.conf import settings
print(settings.TEMPLATES[0]['DIRS'])
# Debe incluir: .../templates
```

### Problema: URLs no funcionan

**Verificar**:

```python
from django.conf import settings
print(settings.ENABLE_ALLAUTH)
# Debe ser: True
```

---

## Testing con Mailpit (Opcional)

### Instalación

```bash
# Docker
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit
```

### Configuración

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
```

### Acceso

```
Web UI: http://localhost:8025
```

**Ventajas**:

- Ver emails en interfaz web
- Probar HTML emails
- Simular diferentes clientes de email

---

## Resultado Esperado Final

✅ Usuario puede:

1. Registrarse con email
2. Recibir email de confirmación
3. Confirmar email
4. Iniciar sesión
5. Acceder al dashboard
6. Cerrar sesión automáticamente
7. Resetear contraseña si la olvida

✅ Sistema valida:

- Fortaleza de contraseña
- Unicidad de email
- Verificación obligatoria
- Rate limiting

✅ UI/UX:

- Diseño consistente Bootstrap 5
- Errores claros y visibles
- Mensajes informativos
- Responsive

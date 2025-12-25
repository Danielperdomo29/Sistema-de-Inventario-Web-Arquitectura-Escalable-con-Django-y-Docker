# Guía de Push a Git - v2.0.0

## Estado Actual

- **Rama actual:** main
- **Working tree:** clean (ya hiciste commit)
- **Archivos nuevos creados:** CHANGELOG.md, COMMIT_GUIDE.md

## Estrategia de Ramas Recomendada

### Estructura de Ramas

```
main (producción estable)
  ├── dev (desarrollo activo)
  │   ├── feature/allauth-integration
  │   ├── feature/security-hardening
  │   └── feature/fiscal-module (futuro)
  └── hotfix/* (correcciones urgentes)
```

## Pasos para Subir Cambios

### Opción 1: Push Directo a Main (Si ya está testeado)

```bash
# 1. Agregar archivos de documentación nuevos
git add CHANGELOG.md COMMIT_GUIDE.md

# 2. Commit de documentación
git commit -m "docs: Add CHANGELOG and commit guide for v2.0.0"

# 3. Tag de versión
git tag -a v2.0.0 -m "Release v2.0.0: Django-Allauth + Security Hardening"

# 4. Push a main
git push origin main

# 5. Push tags
git push origin --tags
```

### Opción 2: Crear Rama Dev y Merge (Recomendado)

```bash
# 1. Crear rama dev desde main
git checkout -b dev

# 2. Agregar documentación
git add CHANGELOG.md COMMIT_GUIDE.md
git commit -m "docs: Add comprehensive documentation for v2.0.0"

# 3. Push dev
git push -u origin dev

# 4. Volver a main
git checkout main

# 5. Merge dev a main
git merge dev

# 6. Tag de versión
git tag -a v2.0.0 -m "Release v2.0.0: Django-Allauth + Security Hardening

Features:
- Dual authentication (legacy + allauth)
- OWASP Top 10 security hardening
- Email verification
- Password reset
- Rate limiting

See CHANGELOG.md for full details"

# 7. Push main y tags
git push origin main
git push origin --tags
```

### Opción 3: Si Dev Ya Existe

```bash
# 1. Ver ramas existentes
git branch -a

# 2. Cambiar a dev
git checkout dev

# 3. Merge main a dev (para sincronizar)
git merge main

# 4. Agregar nuevos archivos
git add CHANGELOG.md COMMIT_GUIDE.md
git commit -m "docs: Add v2.0.0 documentation"

# 5. Push dev
git push origin dev

# 6. Crear Pull Request en GitHub/GitLab
# O hacer merge local:
git checkout main
git merge dev
git push origin main
```

## Verificación Pre-Push

```bash
# 1. Verificar archivos sensibles no incluidos
git status
git diff --cached

# 2. Verificar .gitignore
cat .gitignore | grep -E "\.env|\.pfx|\.key"

# 3. Verificar que .env no está trackeado
git ls-files | grep "\.env$"
# (No debe mostrar nada)

# 4. Ver historial de commits
git log --oneline -10

# 5. Ver archivos que se subirán
git diff origin/main..HEAD --name-only
```

## Archivos Críticos a NO Subir

Asegúrate de que estos NO estén en git:

```
❌ .env
❌ .env.local
❌ *.pfx (certificados digitales)
❌ *.p12
❌ *.key
❌ db.sqlite3 (si usas SQLite)
❌ media/ (archivos subidos por usuarios)
❌ staticfiles/ (archivos estáticos compilados)
```

## Archivos que SÍ Deben Subirse

```
✅ CHANGELOG.md
✅ COMMIT_GUIDE.md
✅ SMOKE_TESTS.md
✅ TROUBLESHOOTING_LOGIN.md
✅ .env.example (plantilla)
✅ requirements.txt
✅ config/settings/*.py
✅ app/models/*.py
✅ app/middleware/*.py
✅ app/adapters/*.py
✅ templates/account/*.html
✅ tests/**/*.py
✅ scripts/*.py
```

## Mensaje de Commit Completo (Si no lo hiciste aún)

```bash
git commit -m "feat: Django-Allauth Integration + OWASP Security (v2.0.0)

Major release implementing dual authentication system with comprehensive
security hardening following OWASP Top 10 guidelines.

BREAKING CHANGES:
- Settings structure changed to config/settings/
- UserAccount model extended with allauth fields
- New middleware required: AuthSyncMiddleware

Features:
- ✨ Dual authentication (legacy + django-allauth)
- ✨ Email verification mandatory
- ✨ Password reset with secure tokens
- ✨ Rate limiting for brute force protection
- ✨ OWASP Top 10 compliance (95%)

Security:
- 🔒 HSTS (1 year)
- 🔒 X-Frame-Options: DENY
- 🔒 Content Security Policy
- 🔒 CORS restrictive
- 🔒 Argon2 password hashing
- 🔒 Secure cookies

New Components:
- CustomAccountAdapter
- AuthSyncMiddleware
- Security decorators
- Migration commands
- Comprehensive tests

Documentation:
- CHANGELOG.md
- SMOKE_TESTS.md
- TROUBLESHOOTING_LOGIN.md

Tested: ✅ Both systems work in parallel
Tested: ✅ No breaking changes for existing users

Migration: See CHANGELOG.md for upgrade instructions"
```

## Después del Push

### 1. Verificar en GitHub/GitLab

```bash
# Ver remote
git remote -v

# Ver último push
git log origin/main -1
```

### 2. Crear Release en GitHub (Opcional)

1. Ir a Releases
2. Click "Create a new release"
3. Tag: `v2.0.0`
4. Title: `v2.0.0 - Django-Allauth + Security Hardening`
5. Description: Copiar desde CHANGELOG.md
6. Adjuntar archivos si es necesario

### 3. Proteger Rama Main

En GitHub/GitLab settings:

- Require pull request reviews
- Require status checks to pass
- Include administrators

## Comandos Rápidos

### Push Simple (Main)

```bash
git add .
git commit -m "docs: Add v2.0.0 documentation"
git tag v2.0.0
git push origin main --tags
```

### Push con Dev

```bash
git checkout -b dev
git add .
git commit -m "docs: Add v2.0.0 documentation"
git push -u origin dev
git checkout main
git merge dev
git tag v2.0.0
git push origin main --tags
```

## Rollback (Si algo sale mal)

```bash
# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer último commit (eliminar cambios)
git reset --hard HEAD~1

# Deshacer push (PELIGROSO)
git push origin main --force
```

---

**Recomendación:** Usa la Opción 2 (crear dev y merge) para mantener main estable.

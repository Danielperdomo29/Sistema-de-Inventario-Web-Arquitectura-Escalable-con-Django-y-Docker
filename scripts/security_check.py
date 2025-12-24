"""
Script para verificar configuración de seguridad del sistema.
Ejecutar: python scripts/security_check.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings


def check_security():
    """Verifica configuración de seguridad"""
    print("=" * 70)
    print("VERIFICACIÓN DE SEGURIDAD - OWASP Top 10")
    print("=" * 70)
    print()
    
    issues = []
    warnings = []
    passed = []
    
    # Check 1: DEBUG en producción
    print("[ 1] Verificando DEBUG mode...")
    if settings.DEBUG and os.getenv('DJANGO_ENV') == 'production':
        issues.append("❌ DEBUG=True en producción (CRÍTICO)")
    elif settings.DEBUG:
        warnings.append("⚠️  DEBUG=True (solo aceptable en desarrollo)")
    else:
        passed.append("✅ DEBUG=False")
    
    # Check 2: SECRET_KEY por defecto
    print("[ 2] Verificando SECRET_KEY...")
    if 'mi-clave-secreta' in settings.SECRET_KEY:
        issues.append("❌ SECRET_KEY por defecto detectada (CRÍTICO)")
    else:
        passed.append("✅ SECRET_KEY personalizada")
    
    # Check 3: ALLOWED_HOSTS
    print("[ 3] Verificando ALLOWED_HOSTS...")
    if '*' in settings.ALLOWED_HOSTS and not settings.DEBUG:
        issues.append("❌ ALLOWED_HOSTS='*' en producción (CRÍTICO)")
    elif '*' in settings.ALLOWED_HOSTS:
        warnings.append("⚠️  ALLOWED_HOSTS='*' (solo aceptable en desarrollo)")
    else:
        passed.append("✅ ALLOWED_HOSTS configurado correctamente")
    
    # Check 4: HTTPS
    print("[ 4] Verificando HTTPS...")
    if hasattr(settings, 'SECURE_SSL_REDIRECT'):
        if not settings.SECURE_SSL_REDIRECT and not settings.DEBUG:
            warnings.append("⚠️  HTTPS no forzado en producción")
        else:
            passed.append("✅ SECURE_SSL_REDIRECT configurado")
    
    # Check 5: HSTS
    print("[ 5] Verificando HSTS...")
    if hasattr(settings, 'SECURE_HSTS_SECONDS'):
        if settings.SECURE_HSTS_SECONDS > 0:
            passed.append(f"✅ HSTS configurado ({settings.SECURE_HSTS_SECONDS}s)")
        else:
            warnings.append("⚠️  HSTS no configurado")
    
    # Check 6: Cookies seguras
    print("[ 6] Verificando cookies seguras...")
    if hasattr(settings, 'SESSION_COOKIE_SECURE'):
        if settings.SESSION_COOKIE_SECURE or settings.DEBUG:
            passed.append("✅ SESSION_COOKIE_SECURE configurado")
        else:
            issues.append("❌ SESSION_COOKIE_SECURE=False en producción")
    
    if hasattr(settings, 'SESSION_COOKIE_HTTPONLY'):
        if settings.SESSION_COOKIE_HTTPONLY:
            passed.append("✅ SESSION_COOKIE_HTTPONLY=True")
        else:
            issues.append("❌ SESSION_COOKIE_HTTPONLY=False (vulnerable a XSS)")
    
    # Check 7: CSRF
    print("[ 7] Verificando CSRF protection...")
    if hasattr(settings, 'CSRF_COOKIE_SECURE'):
        if settings.CSRF_COOKIE_SECURE or settings.DEBUG:
            passed.append("✅ CSRF_COOKIE_SECURE configurado")
        else:
            warnings.append("⚠️  CSRF_COOKIE_SECURE=False")
    
    # Check 8: CORS
    print("[ 8] Verificando CORS...")
    if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS'):
        if settings.CORS_ALLOW_ALL_ORIGINS:
            issues.append("❌ CORS permite todos los orígenes (CRÍTICO)")
        else:
            passed.append("✅ CORS configurado restrictivamente")
    
    # Check 9: CSP
    print("[ 9] Verificando Content Security Policy...")
    if hasattr(settings, 'CSP_DEFAULT_SRC'):
        passed.append("✅ CSP configurado")
    else:
        warnings.append("⚠️  CSP no configurado")
    
    # Check 10: Password Hashers
    print("[10] Verificando password hashers...")
    if hasattr(settings, 'PASSWORD_HASHERS'):
        if 'Argon2PasswordHasher' in settings.PASSWORD_HASHERS[0]:
            passed.append("✅ Argon2 como hasher principal")
        else:
            warnings.append("⚠️  Argon2 no es el hasher principal")
    
    # Check 11: X-Frame-Options
    print("[11] Verificando X-Frame-Options...")
    if hasattr(settings, 'X_FRAME_OPTIONS'):
        if settings.X_FRAME_OPTIONS == 'DENY':
            passed.append("✅ X-Frame-Options=DENY (protección clickjacking)")
        else:
            warnings.append(f"⚠️  X-Frame-Options={settings.X_FRAME_OPTIONS}")
    
    # Check 12: Allauth Security
    print("[12] Verificando Allauth security...")
    if hasattr(settings, 'ENABLE_ALLAUTH') and settings.ENABLE_ALLAUTH:
        if hasattr(settings, 'ACCOUNT_EMAIL_VERIFICATION'):
            if settings.ACCOUNT_EMAIL_VERIFICATION == 'mandatory':
                passed.append("✅ Email verification mandatory")
            else:
                warnings.append("⚠️  Email verification no es mandatory")
        
        if hasattr(settings, 'ACCOUNT_RATE_LIMITS'):
            passed.append("✅ Rate limiting configurado")
        else:
            warnings.append("⚠️  Rate limiting no configurado")
    
    # Reporte final
    print()
    print("=" * 70)
    print("RESULTADOS")
    print("=" * 70)
    print()
    
    if passed:
        print("✅ VERIFICACIONES EXITOSAS:")
        for item in passed:
            print(f"   {item}")
        print()
    
    if warnings:
        print("⚠️  ADVERTENCIAS:")
        for item in warnings:
            print(f"   {item}")
        print()
    
    if issues:
        print("❌ PROBLEMAS CRÍTICOS:")
        for item in issues:
            print(f"   {item}")
        print()
    
    # Score
    total_checks = len(passed) + len(warnings) + len(issues)
    score = (len(passed) / total_checks * 100) if total_checks > 0 else 0
    
    print("=" * 70)
    print(f"PUNTUACIÓN DE SEGURIDAD: {score:.1f}%")
    print("=" * 70)
    print()
    
    if score >= 90:
        print("🎉 Excelente configuración de seguridad!")
    elif score >= 70:
        print("👍 Buena configuración, pero hay mejoras posibles")
    elif score >= 50:
        print("⚠️  Configuración aceptable, se recomienda mejorar")
    else:
        print("❌ Configuración insegura, requiere atención inmediata")
    
    print()
    
    return len(issues) == 0


if __name__ == '__main__':
    success = check_security()
    sys.exit(0 if success else 1)

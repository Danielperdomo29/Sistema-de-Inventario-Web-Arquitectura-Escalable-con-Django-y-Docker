"""
Decoradores de seguridad para APIs

Proporciona autenticación mediante:
1. API Token (para integraciones externas)
2. Session/Login (para usuarios del sistema)
3. Permisos granulares
"""

import functools
import hashlib
import hmac
import logging
from datetime import datetime, timedelta  # noqa: F401

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


# Token API configurado en .env
API_TOKEN_HEADER = "X-API-Token"
API_TOKEN_CACHE_PREFIX = "api_token_valid_"
API_RATE_LIMIT_PREFIX = "api_rate_limit_"


def get_api_token():
    """Obtiene el token API configurado"""
    return getattr(settings, "API_SECRET_TOKEN", None)


def validate_api_token(token: str) -> bool:
    """
    Valida un token API

    Soporta:
    - Token estático configurado en settings
    - Tokens generados con HMAC (futuro)
    """
    if not token:
        return False

    # Verificar en cache primero
    cache_key = f"{API_TOKEN_CACHE_PREFIX}{hashlib.sha256(token.encode()).hexdigest()[:16]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Validar contra token configurado
    configured_token = get_api_token()
    if configured_token and hmac.compare_digest(token, configured_token):
        cache.set(cache_key, True, 300)  # Cache 5 minutos
        return True

    cache.set(cache_key, False, 60)  # Cache negativo 1 minuto
    return False


def check_rate_limit(identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """
    Verifica rate limiting

    Returns:
        True si está dentro del límite, False si excedió
    """
    cache_key = f"{API_RATE_LIMIT_PREFIX}{identifier}"

    current = cache.get(cache_key, 0)
    if current >= max_requests:
        return False

    # Incrementar contador
    try:
        cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, window_seconds)

    return True


def api_token_required(view_func=None, allow_session=True, rate_limit=100):
    """
    Decorador que requiere autenticación por API Token o sesión

    Uso:
        @api_token_required
        def my_view(request):
            ...

        @api_token_required(allow_session=False, rate_limit=50)
        def external_api_view(request):
            ...

    Args:
        allow_session: Si True, también acepta usuarios logueados
        rate_limit: Máximo de requests por minuto (0 = sin límite)
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 1. Verificar token API en header
            token = request.headers.get(API_TOKEN_HEADER)

            is_authenticated = False
            auth_method = None

            if token and validate_api_token(token):
                is_authenticated = True
                auth_method = "api_token"

            # 2. Verificar sesión de usuario si está permitido
            if not is_authenticated and allow_session:
                if request.user.is_authenticated:
                    is_authenticated = True
                    auth_method = "session"

            # 3. Rechazar si no está autenticado
            if not is_authenticated:
                logger.warning(f"Acceso no autorizado a {request.path} desde {get_client_ip(request)}")
                return JsonResponse(
                    {
                        "error": "No autorizado",
                        "mensaje": "Se requiere autenticación. Use X-API-Token header o inicie sesión.",
                        "codigo": "UNAUTHORIZED",
                    },
                    status=401,
                )

            # 4. Verificar rate limiting
            if rate_limit > 0:
                identifier = token[:16] if token else str(request.user.id)
                if not check_rate_limit(identifier, rate_limit):
                    logger.warning(f"Rate limit excedido para {identifier}")
                    return JsonResponse(
                        {
                            "error": "Demasiadas solicitudes",
                            "mensaje": f"Límite de {rate_limit} requests por minuto excedido",
                            "codigo": "RATE_LIMITED",
                        },
                        status=429,
                    )

            # 5. Agregar info de autenticación al request
            request.api_auth_method = auth_method

            return view_func(request, *args, **kwargs)

        return wrapper

    # Permitir uso con o sin paréntesis
    if view_func is not None:
        return decorator(view_func)
    return decorator


def internal_only(view_func):
    """
    Decorador para endpoints solo internos (localhost)
    """

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        client_ip = get_client_ip(request)

        allowed_ips = ["127.0.0.1", "::1", "localhost"]

        # En desarrollo, permitir todas las IPs locales
        if settings.DEBUG:
            allowed_ips.extend(["192.168.", "10.", "172.16."])

        is_internal = any(client_ip.startswith(ip) for ip in allowed_ips)

        if not is_internal:
            logger.warning(f"Acceso externo bloqueado a endpoint interno: {request.path} desde {client_ip}")
            return JsonResponse(
                {
                    "error": "Acceso denegado",
                    "mensaje": "Este endpoint solo es accesible desde la red interna",
                    "codigo": "FORBIDDEN",
                },
                status=403,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def get_client_ip(request) -> str:
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")  # nosec B104 - fallback IP, not binding


def permission_required(permission: str):
    """
    Decorador que requiere un permiso específico

    Uso:
        @permission_required('analytics.view_predictions')
        def view_predictions(request):
            ...
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({"error": "No autenticado", "codigo": "UNAUTHENTICATED"}, status=401)

            if not request.user.has_perm(permission):
                logger.warning(f"Permiso denegado: {request.user} intentó acceder sin {permission}")
                return JsonResponse(
                    {
                        "error": "Permiso denegado",
                        "mensaje": f"Se requiere el permiso: {permission}",
                        "codigo": "FORBIDDEN",
                    },
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

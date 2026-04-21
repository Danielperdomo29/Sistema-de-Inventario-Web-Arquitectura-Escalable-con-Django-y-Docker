import hashlib
import logging

from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class DeviceFingerprintMiddleware(MiddlewareMixin):
    """
    Genera un fingerprint pasivo del dispositivo basado en cabeceras HTTP estables.
    Resistente a técnicas de IP Hopping detectando la firma TCP y Browser del atacante.
    """

    FINGERPRINT_HEADERS = [
        "HTTP_USER_AGENT",
        "HTTP_ACCEPT_LANGUAGE",
        "HTTP_ACCEPT_ENCODING",
        "HTTP_X_FORWARDED_FOR",
        "HTTP_SEC_CH_UA",  # Browser modern hints
    ]

    MAX_FAILED_ATTEMPTS = 10  # Intentos fallidos antes de bloquear silenciosamente la IP
    BLOCK_DURATION = 3600  # 1 hora
    WINDOW_SECONDS = 600  # 10 minutos para contar acumulativos

    def process_request(self, request):
        # 1. Generar Fingerprint del Hardware/Navegador del cliente (Invisible)
        fp_string = self._build_fingerprint_string(request)
        device_id = hashlib.sha256(fp_string.encode("utf-8")).hexdigest()
        request.device_id = device_id

        # 2. Verificar existencia en la lista negra (Redis cache)
        block_key = f"device_block:{device_id}"
        if cache.get(block_key):
            logger.critical(
                f"Ataque bloqueado activo. IP Hopping interceptado: {device_id} desde IP {self._get_client_ip(request)}"
            )
            return HttpResponseForbidden("Forbidden System Access.")

        # Obtener historial de mala praxis del atacante
        history_key = f"device_history:{device_id}"
        history = cache.get(history_key) or {"failed_logins": 0, "sql_injections": 0, "ips": []}

        request.device_history = history
        request.device_history_key = history_key

    def _build_fingerprint_string(self, request):
        parts = []
        for header in self.FINGERPRINT_HEADERS:
            value = request.META.get(header, "")
            if header == "HTTP_X_FORWARDED_FOR":
                value = value.split(",")[0].strip() if value else ""
            parts.append(value)
        parts.append(self._get_client_ip(request))
        return "|".join(parts)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    @classmethod
    def record_failed_login(cls, request):
        if not hasattr(request, "device_id"):
            return
        history = request.device_history
        history["failed_logins"] = history.get("failed_logins", 0) + 1
        cls._update_and_check_block(request, history)

    @classmethod
    def record_sql_injection_attempt(cls, request):
        if not hasattr(request, "device_id"):
            return
        history = request.device_history
        history["sql_injections"] = history.get("sql_injections", 0) + 1
        # La inyección SQL vale como falta grave (Pesa por 2 fallos de caja blanca)
        history["sql_injections"] += 1
        cls._update_and_check_block(request, history)

    @classmethod
    def _update_and_check_block(cls, request, history):
        device_id = request.device_id
        history_key = request.device_history_key

        ip = cls._get_client_ip(request)
        if ip not in history["ips"]:
            history["ips"].append(ip)

        cache.set(history_key, history, timeout=cls.WINDOW_SECONDS)

        total_failures = history.get("failed_logins", 0) + history.get("sql_injections", 0)

        if total_failures >= cls.MAX_FAILED_ATTEMPTS:
            block_key = f"device_block:{device_id}"
            cache.set(block_key, True, timeout=cls.BLOCK_DURATION)
            logger.critical(
                f"[IP HOPPING DETECTADO] Device ID: {device_id} ha sido aislado. Rotó {len(history['ips'])} IPs."
            )

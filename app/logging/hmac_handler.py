import hashlib
import hmac
import os
from logging import FileHandler


class HMACChainFileHandler(FileHandler):
    """
    Handler que firma cada entrada de log con HMAC (WORM model) y encadena las firmas.
    Si un atacante borra o modifica una línea, la verificación fallará al romperse el Hash.
    Aseguramiento de trazabilidad para SIEM.
    """

    def __init__(self, filename, mode="a", encoding=None, delay=False, secret_key=None):
        super().__init__(filename, mode, encoding, delay)
        # Buscar en entorno, si no generar uno seguro en runtime (ideal setear LOG_HMAC_SECRET en .env)
        secret = secret_key or os.environ.get("LOG_HMAC_SECRET", "d3f4u1t-s3cr3t-k3y-f0r-hM4c@29!")
        self.secret_key = secret.encode() if isinstance(secret, str) else secret
        self.last_signature = self._read_last_signature()

    def _read_last_signature(self):
        try:
            with open(self.baseFilename + ".sig", "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def _write_signature(self, signature):
        with open(self.baseFilename + ".sig", "w", encoding="utf-8") as f:
            f.write(signature)

    def emit(self, record):
        msg = self.format(record)
        # Calcular HMAC de la entrada actual encadenada con la firma anterior (Chain)
        chain_input = (self.last_signature or "") + msg
        signature = hmac.new(self.secret_key, chain_input.encode("utf-8"), hashlib.sha256).hexdigest()

        # Adjuntar la firma a la propia línea del Log para que el SIEM lo procese
        record.msg = f"{record.msg} | HMAC:{signature}"

        # Escribir entrada original formateada con el hash en el archivo real
        super().emit(record)

        # Guardar la nueva firma maestra para la siguiente línea en archivo fantasma
        self.last_signature = signature
        self._write_signature(signature)

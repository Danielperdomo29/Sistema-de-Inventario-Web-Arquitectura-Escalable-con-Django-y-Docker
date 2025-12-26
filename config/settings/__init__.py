"""
Sistema de configuración modular con feature flags.
Permite activar/desactivar el nuevo sistema sin romper el actual.
"""

import os

# Feature flag principal: Usar nuevo sistema de settings
USE_NEW_SETTINGS = os.getenv("USE_NEW_SETTINGS", "False").lower() == "true"

if USE_NEW_SETTINGS:
    # Usar nueva estructura modular
    env = os.getenv("DJANGO_ENV", "development")

    if env == "production":
        from .production import *
    elif env == "test":
        from .test import *
    else:
        from .development import *
else:
    # Usar settings.py actual (legacy) ubicado en config/settings.py
    import importlib.util
    from pathlib import Path

    # Cargar settings.py del directorio padre (config/settings.py)
    settings_file = Path(__file__).parent.parent / "settings.py"

    if not settings_file.exists():
        raise FileNotFoundError(
            f"No se encontró settings.py en {settings_file}. "
            "Verifica que config/settings.py existe."
        )

    spec = importlib.util.spec_from_file_location("legacy_settings", settings_file)
    settings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings_module)

    # Importar todas las variables del settings.py original
    for key in dir(settings_module):
        if not key.startswith("_"):
            globals()[key] = getattr(settings_module, key)

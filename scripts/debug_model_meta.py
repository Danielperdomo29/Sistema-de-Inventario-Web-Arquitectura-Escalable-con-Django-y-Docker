import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.fiscal.models.fiscal_config import FiscalConfig
from django.apps import apps
from django.conf import settings

print(f"Model: {FiscalConfig}")
print(f"App Label: {FiscalConfig._meta.app_label}")
print(f"DB Table: {FiscalConfig._meta.db_table}")
print(f"Installed Apps (names): {[app.name for app in apps.get_app_configs()]}")
print(f"FiscalConfig App Config Name: {FiscalConfig._meta.app_config.name}")


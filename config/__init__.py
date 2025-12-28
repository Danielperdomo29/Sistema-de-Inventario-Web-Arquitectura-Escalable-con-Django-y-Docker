"""
Configuración de PyMySQL para compatibilidad con Django.
Bypass de version check para evitar errores de compatibilidad.
"""

import pymysql

# Instalar PyMySQL como reemplazo de MySQLdb
pymysql.install_as_MySQLdb()

# Bypass version check - Django 6.0 requiere mysqlclient 2.2.1+
# Configuramos PyMySQL para que se identifique como versión compatible
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

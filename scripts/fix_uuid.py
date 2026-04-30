import os
import sys
import uuid

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.core.management import call_command
from django.db import connection


def fix_public_id():
    print("🛠️ Iniciando reparación de la base de datos para UUIDs...")

    with connection.cursor() as cursor:
        # Verificar si la columna public_id existe
        cursor.execute("SHOW COLUMNS FROM auth_user LIKE 'public_id'")
        column_exists = cursor.fetchone()

        if column_exists:
            print("⚠️ La columna 'public_id' ya existe (probablemente por el fallo anterior).")
            # Si existe pero falló la unicidad, vamos a generar un UUID distinto para cada usuario
            cursor.execute("SELECT id FROM auth_user")
            users = cursor.fetchall()

            for user in users:
                user_id = user[0]
                new_uuid = uuid.uuid4().hex  # Generar UUID único
                cursor.execute("UPDATE auth_user SET public_id = %s WHERE id = %s", [new_uuid, user_id])

            print("✅ Se han asignado UUIDs únicos a todos los usuarios existentes.")

            # Intentar agregar la restricción UNIQUE si no la tiene
            try:
                cursor.execute("ALTER TABLE auth_user ADD UNIQUE (public_id)")
                print("✅ Restricción UNIQUE agregada con éxito.")
            except Exception as e:
                print(f"ℹ️ Nota: {e} (Ya podría tener la restricción)")

        else:
            print("🔧 La columna 'public_id' no existe. Creándola paso a paso...")
            # 1. Agregar columna permitiendo nulos
            cursor.execute("ALTER TABLE auth_user ADD COLUMN public_id char(32) NULL")

            # 2. Rellenar con UUIDs únicos
            cursor.execute("SELECT id FROM auth_user")
            users = cursor.fetchall()
            for user in users:
                user_id = user[0]
                new_uuid = uuid.uuid4().hex
                cursor.execute("UPDATE auth_user SET public_id = %s WHERE id = %s", [new_uuid, user_id])

            # 3. Hacerla NO NULL y ÚNICA
            cursor.execute("ALTER TABLE auth_user MODIFY COLUMN public_id char(32) NOT NULL UNIQUE")
            print("✅ Columna creada y rellenada correctamente.")

    # Finalmente, le decimos a Django que asuma que la migración 0015 ya se ejecutó
    # para que no intente volver a crearla.
    print("🔄 Marcando la migración de Django como completada...")
    call_command("migrate", "app", "0015", "--fake")
    print("🎉 ¡Reparación completada con éxito!")


if __name__ == "__main__":
    fix_public_id()

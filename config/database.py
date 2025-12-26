import os


class Database:
    """
    Gestión de conexiones a la base de datos.
    REFACTOR: Ahora utiliza la conexión centralizada de Django (settings.DATABASES)
    para asegurar compatibilidad entre entornos (local vs docker) y pooling.
    """

    @staticmethod
    def get_connection():
        """Obtiene la conexión raw de Django"""
        from django.db import connection

        return connection

    @staticmethod
    def execute_query(query, params=None, fetch=True):
        """Ejecuta una consulta SQL usando el cursor de Django"""
        from django.db import connection

        # Django's connection.cursor() handles context management and cleanup automatically in request cycle,
        # but for manual execution let's be explicit.
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch:
                # Return dict-like objects involves a bit more work with standard cursor
                # or we can assume tuple if legacy code handles it.
                # However, previous implementation utilized DictCursor.
                # Let's map columns to make it compatible.
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                # For INSERT/UPDATE, usually we want rowcount or lastrowid
                return cursor.lastrowid

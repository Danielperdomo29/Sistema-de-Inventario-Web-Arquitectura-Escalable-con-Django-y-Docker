import os
import django
import sys

# Setup Django
sys.path.append('/var/www/html')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def seed_roles():
    roles = [
        (1, 'Administrador'),
        (2, 'Vendedor'),
        (3, 'Almacenamiento')
    ]
    
    with connection.cursor() as cursor:
        # Check if table 'roles' exists (legacy system)
        cursor.execute("SHOW TABLES LIKE 'roles'")
        if cursor.fetchone():
            print("Seeding legacy 'roles' table...")
            for role_id, role_name in roles:
                cursor.execute(
                    "INSERT INTO roles (id, nombre) VALUES (%s, %s) ON DUPLICATE KEY UPDATE nombre=%s",
                    (role_id, role_name, role_name)
                )
        else:
            print("Table 'roles' not found. Creating it...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INT PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL
                )
            """)
            for role_id, role_name in roles:
                cursor.execute(
                    "INSERT INTO roles (id, nombre) VALUES (%s, %s)",
                    (role_id, role_name)
                )
                
    print("Roles seeded successfully.")

if __name__ == '__main__':
    seed_roles()

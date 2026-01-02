import os
import sys
import django
import pymysql
# Ensure pymysql acts as MySQLdb for Django if needed, 
# but for this script we use pymysql connection directly.
from environ import Env

# Add the project root to the python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Initialize environment variables
env = Env()
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    Env.read_env(env_file)

def reset_database():
    print("🚀 Starting Database Reset Process...")

    # Database Configuration
    db_name = env("DB_NAME", default="pablogarciajcbd")
    db_user = env("DB_USER", default="root")
    db_password = env("DB_PASSWORD", default="password")
    db_host = env("DB_HOST", default="127.0.0.1")
    db_port = int(env("DB_PORT", default=3306))

    print(f"📡 Connecting to MySQL host: {db_host}...")

    try:
        # Connect to MySQL server (not the specific DB yet)
        db = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password, # pymysql uses 'password' not 'passwd' usually, but widely supports both or check docs. 'password' is safe for pymysql.
            port=db_port
        )
        cursor = db.cursor()

        # Drop and Recreate Database
        print(f"🗑️  Dropping database '{db_name}' if exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        
        print(f"✨ Creating database '{db_name}'...")
        cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        db.commit()
        cursor.close()
        db.close()
        print("✅ Database reset successfully.")

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)

    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    # Run Migrations
    print("🔄 Running migrations...")
    try:
        from django.core.management import call_command
        call_command("migrate")
        print("✅ Migrations applied.")
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        sys.exit(1)

    # Seed Data (Optional)
    seed_script = os.path.join(BASE_DIR, "seed_roles.py")
    if os.path.exists(seed_script):
        print("🌱 Seeding initial data (Roles/Users)...")
        try:
            # We run it as a subprocess or import it. Importing is better if it has a main function or similar.
            # Assuming seed_roles.py can be run via shell
            import subprocess
            subprocess.run([sys.executable, seed_script], check=True)
            print("✅ Data seeded.")
        except Exception as e:
            print(f"⚠️ Error seeding data: {e}")
    
    print("🎉 Database reset and setup complete!")

if __name__ == "__main__":
    # Safety Check: Ask for confirmation if not forced
    if "--force" not in sys.argv:
        response = input("⚠️  WARNING: This will DESTROY all data in the database. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("🚫 Operation cancelled.")
            sys.exit(0)
    
    reset_database()

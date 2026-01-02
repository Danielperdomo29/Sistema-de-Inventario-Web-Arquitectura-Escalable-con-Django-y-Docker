import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    username = "admin"
    email = "admin@example.com"
    password = "password"
    
    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser '{username}'...")
        User.objects.create_superuser(username, email, password, rol_id=1)
        print(f"✅ Superuser created. Login with: {username} / {password}")
    else:
        print(f"ℹ️ Superuser '{username}' already exists.")

if __name__ == '__main__':
    create_superuser()

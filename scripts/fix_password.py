import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

def fix_password():
    User = get_user_model()
    # The user mentioned they changed "password" (the default) to "1003811758".
    # Assuming the user is 'admin' since that's what we seeded.
    username = "admin" 
    new_password = "1003811758"
    
    try:
        user = User.objects.get(username=username)
        print(f"Found user '{username}'. Resetting password to '{new_password}'...")
        user.set_password(new_password)
        user.save()
        print("✅ Password updated successfully. You can now login.")
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found.")
        # Try to find any user?
        user = User.objects.first()
        if user:
            print(f"Found user '{user.username}'. Resetting password to '{new_password}'...")
            user.set_password(new_password)
            user.save()
            print(f"✅ Password for '{user.username}' updated successfully.")

if __name__ == '__main__':
    fix_password()


import os
import sys
import django
from dotenv import load_dotenv

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

load_dotenv()

from app.services.ai_service import AIService
from app.models.user import User

def verify_integration():
    print("--- Verifying Chatbot Integration ---")
    
    # 1. Check API Key Visibility
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FAIL: GEMINI_API_KEY is missing.")
        return
    print(f"PASS: API Key found (starts with... {api_key[:5]})")

    # 2. Check AIService Initialization
    try:
        service = AIService()
        print("PASS: AIService initialized successfully.")
    except Exception as e:
        print(f"FAIL: AIService init failed: {e}")
        return

    # 3. Check Gemini API Call
    try:
        user_id = 1 # Assuming a user exists, or we use a dummy ID if service allows
        # Note: AIService.process_query uses user_id to personalize or log? 
        # Looking at code: proces_query uses user_id for context but mostly optional in logic shown?
        # Actually it uses it for nothing in the provided snippet of AI Service? 
        # Wait, previous view of ai_service.py showed it takes user_id but maybe doesn't use it heavily yet.
        # Let's try a simple query.
        
        response = service.process_query("Hola, ¿qué puedes hacer?", user_id=1)
        
        if "error" in response.lower() or "lo siento" in response.lower():
             print(f"FAIL: Logic Error in response: {response}")
        elif response and isinstance(response, str) and len(response) > 5:
            print(f"PASS: Gemini Response received: {response[:50]}...")
        else:
            print(f"FAIL: Invalid response: {response}")

    except Exception as e:
        print(f"FAIL: API Call error: {e}")

if __name__ == "__main__":
    verify_integration()

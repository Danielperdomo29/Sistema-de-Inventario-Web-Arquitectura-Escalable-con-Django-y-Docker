import os
import sys

import django

from dotenv import load_dotenv

# Configurar Django
sys.path.append("/home/daniel_enrique/proyectos/Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from ia.services.intelligent_chatbot import IntelligentChatbot


def test_gemini():
    print("Testing Gemini connectivity...")
    chatbot = IntelligentChatbot()
    try:
        response = chatbot.get_response("Hola, ¿cuántos productos hay en el inventario?", user_id=1)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_gemini()

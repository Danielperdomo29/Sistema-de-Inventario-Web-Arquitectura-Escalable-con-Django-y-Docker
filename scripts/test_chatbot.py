import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.test import RequestFactory

from app.controllers.chatbot_controller import ChatbotController
from app.models.user import User
from app.models.user_account import UserAccount


def test_chatbot():
    print("Testing ChatbotController...")
    user = UserAccount.objects.first()
    if not user:
        print("No users found in database.")
        return

    print(f"Using user: {user.username} (id={user.id})")

    factory = RequestFactory()

    # Test get_history
    request = factory.get("/chatbot/history/")
    request.user = user
    request.session = {}

    try:
        response = ChatbotController.get_history(request)
        print("get_history response:", response.status_code, response.content)
    except Exception as e:
        print("get_history crashed:", e)

    # Test send_message
    import json

    request = factory.post("/chatbot/send/", data=json.dumps({"message": "ayuda"}), content_type="application/json")
    request.user = user
    request.session = {}

    try:
        response = ChatbotController.send_message(request)
        print("send_message response:", response.status_code, response.content)
    except Exception as e:
        print("send_message crashed:", e)


if __name__ == "__main__":
    test_chatbot()

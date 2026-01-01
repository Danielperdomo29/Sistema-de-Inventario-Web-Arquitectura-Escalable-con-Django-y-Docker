from django.db import models
from django.conf import settings


class ChatbotMessage(models.Model):
    """Modelo para mensajes del chatbot (Django ORM)"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbot_messages')
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chatbot_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"ChatbotMessage(user={self.user.username}, date={self.created_at})"

    # Métodos estáticos para compatibilidad con el controlador existente
    # aunque idealmente el controlador debería usar el ORM directamente.
    
    @staticmethod
    def save_message(user_id, message, response):
        """Guarda un mensaje y su respuesta"""
        ChatbotMessage.objects.create(
            user_id=user_id,
            message=message,
            response=response
        )

    @staticmethod
    def get_history(user_id, limit=10):
        """Obtiene el historial de conversación del usuario"""
        # Obtenemos los últimos 'limit' mensajes
        messages = ChatbotMessage.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
        
        # Convertimos a formato diccionario para compatibilidad
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "message": msg.message,
                "response": msg.response,
                "created_at": msg.created_at,
            })
            
        # Retornamos en orden cronológico (antiguo -> nuevo) para el chat
        return list(reversed(history))

    @staticmethod
    def delete_history(user_id):
        """Elimina el historial de un usuario"""
        ChatbotMessage.objects.filter(user_id=user_id).delete()

    @staticmethod
    def get_all_messages(user_id):
        """Obtiene todos los mensajes de un usuario"""
        messages = ChatbotMessage.objects.filter(user_id=user_id).order_by('created_at')
        return [
            {
                "id": msg.id,
                "user_id": msg.user_id,
                "message": msg.message,
                "response": msg.response,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]
